## Intel Trust Authority (ITA)

**NOTE**: This document assumes familiarity with SGX attestation protocols and
RA-TLS/Secret Provisioning libraries shipped with Gramine. Please refer to
Gramine documentation for details:
- https://gramine.readthedocs.io/en/stable/attestation.html
- https://gramine.readthedocs.io/en/stable/glossary.html
- https://gramine.readthedocs.io/en/stable/sgx-intro.html#sgx-terminology

**DISCLAIMER**: This version was tested with Gramine v1.6 and ITA REST API
version `v1.0.0`.

---

[Intel Trust Authority](https://trustauthority.intel.com/) is a suite of trust
and security services that provides customers with assurance that their apps and
data are protected on the platform of their choice, including multiple cloud,
edge, and on-premises environments.

Similarly to the Intel-developed EPID protocol, the remote verifier based
on the ITA protocol needs to contact the ITA attestation provider each time it
wishes to attest an enclave. An enclave sends DCAP-formatted SGX quotes to the
client/verifier who will forward them to the ITA attestation provider to check
the enclave's validity and receive back the set of claims describing this
enclave.

For more information on ITA, refer to official documentation:
- https://www.intel.com/content/www/us/en/security/trust-authority.html
- https://docs.trustauthority.intel.com/main/articles/introduction.html

### Gramine manifest file

Because ITA attestation uses DCAP-formatted SGX quotes, the manifest in Gramine
must contain the following line:
```
sgx.remote_attestation = "dcap"
```

### RA-TLS library: `ra_tls_verify_ita.so`

Similarly to e.g. `ra_tls_verify_epid.so`, the `ra_tls_verify_ita.so` library
contains the verification callback that should be registered with the TLS
library during verification of the TLS certificate. It verifies the RA-TLS
certificate and the SGX quote by sending it to the Intel Trust Authority (ITA)
provider and retrieving the attestation response (the JWT) from it. This
library is *not* thread-safe.

Note that the JWT's signature can be verified using one of the set of JSON Web
Keys (JWKs). The RA-TLS library retrieves this set of JWKs together with
retrieving the JWT (this eager fetching of JWKs guarantees the freshness of
these keys).

The library verifies the [following set of
claims](https://docs.trustauthority.intel.com/main/articles/concept-attestation-tokens.html)
in the received JWT:
- JWT generic claims
  - `iss` (JWT token issuer, expected to be "Intel Trust Authority")
  - `ver` (JWT schema version, expected to be "1.0.0")
  - `exp` (expiration time of JWT)
  - `nbf` (not-before time of JWT)
- Verifier claims
  - `policy_ids_matched` (currently only prints them out)
  - `policy_ids_unmatched` (currently only prints them out)
- Attester claims
  - `attester_type` (expected to be "SGX")
  - `attester_tcb_status` (verified against
    `RA_TLS_ALLOW_OUTDATED_TCB_INSECURE`, `RA_TLS_ALLOW_HW_CONFIG_NEEDED`,
    `RA_TLS_ALLOW_SW_HARDENING_NEEDED`)
  - `attester_advisory_ids` (currently only prints them out)
- Intel SGX claims (TEE-specific claims)
  - `sgx_is_debuggable` (verified using `RA_TLS_ALLOW_DEBUG_ENCLAVE_INSECURE`)
  - `sgx_mrenclave` (verified against `RA_TLS_MRENCLAVE`)
  - `sgx_mrsigner` (verified against `RA_TLS_MRSIGNER`)
  - `sgx_isvprodid` (verified against `RA_TLS_ISV_PROD_ID`)
  - `sgx_isvsvn` (verified against `RA_TLS_ISV_SVN`)
  - `sgx_report_data` (verified to contain the hash of the RA-TLS public key)
- (note that EAT claims are currently not verified)

The library uses the same [SGX-specific environment variables as
`ra_tls_verify_epid.so`](https://gramine.readthedocs.io/en/stable/attestation.html#ra-tls-verify-epid-so)
and ignores the EPID-specific environment variables. Similarly to the EPID
version, instead of using environment variables, the four SGX measurements may
be verified via a user-specified callback registered via
`ra_tls_set_measurement_callback()`.

The library uses the following ITA-specific environment variables:

- `RA_TLS_ITA_PROVIDER_URL` (mandatory) -- URL for ITA provider's REST API
  endpoints.
- `RA_TLS_ITA_PORTAL_URL` (mandatory) -- URL for ITA portal's JWKs download.
- `RA_TLS_ITA_API_KEY` (mandatory) -- API key for ITA provider's API endpoint
  access.
- `RA_TLS_ITA_PROVIDER_API_VERSION` (optional) -- version of the ITA provider's
  REST API `attest` endpoint. If not specified, the default hard-coded version
  `v1` is used.
- `RA_TLS_ITA_POLICY_IDS` (optional) -- attestation policy IDs associated with
  the used API key. If not specified, no attestation policies (other than the
  default policy that verifies the SGX platform) are evaluation. Can be
  specified as a single policy or as a comma-separated set of policies. In the
  latter case, each policy must be surrounded by double quotes.

The library sets the following ITA-specific environment variables:

- `RA_TLS_ITA_JWT` -- contains the raw ITA JWT (JSON object).
- `RA_TLS_ITA_SET_OF_JWKS` -- contains the raw set of JWKs (JSON object).

### Secret Provisioning library: `secret_prov_verify_ita.so`

Similarly to `secret_prov_verify_epid.so`, this library is used in
secret-provisioning services. The only difference is that this library uses ITA
based RA-TLS flows underneath.

The library sets the same environment variables as `ra_tls_verify_ita.so`,
namely `RA_TLS_ITA_JWT` and `RA_TLS_ita_SET_OF_JWKS`.

### Building ITA libraries

The only prerequisite is that Gramine v1.6 must be installed on the system.

First, you need to copy some files from the MAA plugin, as both ITA and MAA
have many commonalities in the build process:
```sh
cp -r ../../azure/ra_tls_maa/subprojects ./
```

To build the `ra_tls_verify_ita.so` and `secret_prov_verify_ita.so` libraries,
we use the meson build system:
```sh
meson setup build/ --buildtype=release
ninja -C build/
sudo ninja -C build/ install
```

This installs the two libraries under a system-wide path. This path should be
added to the manifest file of an application that wishes to use ITA libraries
(typically manifests already contain this path).

Similarly to EPID- and DCAP-based RA-TLS/Secret Prov libraries shipped with
Gramine, the ITA-based libraries are minimized and statically linked with all
dependencies except libc ones.

### Testing ITA libraries

The ITA libraries can be tested with the
[`ra-tls-mbedtls`](https://github.com/gramineproject/gramine/tree/master/CI-Examples/ra-tls-mbedtls)
and
[`ra-tls-secret-prov`](https://github.com/gramineproject/gramine/tree/master/CI-Examples/ra-tls-secret-prov)
examples available in Gramine.

To be able to run these tests, the machine must run on the SGX enabled host, with
access to the ITA attestation provider service.

For this, we provide a patch that should be applied on top of Gramine v1.6 repo:
```sh
git clone --depth 1 --branch v1.6 https://github.com/gramineproject/gramine.git
cd gramine/
git apply ../helpers/gramine-v1.6-ci-examples.patch
```

For all examples, we set the following environment variables:
```sh
export RA_TLS_ALLOW_DEBUG_ENCLAVE_INSECURE=1
export RA_TLS_ALLOW_OUTDATED_TCB_INSECURE=1
export RA_TLS_ALLOW_HW_CONFIG_NEEDED=1
export RA_TLS_ALLOW_SW_HARDENING_NEEDED=1
```

To test the `ra-tls-mbedtls` example, cd to its directory and run:
```sh
make clean
make app ita RA_TYPE=dcap

gramine-sgx ./server &

RA_TLS_ITA_PROVIDER_URL="https://api.trustauthority.intel.com" \
RA_TLS_ITA_PORTAL_URL="https://portal.trustauthority.intel.com" \
RA_TLS_ITA_API_KEY=<ITA API key> \
RA_TLS_MRENCLAVE=<MRENCLAVE of the server enclave> \
RA_TLS_MRSIGNER=<MRSIGNER of the server enclave> \
RA_TLS_ISV_PROD_ID=<ISV_PROD_ID of the server enclave> \
RA_TLS_ISV_SVN=<ISV_SVN of the server enclave> \
./client ita

# client will successfully connect to the server via RA-TLS/ITA flows
kill %%
```

To test the `ra-tls-secret-prov` example, cd to its directory and run:
```sh
make clean
make app ita RA_TYPE=dcap

# test encrypted files client (other examples can be tested similarly)
cd secret_prov_pf

RA_TLS_ITA_PROVIDER_URL="https://api.trustauthority.intel.com" \
RA_TLS_ITA_PORTAL_URL="https://portal.trustauthority.intel.com" \
RA_TLS_ITA_API_KEY=<ITA API key> \
./server_ita wrap_key &

gramine-sgx ./client

kill %%
```
