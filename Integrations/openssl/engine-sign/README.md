# Enclave signing with a HSM using OpenSSL engine

SGX enclaves must be signed using a 3072-bit RSA key. This key needs to be
protected and must not be disclosed to anyone. Typically for production
deployments, you should use a key secured in a Hardware Security Module (HSM).

This directory contains the plugin to Gramine tools and templates that enable
support for production signing of SGX enclaves using keys from a HSM accessible
using OpenSSL engine.

## Prerequisites for SGX enclave signing

- OpenSSL engine-based access available for the HSM.
- 3072-bit RSA private key with a public exponent 3 created in this HSM. Please
  note that only Managed HSM supports setting public exponent.
- Tools installed and the user is authenticated to access to the HSM.

## Running

The command to sign the enclave with a HSM using OpenSSL engine looks like this:
```
./gramine-sgx-ossl-sign \
  --manifest <your-app-manifest> --output <your-app-manifest>.sgx \
  --engine <openssl_engine> --key <sgx_sign_key>
```

where `sgx_sign_key` is the name of the RSA private key created in the HSM
accessible through the engine `openssl_engine`.

