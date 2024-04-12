/* SPDX-License-Identifier: LGPL-3.0-or-later */
/* Copyright (C) 2023 Intel Corporation */

/*!
 * \file
 *
 * This file contains the implementation of a verification callback for TLS libraries. The callback
 * verifies the correctness of a self-signed RA-TLS certificate with an SGX quote embedded in it.
 * The callback accesses a specific attestation provider of the Intel Trust Authority (ITA)
 * for ITA-based attestation as part of the verification process. In particular, the callback sends
 * the Attestation request (JSON string that embeds the SGX quote + Enclave Held Data) to ITA via
 * HTTPS and receives an Attestation response (a JSON Web Token, or JWT, with claims). To ensure
 * authenticity of the Attestation response, the callback also obtains a set of JSON Web Keys, or
 * JWKs, from ITA and verifies the signature of JWT with the corresponding JWK's public key.
 *
 * The HTTPS Attestation request is sent to the URL in the format:
 *     POST {providerUrl}/appraisal/{apiVersion}/attest
 *
 * The HTTPS "Get set of JWKs" request is sent to the URL in the format:
 *     GET {portalUrl}/certs/
 *
 * - {providerUrl} is the attestation provider URL (that releases JWTs), e.g.
 *   `https://api.trustauthority.intel.com`.
 * - {portalUrl} is the ITA portal URL (that returns a set of JWKs, where one of these JWKs contains
 *   a public key that corresponds to the private key with which the JWT was signed), e.g.
 *   `https://portal.trustauthority.intel.com`.
 *
 * This file is part of the RA-TLS verification library which is typically linked into client
 * applications. This library is *not* thread-safe.
 */

#define _GNU_SOURCE
#include <assert.h>
#include <ctype.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include <curl/curl.h>

#include <mbedtls/base64.h>
#include <mbedtls/md.h>
#include <mbedtls/rsa.h>
#include <mbedtls/x509_crt.h>

#include <cJSON.h>

#include "ra_tls.h"
#include "ra_tls_common.h"
#include "sgx_arch.h"
#include "sgx_attest.h"

extern verify_measurements_cb_t g_verify_measurements_cb;

#define ERROR(fmt, ...)                                           \
    do {                                                          \
        fprintf(stderr, "%s: " fmt, __FUNCTION__, ##__VA_ARGS__); \
    } while (0)

#define INFO(fmt, ...)                            \
    do {                                          \
        fprintf(stderr, fmt, ##__VA_ARGS__);      \
    } while (0)

#define JWT_ISSUER_NAME                 "Intel Trust Authority"

#define RA_TLS_ITA_PROVIDER_URL         "RA_TLS_ITA_PROVIDER_URL"
#define RA_TLS_ITA_PROVIDER_API_VERSION "RA_TLS_ITA_PROVIDER_API_VERSION"
#define RA_TLS_ITA_API_KEY              "RA_TLS_ITA_API_KEY"
#define RA_TLS_ITA_POLICY_IDS           "RA_TLS_ITA_POLICY_IDS"
#define RA_TLS_ITA_PORTAL_URL           "RA_TLS_ITA_PORTAL_URL"

#define ITA_URL_MAX_SIZE 256
#define ITA_API_KEY_MAX_SIZE 256

/** ITA "Attest SGX Enclave" API endpoint. */
#define ITA_URL_ATTEST_ENDPOINT "attest"

/** ITA "Get Signing Certificates" API endpoint. */
#define ITA_URL_CERTS_ENDPOINT "certs"

/** Default API version for ITA API endpoints. */
#define DEFAULT_ITA_PROVIDER_API_VERSION "v1"

/* Environment variables exposed by successful RA-TLS verification API */
#define RA_TLS_ITA_JWT "RA_TLS_ITA_JWT"
#define RA_TLS_ITA_SET_OF_JWKS "RA_TLS_ITA_SET_OF_JWKS"

static char* g_ita_base_url    = NULL;
static char* g_ita_api_version = NULL;
static char* g_ita_api_key     = NULL;
static char* g_ita_portal_url  = NULL;

/*! Context used in ita_*() calls */
struct ita_context {
    bool curl_global_init_done;
    CURL* curl;                 /*!< CURL context for this session */
    struct curl_slist* headers; /*!< Request headers sent to ITA attestation provider */
};

/*! ITA response (JWT token for `attest/` API, set of Signing keys for `certs/` API) */
struct ita_response {
    char* data;              /*!< response (JSON string) */
    size_t data_size;        /*!< size of \a data string */
};

/* Parse hex string to buffer; returns 0 on success, otherwise -1 */
static int parse_hex(const char* hex, void* buffer, size_t buffer_size) {
    if (!hex || !buffer || buffer_size == 0 || strlen(hex) != buffer_size * 2)
        return -1;

    for (size_t i = 0; i < buffer_size; i++) {
        if (!isxdigit(hex[i * 2]) || !isxdigit(hex[i * 2 + 1])) {
            return -1;
        }
        sscanf(hex + i * 2, "%02hhx", &((uint8_t*)buffer)[i]);
    }
    return 0;
}

static void replace_char(uint8_t* buf, size_t buf_size, char find, char replace) {
    while (*buf && buf_size > 0) {
        if (*buf == find)
            *buf = replace;
        buf++;
        buf_size--;
    }
}

/* mbedTLS currently doesn't implement base64url but only base64, so we introduce helpers */
static int base64url_encode(uint8_t* dst, size_t dlen, size_t* olen, const uint8_t* src,
                            size_t slen) {
    int ret = mbedtls_base64_encode(dst, dlen, olen, src, slen);
    if (ret < 0 || dlen == 0 || !dst)
        return ret;

    /* dst contains base64-encoded string; replace `+` -> `-`, `/` -> `_`, `=` -> `\0` */
    replace_char(dst, dlen, '+', '-');
    replace_char(dst, dlen, '/', '_');
    replace_char(dst, dlen, '=', '\0');

    size_t len = 0;
    while (dst[len] != '\0')
        len++;
    *olen = len + 1;
    return 0;
}

static int base64url_decode(uint8_t* dst, size_t dlen, size_t* olen, const uint8_t* src,
                            size_t slen) {
    if (!src || slen == 0) {
        /* that's what mbedtls_base64_decode() does in this case */
        *olen = 0;
        return 0;
    }

    size_t copied_slen = slen + (3 - (slen - 1) % 4); /* account for 4-byte padding */
    uint8_t* copied_src = calloc(1, copied_slen + 1);
    memcpy(copied_src, src, slen);

    /* src contains base64url-encoded string; replace `-` -> `+`, `_` -> `/` and pad with `=` */
    replace_char(copied_src, copied_slen, '-', '+');
    replace_char(copied_src, copied_slen, '_', '/');
    memset(copied_src + slen, '=', copied_slen - slen);

    int ret = mbedtls_base64_decode(dst, dlen, olen, copied_src, copied_slen);
    free(copied_src);
    return ret;
}

static int init_from_env(char** ptr, const char* env_name, const char* default_val) {
    if (*ptr) {
        /* already initialized */
        return 0;
    }

    char* env_val = getenv(env_name);
    if (!env_val) {
        if (!default_val)
            return MBEDTLS_ERR_X509_BAD_INPUT_DATA;

        *ptr = strdup(default_val);
        if (!*ptr)
            return MBEDTLS_ERR_X509_ALLOC_FAILED;

        return 0;
    }

    size_t env_val_size = strlen(env_val) + 1;
    *ptr = malloc(env_val_size);
    if (!*ptr)
        return MBEDTLS_ERR_X509_ALLOC_FAILED;

    memcpy(*ptr, env_val, env_val_size);
    return 0;
}

static int verify_quote_body_enclave_attributes(sgx_quote_body_t* quote_body,
                                                bool allow_debug_enclave) {
    if (!allow_debug_enclave && (quote_body->report_body.attributes.flags & SGX_FLAGS_DEBUG)) {
        ERROR("Quote: DEBUG bit in enclave attributes is set\n");
        return -1;
    }
    /* sanity checks: 64-bit enclave, initialized, must not have provision/EINIT token key */
    if (!(quote_body->report_body.attributes.flags & SGX_FLAGS_MODE64BIT) ||
            !(quote_body->report_body.attributes.flags & SGX_FLAGS_INITIALIZED) ||
            (quote_body->report_body.attributes.flags & SGX_FLAGS_PROVISION_KEY) ||
            (quote_body->report_body.attributes.flags & SGX_FLAGS_LICENSE_KEY)) {
        return -1;
    }
    return 0;
}

/*!
 * \brief Parse response headers of the ITA attestation response (currently none).
 *
 * \param[in] buffer   Single HTTP header.
 * \param[in] size     Together with \a count the size of \a buffer.
 * \param[in] count    Size of \a buffer, in \a size units.
 * \param[in] context  User data pointer (of type struct ita_response).
 *
 * \returns Number of bytes parsed in the HTTP response headers.
 *
 * \details See cURL documentation at
 *          https://curl.haxx.se/libcurl/c/CURLOPT_HEADERFUNCTION.html
 */
static size_t header_callback(char* buffer, size_t size, size_t count, void* context) {
    /* unused callback, always return success */
    (void)buffer;
    (void)context;
    return size * count;
}

/*!
 * \brief Add HTTP body chunk to internal buffer (contains JSON string).
 *
 * \param[in] buffer   Chunk containing HTTP body.
 * \param[in] size     Together with \a count a size of \a buffer.
 * \param[in] count    Size of \a buffer, in \a size units.
 * \param[in] context  User data pointer (of type struct ita_response).
 *
 * \returns Number of bytes parsed in the HTTP response body.
 *
 * \details See cURL documentation at
 *          https://curl.haxx.se/libcurl/c/CURLOPT_WRITEFUNCTION.html
 */
static size_t body_callback(char* buffer, size_t size, size_t count, void* context) {
    size_t total_size = size * count;

    struct ita_response* response = context;
    assert(response);

    /* make space for the data, plus terminating \0 */
    response->data = realloc(response->data, response->data_size + total_size + 1);
    if (!response->data) {
        exit(-ENOMEM); // no way to gracefully recover
    }

    /* append the data (buffer) to response->data */
    memcpy(response->data + response->data_size, buffer, total_size);
    response->data_size += total_size;

    /* add terminating `\0`, but don't count it in response->data_size to ease appending a next
     * chunk (if any) */
    response->data[response->data_size] = '\0';

    return total_size;
}

static void response_cleanup(struct ita_response* response) {
    free(response->data);
    free(response);
}

static void ita_cleanup(struct ita_context* context) {
    if (!context)
        return;

    curl_slist_free_all(context->headers);
    curl_easy_cleanup(context->curl);

    /* every curl_global_init() must have a corresponding curl_global_cleanup() */
    if (context->curl_global_init_done)
        curl_global_cleanup();

    free(context);
}

static int ita_init(struct ita_context** out_context) {
    int ret;
    char* api_key_hdr = NULL;

    struct ita_context* context = calloc(1, sizeof(*context));
    if (!context) {
        ret = MBEDTLS_ERR_X509_ALLOC_FAILED;
        goto out;
    }

    /* can be called multiple times */
    CURLcode curl_ret = curl_global_init(CURL_GLOBAL_ALL);
    if (curl_ret != CURLE_OK) {
        ret = MBEDTLS_ERR_X509_FATAL_ERROR;
        goto out;
    }
    context->curl_global_init_done = true;

    context->curl = curl_easy_init();
    if (!context->curl) {
        ret = MBEDTLS_ERR_X509_FATAL_ERROR;
        goto out;
    }

    api_key_hdr = malloc(ITA_API_KEY_MAX_SIZE);
    if (!api_key_hdr) {
        ret = MBEDTLS_ERR_X509_ALLOC_FAILED;
        goto out;
    }

    assert(g_ita_api_key);
    ret = snprintf(api_key_hdr, ITA_API_KEY_MAX_SIZE, "x-api-key: %s", g_ita_api_key);
    if (ret < 0 || (size_t)ret >= ITA_API_KEY_MAX_SIZE) {
        ret = MBEDTLS_ERR_X509_BUFFER_TOO_SMALL;
        goto out;
    }

    curl_ret = curl_easy_setopt(context->curl, CURLOPT_SSLVERSION, CURL_SSLVERSION_MAX_DEFAULT);
    if (curl_ret != CURLE_OK) {
        ret = MBEDTLS_ERR_X509_FATAL_ERROR;
        goto out;
    }

    curl_ret = curl_easy_setopt(context->curl, CURLOPT_SSL_VERIFYPEER, 1L);
    if (curl_ret != CURLE_OK) {
        ret = MBEDTLS_ERR_X509_FATAL_ERROR;
        goto out;
    }

    /* set ITA API key as a header (required by ITA API for client authorization) */
    context->headers = curl_slist_append(context->headers, api_key_hdr);
    if (!context->headers) {
        ret = MBEDTLS_ERR_X509_FATAL_ERROR;
        goto out;
    }

    /* this `Accept:` header is required by ITA API */
    context->headers = curl_slist_append(context->headers, "Accept: application/json");
    if (!context->headers) {
        ret = MBEDTLS_ERR_X509_FATAL_ERROR;
        goto out;
    }

    context->headers = curl_slist_append(context->headers, "Content-Type: application/json");
    if (!context->headers) {
        ret = MBEDTLS_ERR_X509_FATAL_ERROR;
        goto out;
    }

    curl_ret = curl_easy_setopt(context->curl, CURLOPT_HTTPHEADER, context->headers);
    if (curl_ret != CURLE_OK) {
        ret = MBEDTLS_ERR_X509_FATAL_ERROR;
        goto out;
    }

    curl_ret = curl_easy_setopt(context->curl, CURLOPT_HEADERFUNCTION, header_callback);
    if (curl_ret != CURLE_OK) {
        ret = MBEDTLS_ERR_X509_FATAL_ERROR;
        goto out;
    }

    curl_ret = curl_easy_setopt(context->curl, CURLOPT_WRITEFUNCTION, body_callback);
    if (curl_ret != CURLE_OK) {
        ret = MBEDTLS_ERR_X509_FATAL_ERROR;
        goto out;
    }

    *out_context = context;
    ret = 0;
out:
    if (ret < 0) {
        ita_cleanup(context);
    }
    free(api_key_hdr);
    return ret;
}

/*! Send GET request (empty) to ITA portal's `certs/` API endpoint and save the resulting set of
 * JWKs in \a out_set_of_jwks; caller is responsible for its cleanup */
static int ita_get_signing_certs(struct ita_context* context, char** out_set_of_jwks) {
    int ret;

    char* request_url = NULL;
    struct ita_response* response = NULL;

    /* prepare sending "GET certs" to ITA and receiving a response (using Curl) */
    response = calloc(1, sizeof(*response));
    if (!response) {
        ret = MBEDTLS_ERR_X509_ALLOC_FAILED;
        goto out;
    }

    request_url = malloc(ITA_URL_MAX_SIZE);
    if (!request_url) {
        ret = MBEDTLS_ERR_X509_ALLOC_FAILED;
        goto out;
    }

    ret = snprintf(request_url, ITA_URL_MAX_SIZE, "%s/%s", g_ita_portal_url,
                   ITA_URL_CERTS_ENDPOINT);
    if (ret < 0 || (size_t)ret >= ITA_URL_MAX_SIZE) {
        ret = MBEDTLS_ERR_X509_BUFFER_TOO_SMALL;
        goto out;
    }

    CURLcode curl_ret;
    curl_ret = curl_easy_setopt(context->curl, CURLOPT_URL, request_url);
    if (curl_ret != CURLE_OK) {
        ret = MBEDTLS_ERR_X509_FATAL_ERROR;
        goto out;
    }

    curl_ret = curl_easy_setopt(context->curl, CURLOPT_HTTPGET, 1);
    if (curl_ret != CURLE_OK) {
        ret = MBEDTLS_ERR_X509_FATAL_ERROR;
        goto out;
    }

    curl_ret = curl_easy_setopt(context->curl, CURLOPT_HEADERDATA, response);
    if (curl_ret != CURLE_OK) {
        ret = MBEDTLS_ERR_X509_FATAL_ERROR;
        goto out;
    }

    curl_ret = curl_easy_setopt(context->curl, CURLOPT_WRITEDATA, response);
    if (curl_ret != CURLE_OK) {
        ret = MBEDTLS_ERR_X509_FATAL_ERROR;
        goto out;
    }

    /* send the "GET certs" request, callbacks will store results in `response` */
    curl_ret = curl_easy_perform(context->curl);
    if (curl_ret != CURLE_OK) {
        ERROR("Failed to send the ITA \"GET certs\" request to `%s`\n", request_url);
        ret = MBEDTLS_ERR_X509_FATAL_ERROR;
        goto out;
    }

    long response_code;
    curl_ret = curl_easy_getinfo(context->curl, CURLINFO_RESPONSE_CODE, &response_code);
    if (curl_ret != CURLE_OK) {
        ret = MBEDTLS_ERR_X509_FATAL_ERROR;
        goto out;
    }

    if (response_code != 200) {
        ERROR("ITA \"GET certs\" request failed with code %ld and message `%s`\n", response_code,
              response->data);
        ret = MBEDTLS_ERR_X509_FATAL_ERROR;
        goto out;
    }

    if (!response->data) {
        ERROR("ITA \"GET certs\" response doesn't have the set of JSON Web Keys (JWKs)\n");
        ret = MBEDTLS_ERR_X509_FATAL_ERROR;
        goto out;
    }

    char* set_of_jwks = strdup(response->data);
    if (!set_of_jwks) {
        ret = MBEDTLS_ERR_X509_ALLOC_FAILED;
        goto out;
    }

    *out_set_of_jwks = set_of_jwks;
    ret = 0;
out:
    response_cleanup(response);
    free(request_url);
    return ret;
}

/*! Send request (with \a quote embedded in it) to ITA attestation provider's `attest/` API endpoint
 * and save response in \a out_ita_response; caller is responsible for its cleanup */
static int ita_send_request(struct ita_context* context, const void* quote, size_t quote_size,
                            const void* runtime_data, size_t runtime_data_size,
                            struct ita_response** out_ita_response) {
    int ret;

    char* quote_b64        = NULL;
    char* runtime_data_b64 = NULL;
    char* request_json     = NULL;
    char* request_url      = NULL;

    struct ita_response* response = NULL;

    /* get needed base64url buffer size for quote, allocate it and encode the quote */
    size_t quote_b64_size = 0;
    ret = base64url_encode(/*dest=*/NULL, /*dlen=*/0, &quote_b64_size, quote, quote_size);
    if (ret != MBEDTLS_ERR_BASE64_BUFFER_TOO_SMALL) {
        goto out;
    }

    quote_b64 = malloc(quote_b64_size);
    if (!quote_b64) {
        ret = MBEDTLS_ERR_X509_ALLOC_FAILED;
        goto out;
    }

    ret = base64url_encode((uint8_t*)quote_b64, quote_b64_size, &quote_b64_size, quote, quote_size);
    if (ret < 0) {
        goto out;
    }

    /* get needed base64url buffer size for runtime data, allocate it and encode the runtime data */
    size_t runtime_data_b64_size = 0;
    ret = base64url_encode(/*dest=*/NULL, /*dlen=*/0, &runtime_data_b64_size, runtime_data,
                           runtime_data_size);
    if (ret != MBEDTLS_ERR_BASE64_BUFFER_TOO_SMALL) {
        goto out;
    }

    runtime_data_b64 = malloc(runtime_data_b64_size);
    if (!runtime_data_b64) {
        ret = MBEDTLS_ERR_X509_ALLOC_FAILED;
        goto out;
    }

    ret = base64url_encode((uint8_t*)runtime_data_b64, runtime_data_b64_size,
                           &runtime_data_b64_size, runtime_data, runtime_data_size);
    if (ret < 0) {
        goto out;
    }

    /* construct JSON string with the attestation request to ITA; it contains the SGX quote, the
     * "runtime data" (SGX report user data) and policy IDs (if any specified in the envvar) */
    const char* request_json_fmt = NULL;
    size_t request_json_size = quote_b64_size + runtime_data_b64_size;

    char* ita_policy_ids = getenv(RA_TLS_ITA_POLICY_IDS);
    if (ita_policy_ids) {
        if (!strlen(ita_policy_ids) || ita_policy_ids[0] != '"') {
            ERROR("Environment variable RA_TLS_ITA_POLICY_IDS is not a JSON string (does not start "
                  "with a double quote)\n");
            ret = MBEDTLS_ERR_X509_FATAL_ERROR;
            goto out;
        }
        /* RA_TLS_ITA_POLICY_IDS envvar specifies a comma-separated set of policy IDs */
        request_json_fmt = "{\"quote\": \"%s\", \"runtime_data\": \"%s\","
                           " \"policy_ids\": [%s]}";
        request_json_size += strlen(ita_policy_ids) + strlen(request_json_fmt) + 1;
    } else {
        request_json_fmt = "{\"quote\": \"%s\", \"runtime_data\": \"%s\"}";
        request_json_size += strlen(request_json_fmt) + 1;
    }

    request_json = malloc(request_json_size);
    if (!request_json) {
        ret = MBEDTLS_ERR_X509_ALLOC_FAILED;
        goto out;
    }

    ret = snprintf(request_json, request_json_size, request_json_fmt, quote_b64, runtime_data_b64,
                   ita_policy_ids ? ita_policy_ids : /*unused dummy*/"");
    if (ret < 0 || (size_t)ret >= request_json_size) {
        ret = MBEDTLS_ERR_X509_BUFFER_TOO_SMALL;
        goto out;
    }

    /* prepare sending attestation request to ITA and receiving a response (using Curl) */
    response = calloc(1, sizeof(*response));
    if (!response) {
        ret = MBEDTLS_ERR_X509_ALLOC_FAILED;
        goto out;
    }

    request_url = malloc(ITA_URL_MAX_SIZE);
    if (!request_url) {
        ret = MBEDTLS_ERR_X509_ALLOC_FAILED;
        goto out;
    }

    ret = snprintf(request_url, ITA_URL_MAX_SIZE, "%s/appraisal/%s/" ITA_URL_ATTEST_ENDPOINT,
                   g_ita_base_url, g_ita_api_version);
    if (ret < 0 || (size_t)ret >= ITA_URL_MAX_SIZE) {
        ret = MBEDTLS_ERR_X509_BUFFER_TOO_SMALL;
        goto out;
    }

    CURLcode curl_ret;
    curl_ret = curl_easy_setopt(context->curl, CURLOPT_URL, request_url);
    if (curl_ret != CURLE_OK) {
        ret = MBEDTLS_ERR_X509_FATAL_ERROR;
        goto out;
    }

    curl_ret = curl_easy_setopt(context->curl, CURLOPT_POST, 1);
    if (curl_ret != CURLE_OK) {
        ret = MBEDTLS_ERR_X509_FATAL_ERROR;
        goto out;
    }

    curl_ret = curl_easy_setopt(context->curl, CURLOPT_POSTFIELDS, request_json);
    if (curl_ret != CURLE_OK) {
        ret = MBEDTLS_ERR_X509_FATAL_ERROR;
        goto out;
    }

    curl_ret = curl_easy_setopt(context->curl, CURLOPT_HEADERDATA, response);
    if (curl_ret != CURLE_OK) {
        ret = MBEDTLS_ERR_X509_FATAL_ERROR;
        goto out;
    }

    curl_ret = curl_easy_setopt(context->curl, CURLOPT_WRITEDATA, response);
    if (curl_ret != CURLE_OK) {
        ret = MBEDTLS_ERR_X509_FATAL_ERROR;
        goto out;
    }

    /* send the attestation request, callbacks will store results in `response` */
    curl_ret = curl_easy_perform(context->curl);
    if (curl_ret != CURLE_OK) {
        ERROR("Failed to send the ITA Attestation request to `%s`\n", request_url);
        ret = MBEDTLS_ERR_X509_FATAL_ERROR;
        goto out;
    }

    long response_code;
    curl_ret = curl_easy_getinfo(context->curl, CURLINFO_RESPONSE_CODE, &response_code);
    if (curl_ret != CURLE_OK) {
        ret = MBEDTLS_ERR_X509_FATAL_ERROR;
        goto out;
    }

    if (response_code != 200) {
        ERROR("ITA Attestation request failed with code %ld and message `%s`\n", response_code,
              response->data);
        ret = MBEDTLS_ERR_X509_FATAL_ERROR;
        goto out;
    }

    if (!response->data) {
        ERROR("ITA Attestation response doesn't have the JSON Web Token (JWT)\n");
        ret = MBEDTLS_ERR_X509_FATAL_ERROR;
        goto out;
    }

    *out_ita_response = response;
    ret = 0;

out:
    if (ret < 0 && response) {
        response_cleanup(response);
    }
    free(quote_b64);
    free(runtime_data_b64);
    free(request_json);
    free(request_url);
    return ret;
}

/*! Verify the attestation response from ITA (the JWT token) and create a dummy SGX quote populated
 * with the SGX-enclave measurements from this response in \a out_quote_body; caller is responsible
 * for its cleanup */
static int ita_verify_response_output_quote(struct ita_response* response, const char* set_of_jwks,
                                            sgx_quote_body_t** out_quote_body) {
    int ret;

    sgx_quote_body_t* quote_body = NULL;

    char* ita_certs_url = NULL;

    cJSON* json_response      = NULL;
    cJSON* json_token_header  = NULL;
    cJSON* json_token_payload = NULL;
    cJSON* json_jwks          = NULL;

    char* token_b64_header    = NULL;
    char* token_b64_payload   = NULL;
    char* token_b64_signature = NULL;

    char* token_header    = NULL;
    char* token_payload   = NULL;
    char* token_signature = NULL;

    char* token_signing_x509cert_b64 = NULL; /* not allocated, so no need to free it */
    char* token_signing_x509cert     = NULL;

    mbedtls_md_context_t md_context;
    mbedtls_md_init(&md_context);

    mbedtls_x509_crt token_signing_crt;
    mbedtls_x509_crt_init(&token_signing_crt);

    json_response = cJSON_Parse(response->data);
    if (!json_response) {
        ERROR("ITA Attestation response is not proper JSON\n");
        ret = MBEDTLS_ERR_X509_FATAL_ERROR;
        goto out;
    }

    cJSON* token_b64 = cJSON_GetObjectItem(json_response, "token");
    if (!cJSON_IsString(token_b64)) {
        ERROR("ITA Attestation response doesn't contain the `token` string key (JWT)\n");
        ret = MBEDTLS_ERR_X509_CERT_UNKNOWN_FORMAT;
        goto out;
    }

    /* JWT tokens are strings in the format: xxx.yyy.zzz where xxx, yyy, zzz are the header, the
     * payload, and the signature correspondingly (each base64url encoded) */
    char* header_begin_in_token_b64 = token_b64->valuestring;
    char* header_end_in_token_b64   = strchr(header_begin_in_token_b64, '.');
    if (!header_end_in_token_b64) {
        ERROR("ITA JWT is incorrectly formatted (cannot find the header)\n");
        ret = MBEDTLS_ERR_X509_CERT_UNKNOWN_FORMAT;
        goto out;
    }

    token_b64_header = calloc(1, header_end_in_token_b64 - header_begin_in_token_b64 + 1);
    if (!token_b64_header) {
        ret = MBEDTLS_ERR_X509_ALLOC_FAILED;
        goto out;
    }
    memcpy(token_b64_header, header_begin_in_token_b64,
           header_end_in_token_b64 - header_begin_in_token_b64);

    char* payload_begin_in_token_b64 = header_end_in_token_b64 + 1;
    char* payload_end_in_token_b64   = strchr(payload_begin_in_token_b64, '.');
    if (!payload_end_in_token_b64) {
        ERROR("ITA JWT is incorrectly formatted (cannot find the payload)\n");
        ret = MBEDTLS_ERR_X509_CERT_UNKNOWN_FORMAT;
        goto out;
    }

    token_b64_payload = calloc(1, payload_end_in_token_b64 - payload_begin_in_token_b64 + 1);
    if (!token_b64_payload) {
        ret = MBEDTLS_ERR_X509_ALLOC_FAILED;
        goto out;
    }
    memcpy(token_b64_payload, payload_begin_in_token_b64,
           payload_end_in_token_b64 - payload_begin_in_token_b64);

    char* signature_begin_in_token_b64 = payload_end_in_token_b64 + 1;
    token_b64_signature = strdup(signature_begin_in_token_b64);
    if (!token_b64_signature) {
        ret = MBEDTLS_ERR_X509_ALLOC_FAILED;
        goto out;
    }

    size_t token_header_size;
    ret = base64url_decode(/*dest=*/NULL, /*dlen=*/0, &token_header_size,
                           (const uint8_t*)token_b64_header, strlen(token_b64_header));
    if (ret != MBEDTLS_ERR_BASE64_BUFFER_TOO_SMALL) {
        goto out;
    }

    token_header = calloc(1, token_header_size + 1);
    if (!token_header) {
        ret = MBEDTLS_ERR_X509_ALLOC_FAILED;
        goto out;
    }

    ret = base64url_decode((uint8_t*)token_header, token_header_size, &token_header_size,
                           (const uint8_t*)token_b64_header, strlen(token_b64_header));
    if (ret < 0) {
        ERROR("ITA JWT is incorrectly formatted (the header is not Base64Url encoded)\n");
        goto out;
    }

    size_t token_payload_size;
    ret = base64url_decode(/*dest=*/NULL, /*dlen=*/0, &token_payload_size,
                           (const uint8_t*)token_b64_payload, strlen(token_b64_payload));
    if (ret != MBEDTLS_ERR_BASE64_BUFFER_TOO_SMALL) {
        goto out;
    }

    token_payload = calloc(1, token_payload_size + 1);
    if (!token_payload) {
        ret = MBEDTLS_ERR_X509_ALLOC_FAILED;
        goto out;
    }

    ret = base64url_decode((uint8_t*)token_payload, token_payload_size, &token_payload_size,
                           (const uint8_t*)token_b64_payload, strlen(token_b64_payload));
    if (ret < 0) {
        ERROR("ITA JWT is incorrectly formatted (the payload is not Base64Url encoded)\n");
        goto out;
    }

    size_t token_signature_size;
    ret = base64url_decode(/*dest=*/NULL, /*dlen=*/0, &token_signature_size,
                           (const uint8_t*)token_b64_signature, strlen(token_b64_signature));
    if (ret != MBEDTLS_ERR_BASE64_BUFFER_TOO_SMALL) {
        goto out;
    }

    token_signature = calloc(1, token_signature_size + 1);
    if (!token_signature) {
        ret = MBEDTLS_ERR_X509_ALLOC_FAILED;
        goto out;
    }

    ret = base64url_decode((uint8_t*)token_signature, token_signature_size, &token_signature_size,
                           (const uint8_t*)token_b64_signature, strlen(token_b64_signature));
    if (ret < 0) {
        ERROR("ITA JWT is incorrectly formatted (the signature is not Base64Url encoded)\n");
        goto out;
    }

    /* at this point, we parsed JWT into three decoded strings: token_header, token_payload,
     * token_signature; the first two are JSON strings */
    json_token_header = cJSON_Parse(token_header);
    if (!json_token_header) {
        ERROR("ITA JWT is incorrectly formatted (the header is not proper JSON)\n");
        ret = MBEDTLS_ERR_X509_FATAL_ERROR;
        goto out;
    }

    cJSON* token_header_alg = cJSON_GetObjectItem(json_token_header, "alg");
    cJSON* token_header_kid = cJSON_GetObjectItem(json_token_header, "kid");
    cJSON* token_header_typ = cJSON_GetObjectItem(json_token_header, "typ");
    cJSON* token_header_jku = cJSON_GetObjectItem(json_token_header, "jku");

    /* currently ITA supports only JWTs with PS384/RSASSA-PSS signing */
    if (!cJSON_IsString(token_header_alg) || strcmp(token_header_alg->valuestring, "PS384") ||
            !cJSON_IsString(token_header_typ) || strcmp(token_header_typ->valuestring, "JWT") ||
            !cJSON_IsString(token_header_kid)) {
        ERROR("ITA JWT header's `alg`, `typ` and/or `kid` fields contain unrecognized values\n");
        ret = MBEDTLS_ERR_X509_CERT_UNKNOWN_FORMAT;
        goto out;
    }

    /* verify that we got the set of JWKs from the same endpoint as contained in `jku`; note that
     * `jku` field doesn't have the trailing slash */
    ita_certs_url = malloc(ITA_URL_MAX_SIZE);
    if (!ita_certs_url) {
        ret = MBEDTLS_ERR_X509_ALLOC_FAILED;
        goto out;
    }

    ret = snprintf(ita_certs_url, ITA_URL_MAX_SIZE, "%s/%s", g_ita_portal_url,
                   ITA_URL_CERTS_ENDPOINT);
    if (ret < 0 || (size_t)ret >= ITA_URL_MAX_SIZE) {
        ret = MBEDTLS_ERR_X509_BUFFER_TOO_SMALL;
        goto out;
    }

    if (!cJSON_IsString(token_header_jku) || strcmp(token_header_jku->valuestring, ita_certs_url)) {
        ERROR("ITA JWT header's `jku` field contains an unexpected URL (got `%s`, expected `%s`)\n",
              token_header_jku->valuestring, ita_certs_url);
        ret = MBEDTLS_ERR_X509_CERT_UNKNOWN_FORMAT;
        goto out;
    }

    json_token_payload = cJSON_Parse(token_payload);
    if (!json_token_payload) {
        ERROR("ITA JWT is incorrectly formatted (the payload is not proper JSON)\n");
        ret = MBEDTLS_ERR_X509_FATAL_ERROR;
        goto out;
    }

    /* json_token_header["kid"] contains an ID that should be found in `set_of_jwks`, so let's parse
     * the latter, find the corresponding array item and extract the X.509 cert from `x5c` field */
    json_jwks = cJSON_Parse(set_of_jwks);
    if (!json_jwks) {
        ERROR("ITA set of JWKs is incorrectly formatted (the set is not proper JSON)\n");
        ret = MBEDTLS_ERR_X509_FATAL_ERROR;
        goto out;
    }

    cJSON* keys_json_array = cJSON_GetObjectItem(json_jwks, "keys");
    if (!cJSON_IsArray(keys_json_array)) {
        ERROR("ITA set of JWKs doesn't contain the `keys` JSON array\n");
        ret = MBEDTLS_ERR_X509_FATAL_ERROR;
        goto out;
    }

    token_signing_x509cert_b64 = NULL; /* for sanity */
    const cJSON* key_json = NULL;
    cJSON_ArrayForEach(key_json, keys_json_array) {
        /* in practice, the `certs/` API endpoint doesn't have `use` and `alg` fields */
        cJSON* key_kty = cJSON_GetObjectItem(key_json, "kty");
        cJSON* key_kid = cJSON_GetObjectItem(key_json, "kid");
        cJSON* key_x5c = cJSON_GetObjectItem(key_json, "x5c");

        /* currently only support RSA keys */
        if (!cJSON_IsString(key_kty) || strcmp(key_kty->valuestring, "RSA")) {
            ERROR("ITA JWK's `kty` field contains an unexpected value (got `%s`, expected `%s`)\n",
                  key_kty->valuestring, "RSA");
            ret = MBEDTLS_ERR_X509_CERT_UNKNOWN_FORMAT;
            goto out;
        }

        if (!cJSON_IsString(key_kid) || !cJSON_IsArray(key_x5c) || !cJSON_GetArraySize(key_x5c)) {
            ERROR("ITA JWK's `kid` and/or `x5c` fields have incorrect types\n");
            ret = MBEDTLS_ERR_X509_CERT_UNKNOWN_FORMAT;
            goto out;
        }

        /* compare kid from the set of JWKs with the one in JWT */
        if (!strcmp(key_kid->valuestring, token_header_kid->valuestring)) {
            cJSON* key_first_x509cert = cJSON_GetArrayItem(key_x5c, 0);
            if (!cJSON_IsString(key_first_x509cert)) {
                ERROR("ITA JWK's `x5c` is not an array of string-value X.509 certificates\n");
                ret = MBEDTLS_ERR_X509_CERT_UNKNOWN_FORMAT;
                goto out;
            }

            token_signing_x509cert_b64 = key_first_x509cert->valuestring;
            break;
        }
    }

    if (!token_signing_x509cert_b64) {
        ERROR("Failed to find a corresponding JWK for the JWT received from ITA\n");
        ret = MBEDTLS_ERR_X509_FATAL_ERROR;
        goto out;
    }

    /* note that "x5c" field is *not* base64url encoded */
    size_t token_signing_x509cert_size = 0;
    ret = mbedtls_base64_decode(/*dest=*/NULL, /*dlen=*/0, &token_signing_x509cert_size,
                                (const uint8_t*)token_signing_x509cert_b64,
                                strlen(token_signing_x509cert_b64));
    if (ret != MBEDTLS_ERR_BASE64_BUFFER_TOO_SMALL) {
        goto out;
    }

    token_signing_x509cert = malloc(token_signing_x509cert_size);
    if (!token_signing_x509cert) {
        ret = MBEDTLS_ERR_X509_ALLOC_FAILED;
        goto out;
    }

    ret = mbedtls_base64_decode((uint8_t*)token_signing_x509cert, token_signing_x509cert_size,
                                &token_signing_x509cert_size,
                                (const uint8_t*)token_signing_x509cert_b64,
                                strlen(token_signing_x509cert_b64));
    if (ret < 0) {
        ERROR("ITA JWK's certificate is incorrectly formatted (not Base64 encoded)\n");
        goto out;
    }

    ret = mbedtls_x509_crt_parse(&token_signing_crt, (const uint8_t*)token_signing_x509cert,
                                 token_signing_x509cert_size);
    if (ret < 0) {
        ERROR("ITA JWK's certificate is incorrectly formatted (not a proper X.509 cert)\n");
        goto out;
    }

    /* perform signature verification of attestation token using the public key from the self-signed
     * certificate obtained from `certs/` ITA API endpoint */
    uint8_t md_sha384[48];
    mbedtls_md_setup(&md_context, mbedtls_md_info_from_type(MBEDTLS_MD_SHA384), /*hmac=*/0);
    mbedtls_md_starts(&md_context);
    mbedtls_md_update(&md_context, (const uint8_t*)token_b64_header, strlen(token_b64_header));
    mbedtls_md_update(&md_context, (const uint8_t*)".", 1);
    mbedtls_md_update(&md_context, (const uint8_t*)token_b64_payload,
                      strlen(token_b64_payload));
    mbedtls_md_finish(&md_context, md_sha384);

    mbedtls_rsa_context* rsa_ctx = mbedtls_pk_rsa(token_signing_crt.pk);
    ret = mbedtls_rsa_rsassa_pss_verify(rsa_ctx, MBEDTLS_MD_SHA384, 48, md_sha384,
                                        (const uint8_t*)token_signature);
    if (ret < 0) {
        ERROR("Failed signature verification of JWT using the JWK's certificate\n");
        goto out;
    }

    /*
     * FIXME: the token-signing certificate obtained from the `certs/` ITA API endpoint
     * (`token_signing_crt`) is supposed to embed an SGX quote; this SGX quote has the measurements
     * like MRSIGNER that are published by the ITA team, and this SGX quote also has a binding to
     * the public key of `token_signing_crt` via the classic hash-of-public-key:
     *   token_signing_crt.sgx_quote.sgx_report.report_data = hash(token_signing_crt.pk)
     *
     * So ideally our code must extract the SGX quote from this certificate, verify this quote,
     * verify that the quote binds to the cert's public key and verify the SGX measurements (against
     * the ones published by the ITA team).
     *
     * Currently ITA does not have such a feature. Therefore, our code currently doesn't perform the
     * SGX-specific verification of the token-signing certificate. We rely on the fact that
     * obtaining the token-signing certificate happens via a protected HTTPS connection to a
     * well-known ITA portal, so the certificate is considered trusted.
     */

    /*
     * We verified the header & signature of the received JWT, can trust its payload. See claims at
     * https://docs.trustauthority.intel.com/main/articles/concept-attestation-tokens.html#token-body
     */

    /* a. Verify JWT generic claims: iss, ver, exp, nbf; we don't care about iat, jti */
    cJSON* iss = cJSON_GetObjectItem(json_token_payload, "iss");
    cJSON* ver = cJSON_GetObjectItem(json_token_payload, "ver");
    cJSON* expiration_time = cJSON_GetObjectItem(json_token_payload, "exp");
    cJSON* not_before_time = cJSON_GetObjectItem(json_token_payload, "nbf");

    if (!cJSON_IsString(iss) || strcmp(iss->valuestring, "Intel Trust Authority")) {
        ERROR("The JWT wasn't issued by Intel Trust Authority (ITA)");
        ret = MBEDTLS_ERR_X509_CERT_UNKNOWN_FORMAT;
        goto out;
    }

    if (!cJSON_IsString(ver) || strcmp(ver->valuestring, "1.0.0")) {
        ERROR("ITA JWT payload's `ver` field is not `1.0.0`\n");
        ret = MBEDTLS_ERR_X509_CERT_UNKNOWN_FORMAT;
        goto out;
    }

    /* expiration_time (exp) and not_before_time (nbf) are represented as JSON numbers with a
     * NumericDate value -- the number of seconds from 1970-01-01 UTC (Seconds Since the Epoch).
     * Verify against the current time (with slack), otherwise this JWT must not be accepted. */
    if (!cJSON_IsNumber(expiration_time) || !cJSON_IsNumber(not_before_time)) {
        ERROR("ITA JWT payload's `exp` and/or `nbf` fields have incorrect types\n");
        ret = MBEDTLS_ERR_X509_CERT_UNKNOWN_FORMAT;
        goto out;
    }
    time_t curr_time = time(NULL);
    if (curr_time == (time_t)-1) {
        ERROR("Failed to fetch current time (to compare against `exp` and `nbf` of ITA JWT)\n");
        ret = MBEDTLS_ERR_X509_FATAL_ERROR;
        goto out;
    }
    int not_before_time_with_slack = not_before_time->valueint > 60
                                         ? not_before_time->valueint - 60
                                         : not_before_time->valueint;
    if (!((time_t)not_before_time_with_slack <= curr_time
                && curr_time <= (time_t)expiration_time->valueint)) {
        ERROR("ITA JWT is expired (nbf=%d, exp=%d in 'Seconds Since the Epoch' format)\n",
              not_before_time->valueint, expiration_time->valueint);
        ret = MBEDTLS_ERR_X509_FATAL_ERROR;
        goto out;
    }

    /* b. verify Verifier claims: policy_ids_matched, policy_ids_unmatched; we don't care about
     *    verifier_nonce, verifier_instance_ids */
    cJSON* policy_ids_matched = cJSON_GetObjectItem(json_token_payload, "policy_ids_matched");
    cJSON* policy_ids_unmatched = cJSON_GetObjectItem(json_token_payload, "policy_ids_unmatched");

    /*
     * ITA sends both matched and unmatched policy IDs in the Attestation Token. It is supposed to
     * be the responsibility of the Relying Party to decide whether and how to check both of these.
     * However, RA-TLS must have some sane default, so currently we (a) make sure that matched
     * policies are correctly formatted and (b) there are *no* unmatched policies.
     *
     * FIXME: "Signed policies" are currently not verified in our code. From ITA docs: "If elevated
     *         trust is required, the RP should verify the matched policy IDs by requesting a copy
     *         of the signed policy stored in the Intel Trust Authority database. An RP can verify
     *         that both the policy ID and hash have the expected values."
     */
    if (policy_ids_matched) {
        if (policy_ids_matched->type != cJSON_Array) {
            ERROR("ITA JWT: Unexpected type of `policy_ids_matched` field (expected JSON array)\n");
            ret = MBEDTLS_ERR_X509_CERT_UNKNOWN_FORMAT;
            goto out;
        }
    }

    if (policy_ids_unmatched) {
        if (policy_ids_unmatched->type != cJSON_Array) {
            ERROR("ITA JWT: Unexpected type of `policy_ids_unmatched` field (expected JSON "
                  "array)\n");
            ret = MBEDTLS_ERR_X509_CERT_UNKNOWN_FORMAT;
            goto out;
        }
        if (cJSON_GetArraySize(policy_ids_unmatched)) {
            ERROR("ITA JWT: Found unmatched policy IDs; RA-TLS forbids this\n");
            ret = MBEDTLS_ERR_X509_CERT_UNKNOWN_FORMAT;
            goto out;
        }
    }

    /* c. Verify Attester claims: attester_type, attester_tcb_status, attester_advisory_ids; we
     *   don't care about attester_tcb_date, attester_inittime_data, attester_runtime_data,
     *   attester_held_data */
    cJSON* attester_type = cJSON_GetObjectItem(json_token_payload, "attester_type");
    cJSON* attester_tcb_status = cJSON_GetObjectItem(json_token_payload, "attester_tcb_status");
    cJSON* attester_advisory_ids = cJSON_GetObjectItem(json_token_payload, "attester_advisory_ids");

    if (!cJSON_IsString(attester_type) || strcmp(attester_type->valuestring, "SGX")) {
        ERROR("ITA JWT payload's `attester_type` field is not `SGX`\n");
        ret = MBEDTLS_ERR_X509_CERT_UNKNOWN_FORMAT;
        goto out;
    }

    /* verify the TCB status, this logic is similar to the one in `ra_tls_verify_dcap.c` */
    bool allow_outdated_tcb        = getenv_allow_outdated_tcb();
    bool allow_hw_config_needed    = getenv_allow_hw_config_needed();
    bool allow_sw_hardening_needed = getenv_allow_sw_hardening_needed();

    if (!cJSON_IsString(attester_tcb_status)) {
        ERROR("ITA JWT payload's `attester_tcb_status` field is not a string\n");
        ret = MBEDTLS_ERR_X509_CERT_UNKNOWN_FORMAT;
        goto out;
    }

    /* see possible values for `attester_tcb_status` at
     * https://docs.trustauthority.intel.com/main/articles/concept-attestation-tokens.html#tcb-status-values */
    if (!strcmp(attester_tcb_status->valuestring, "UpToDate")) {
        ret = 0;
    } else if (!strcmp(attester_tcb_status->valuestring, "SWHardeningNeeded")) {
        ret = allow_sw_hardening_needed ? 0 : MBEDTLS_ERR_X509_CERT_VERIFY_FAILED;
    } else if (!strcmp(attester_tcb_status->valuestring, "ConfigurationNeeded")) {
        ret = allow_hw_config_needed ? 0 : MBEDTLS_ERR_X509_CERT_VERIFY_FAILED;
    } else if (!strcmp(attester_tcb_status->valuestring, "ConfigurationAndSWHardeningNeeded")) {
        ret = allow_hw_config_needed
                  ? (allow_sw_hardening_needed ? 0 : MBEDTLS_ERR_X509_CERT_VERIFY_FAILED)
                  : MBEDTLS_ERR_X509_CERT_VERIFY_FAILED;
    } else if (!strcmp(attester_tcb_status->valuestring, "OutOfDate")) {
        ret = allow_outdated_tcb ? 0 : MBEDTLS_ERR_X509_CERT_VERIFY_FAILED;
    } else if (!strcmp(attester_tcb_status->valuestring, "OutOfDateConfigurationNeeded")) {
        ret = allow_outdated_tcb
                  ? (allow_hw_config_needed ? 0 : MBEDTLS_ERR_X509_CERT_VERIFY_FAILED)
                  : MBEDTLS_ERR_X509_CERT_VERIFY_FAILED;
    } else {
        ret = MBEDTLS_ERR_X509_CERT_VERIFY_FAILED;
    }

    if (ret < 0) {
        ERROR("ITA JWT: TCB status is not allowed: %s\n", attester_tcb_status->valuestring);
        goto out;
    }
    if (strcmp(attester_tcb_status->valuestring, "UpToDate") != 0) {
        INFO("ITA JWT: Allowing TCB status %s\n", attester_tcb_status->valuestring);
    }

    if (attester_advisory_ids) {
        if (attester_advisory_ids->type != cJSON_Array) {
            ERROR("ITA JWT: Unexpected type of `advisoryIDs` field (expected JSON array)\n");
            ret = MBEDTLS_ERR_X509_CERT_UNKNOWN_FORMAT;
            goto out;
        }
        char* ids_str = cJSON_Print(attester_advisory_ids);
        if (!ids_str) {
            ERROR("ITA JWT: Failed to print `advisoryIDs` field\n");
            ret = MBEDTLS_ERR_X509_CERT_UNKNOWN_FORMAT;
            goto out;
        }
        INFO("         [ advisory IDs: %s ]\n", ids_str);
        free(ids_str);
    }

    /* d. Verify Intel SGX claims; we currently don't use sgx_config_id and sgx_collateral */
    cJSON *sgx_is_debuggable = cJSON_GetObjectItem(json_token_payload, "sgx_is_debuggable");
    cJSON *sgx_mrenclave     = cJSON_GetObjectItem(json_token_payload, "sgx_mrenclave");
    cJSON *sgx_mrsigner      = cJSON_GetObjectItem(json_token_payload, "sgx_mrsigner");
    cJSON *sgx_product_id    = cJSON_GetObjectItem(json_token_payload, "sgx_isvprodid");
    cJSON *sgx_svn           = cJSON_GetObjectItem(json_token_payload, "sgx_isvsvn");
    cJSON *sgx_report_data   = cJSON_GetObjectItem(json_token_payload, "sgx_report_data");

    if (!cJSON_IsBool(sgx_is_debuggable) || !cJSON_IsString(sgx_mrenclave) ||
            !cJSON_IsString(sgx_mrsigner) || !cJSON_IsNumber(sgx_product_id) ||
            !cJSON_IsNumber(sgx_svn) || !cJSON_IsString(sgx_report_data)) {
        ERROR("ITA JWT payload's `sgx_is_debuggable`, `sgx_mrenclave`, "
              "`sgx_mrsigner`, `sgx_isvprodid`, `sgx_isvsvn` and/or "
              "`sgx_report_data` fields have incorrect types\n");
        ret = MBEDTLS_ERR_X509_CERT_UNKNOWN_FORMAT;
        goto out;
    }

    /* construct a dummy SGX quote (body) with contents taken from the JWT payload; this is for
     * convenience because other functions in RA-TLS library operate on an SGX quote */
    quote_body = calloc(1, sizeof(*quote_body));
    if (!quote_body) {
        ret = MBEDTLS_ERR_X509_ALLOC_FAILED;
        goto out;
    }

    quote_body->version = 3; /* DCAP; not strictly needed, just for sanity */

    quote_body->report_body.attributes.flags = SGX_FLAGS_INITIALIZED | SGX_FLAGS_MODE64BIT;
    if (cJSON_IsTrue(sgx_is_debuggable))
        quote_body->report_body.attributes.flags |= SGX_FLAGS_DEBUG;

    ret = parse_hex(sgx_mrenclave->valuestring, &quote_body->report_body.mr_enclave,
                    sizeof(quote_body->report_body.mr_enclave));
    if (ret < 0) {
        ERROR("ITA JWT payload's `sgx_mrenclave` field is not hex encoded\n");
        ret = MBEDTLS_ERR_X509_CERT_UNKNOWN_FORMAT;
        goto out;
    }

    ret = parse_hex(sgx_mrsigner->valuestring, &quote_body->report_body.mr_signer,
                    sizeof(quote_body->report_body.mr_signer));
    if (ret < 0) {
        ERROR("ITA JWT payload's `sgx_mrsigner` field is not hex encoded\n");
        ret = MBEDTLS_ERR_X509_CERT_UNKNOWN_FORMAT;
        goto out;
    }

    static_assert(sizeof(quote_body->report_body.isv_prod_id) == 2); /* uint16_t */
    if (sgx_product_id->valueint == INT_MAX || sgx_product_id->valueint == INT_MIN) {
        ERROR("ITA JWT payload's `sgx_isvprodid` field is not an integer\n");
        ret = MBEDTLS_ERR_X509_CERT_UNKNOWN_FORMAT;
        goto out;
    }
    if (sgx_product_id->valueint < 0 || sgx_product_id->valueint > USHRT_MAX) {
        ERROR("ITA JWT payload's `sgx_isvprodid` field is not uint16_t\n");
        ret = MBEDTLS_ERR_X509_CERT_UNKNOWN_FORMAT;
        goto out;
    }
    quote_body->report_body.isv_prod_id = sgx_product_id->valueint;

    static_assert(sizeof(quote_body->report_body.isv_svn) == 2); /* uint16_t */
    if (sgx_svn->valueint == INT_MAX || sgx_svn->valueint == INT_MIN) {
        ERROR("ITA JWT payload's `sgx_isvsvn` field is not an integer\n");
        ret = MBEDTLS_ERR_X509_CERT_UNKNOWN_FORMAT;
        goto out;
    }
    if (sgx_svn->valueint < 0 || sgx_svn->valueint > USHRT_MAX) {
        ERROR("ITA JWT payload's `sgx_isvsvn` field is not uint16_t\n");
        ret = MBEDTLS_ERR_X509_CERT_UNKNOWN_FORMAT;
        goto out;
    }
    quote_body->report_body.isv_svn = sgx_svn->valueint;

    ret = parse_hex(sgx_report_data->valuestring, &quote_body->report_body.report_data,
                    sizeof(quote_body->report_body.report_data));
    if (ret < 0) {
        ERROR("ITA JWT payload's `sgx_report_data` field is not hex encoded\n");
        ret = MBEDTLS_ERR_X509_CERT_UNKNOWN_FORMAT;
        goto out;
    }

#if 0
    ERROR("--- JWT is ```%s``` ---\n", token_b64->valuestring);
    ERROR("--- set_of_jwks is ```%s``` ---\n", set_of_jwks);
#endif

    /*
     * Expose JWT (as base64-formatted string) and "set of JWKs" (as JSON string) in envvars;
     * at this point we know that JWT and "set of JWKs" are correctly formatted strings.
     *
     * NOTE: manipulations with envvars are not thread-safe.
     */
    if (getenv(RA_TLS_ITA_JWT)) {
        ERROR("ITA JWT cannot be exposed through RA_TLS_ITA_JWT envvar because this envvar is "
              "already used (you must unsetenv before calling RA-TLS verification)\n");
        ret = MBEDTLS_ERR_X509_FATAL_ERROR;
        goto out;
    }
    ret = setenv(RA_TLS_ITA_JWT, token_b64->valuestring, /*overwrite=*/1);
    if (ret < 0) {
        ERROR("ITA JWT cannot be exposed through RA_TLS_ITA_JWT envvar because setenv() failed "
              "with error %d\n", errno);
        ret = MBEDTLS_ERR_X509_FATAL_ERROR;
        goto out;
    }

    if (getenv(RA_TLS_ITA_SET_OF_JWKS)) {
        ERROR("ITA \"Set of JWKs\" cannot be exposed through RA_TLS_ITA_SET_OF_JWKS envvar because "
              "this envvar is already used (you must unsetenv before calling RA-TLS "
              "verification)\n");
        ret = MBEDTLS_ERR_X509_FATAL_ERROR;
        goto out;
    }

    ret = setenv(RA_TLS_ITA_SET_OF_JWKS, set_of_jwks, /*overwrite=*/1);
    if (ret < 0) {
        ERROR("ITA \"Set of JWKs\" cannot be exposed through RA_TLS_ITA_SET_OF_JWKS envvar because "
              "setenv() failed with error %d\n", errno);
        ret = MBEDTLS_ERR_X509_FATAL_ERROR;
        goto out;
    }

    *out_quote_body = quote_body;
    ret = 0;
out:
    if (ret < 0) {
        free(quote_body);
    }

    if (json_response)
        cJSON_Delete(json_response);
    if (json_token_header)
        cJSON_Delete(json_token_header);
    if (json_token_payload)
        cJSON_Delete(json_token_payload);
    if (json_jwks)
        cJSON_Delete(json_jwks);

    free(token_b64_header);
    free(token_b64_payload);
    free(token_b64_signature);

    free(token_header);
    free(token_payload);
    free(token_signature);

    free(ita_certs_url);
    free(token_signing_x509cert);
    mbedtls_x509_crt_free(&token_signing_crt);
    mbedtls_md_free(&md_context);
    return ret;
}

/*! parse the public key \p pk into DER format and copy it into \p out_pk_der */
static int parse_pk(mbedtls_pk_context* pk, uint8_t* out_pk_der, size_t* out_pk_der_size) {
    /* below function writes data at the end of the buffer */
    int pk_der_size_byte = mbedtls_pk_write_pubkey_der(pk, out_pk_der, PUB_KEY_SIZE_MAX);
    if (pk_der_size_byte < 0)
        return pk_der_size_byte;

    /* move the data to the beginning of the buffer, to avoid pointer arithmetic later */
    memmove(out_pk_der, out_pk_der + PUB_KEY_SIZE_MAX - pk_der_size_byte, pk_der_size_byte);
    *out_pk_der_size = pk_der_size_byte;
    return 0;
}

int ra_tls_verify_callback(void* data, mbedtls_x509_crt* crt, int depth, uint32_t* flags) {
    struct ra_tls_verify_callback_results* results = (struct ra_tls_verify_callback_results*)data;

    int ret;

    struct ita_context* context   = NULL;
    struct ita_response* response = NULL;
    char* set_of_jwks             = NULL;

    sgx_quote_body_t* quote_from_ita = NULL;

    if (results) {
        /* TODO: when ITA becomes standard, add RA_TLS_ATTESTATION_SCHEME_ita to core RA-TLS lib */
        results->attestation_scheme = RA_TLS_ATTESTATION_SCHEME_UNKNOWN;
        results->err_loc = AT_INIT;
    }

    if (depth != 0) {
        /* the cert chain in RA-TLS consists of single self-signed cert, so we expect depth 0 */
        return MBEDTLS_ERR_X509_INVALID_FORMAT;
    }

    if (flags) {
        /* mbedTLS sets flags to signal that the cert is not to be trusted (e.g., it is not
         * correctly signed by a trusted CA; since RA-TLS uses self-signed certs, we don't care
         * what mbedTLS thinks and ignore internal cert verification logic of mbedTLS */
        *flags = 0;
    }

    ret = init_from_env(&g_ita_base_url, RA_TLS_ITA_PROVIDER_URL, /*default_val=*/NULL);
    if (ret < 0) {
        ERROR("Failed to read the environment variable RA_TLS_ITA_PROVIDER_URL\n");
        goto out;
    }

    ret = init_from_env(&g_ita_api_version, RA_TLS_ITA_PROVIDER_API_VERSION,
                        DEFAULT_ITA_PROVIDER_API_VERSION);
    if (ret < 0) {
        ERROR("Failed to read the environment variable RA_TLS_ITA_PROVIDER_API_VERSION\n");
        goto out;
    }

    ret = init_from_env(&g_ita_api_key, RA_TLS_ITA_API_KEY, /*default_val=*/NULL);
    if (ret < 0) {
        ERROR("Failed to read the environment variable RA_TLS_ITA_API_KEY\n");
        goto out;
    }

    ret = init_from_env(&g_ita_portal_url, RA_TLS_ITA_PORTAL_URL, /*default_val=*/NULL);
    if (ret < 0) {
        ERROR("Failed to read the environment variable RA_TLS_ITA_PORTAL_URL\n");
        goto out;
    }

    if (results)
        results->err_loc = AT_EXTRACT_QUOTE;

    /* extract SGX quote from "quote" OID extension from crt */
    sgx_quote_t* quote;
    size_t quote_size;
    ret = find_oid_in_cert_extensions(crt->v3_ext.p, crt->v3_ext.len, g_quote_oid, g_quote_oid_size,
                                      (uint8_t**)&quote, &quote_size);
    if (ret < 0)
        goto out;

    if (quote_size < sizeof(*quote)) {
        ret = MBEDTLS_ERR_X509_INVALID_EXTENSIONS;
        goto out;
    }

    /* compare public key's hash from cert against quote's report_data */
    ret = cmp_crt_pk_against_quote_report_data(crt, quote);
    if (ret < 0)
        goto out;

    /* parse the public key of the received certificate into DER format -- it should be put into the
     * Attestation request's `runtimeData` field (ITA will take a SHA256 hash over it and verify
     * against the first 32 bytes of the SGX quote's report_data field) */
    uint8_t pk_der[PUB_KEY_SIZE_MAX] = {0};
    size_t pk_der_size;
    ret = parse_pk(&crt->pk, pk_der, &pk_der_size);
    if (ret < 0)
        goto out;

    /* TODO: when ITA becomes standard, use results->ita.<fields> to expose more info on error */
    if (results)
        results->err_loc = AT_VERIFY_EXTERNAL;

    /* initialize the ITA context, get the set of JWKs from the `certs/` ITA Portal API endpoint,
     * send the SGX quote to the `attest/` ITA Attestation Provider API endpoint, and finally
     * receive and verify the attestation response (JWT) */
    ret = ita_init(&context);
    if (ret < 0) {
        goto out;
    }

    /* a set of JWKs may change over time, so we better get them every time */
    ret = ita_get_signing_certs(context, &set_of_jwks);
    if (ret < 0) {
        goto out;
    }

    ret = ita_send_request(context, quote, quote_size, pk_der, pk_der_size, &response);
    if (ret < 0 || !response || !response->data) {
        goto out;
    }

    /* The attestation response is JWT -- we need to verify its signature using one of the set of
     * JWKs, as well as verify its header and payload, and construct an SGX quote from the
     * JWT-payload values to be used in further `verify_*` functions */
    ret = ita_verify_response_output_quote(response, set_of_jwks, &quote_from_ita);
    if (ret < 0) {
        ret = MBEDTLS_ERR_X509_CERT_VERIFY_FAILED;
        goto out;
    }

    /* verify that the SGX quote sent to ITA has the same measurements as the constructed from the
     * ITA's JWT payload -- just for sanity */
    sgx_report_body_t* orig_body = &quote->body.report_body;
    sgx_report_body_t* ita_body  = &quote_from_ita->report_body;
    if (memcmp(&orig_body->report_data, &ita_body->report_data, sizeof(orig_body->report_data)) ||
            memcmp(&orig_body->mr_enclave, &ita_body->mr_enclave, sizeof(orig_body->mr_enclave)) ||
            memcmp(&orig_body->mr_signer, &ita_body->mr_signer, sizeof(orig_body->mr_signer))) {
        ERROR("Failed verification of JWT's SGX measurements against the original SGX quote's "
              "measurements (for sanity)\n");
        ret = MBEDTLS_ERR_X509_CERT_VERIFY_FAILED;
        goto out;
    }

    if (results)
        results->err_loc = AT_VERIFY_ENCLAVE_ATTRS;

    /* verify enclave attributes from the SGX quote body, including the user-supplied verification
     * parameter "allow debug enclave"; NOTE: "allow outdated TCB", "allow HW config needed", "allow
     * SW hardening needed" parameters were verified in ita_verify_response_output_quote() */
    ret = verify_quote_body_enclave_attributes(quote_from_ita, getenv_allow_debug_enclave());
    if (ret < 0) {
        ERROR("Failed verification of JWT's SGX enclave attributes\n");
        ret = MBEDTLS_ERR_X509_CERT_VERIFY_FAILED;
        goto out;
    }

    if (results)
        results->err_loc = AT_VERIFY_ENCLAVE_MEASUREMENTS;

    /* verify other relevant enclave information from the SGX quote */
    if (g_verify_measurements_cb) {
        /* use user-supplied callback to verify measurements */
        ret = g_verify_measurements_cb((const char*)&quote_from_ita->report_body.mr_enclave,
                                       (const char*)&quote_from_ita->report_body.mr_signer,
                                       (const char*)&quote_from_ita->report_body.isv_prod_id,
                                       (const char*)&quote_from_ita->report_body.isv_svn);
    } else {
        /* use default logic to verify measurements */
        ret = verify_quote_body_against_envvar_measurements(quote_from_ita);
    }
    if (ret < 0) {
        ERROR("Failed verification of JWT's SGX measurements\n");
        ret = MBEDTLS_ERR_X509_CERT_VERIFY_FAILED;
        goto out;
    }

    if (results)
        results->err_loc = AT_NONE;
    ret = 0;
out:
    if (context)
        ita_cleanup(context);

    if (response)
        response_cleanup(response);

    free(set_of_jwks);
    free(quote_from_ita);
    return ret;
}
