## Microsoft Azure Attestation (MAA)

**NOTE**: This document assumes familiarity with SGX attestation protocols and
RA-TLS/Secret Provisioning libraries shipped with Gramine. Please refer to
Gramine documentation for details:
- https://gramine.readthedocs.io/en/stable/attestation.html
- https://gramine.readthedocs.io/en/stable/glossary.html
- https://gramine.readthedocs.io/en/stable/sgx-intro.html#sgx-terminology

**DISCLAIMER**: This version was tested with Gramine v1.5 and MAA API version
`2022-08-01`.

---

Microsoft Azure Attestation (MAA) is the attestation protocol (attestation
scheme) developed by Microsoft and available in the Microsoft Azure public
cloud. Similarly to the Intel-developed EPID protocol, the remote verifier based
on the MAA protocol needs to contact the MAA attestation provider each time it
wishes to attest an enclave. An enclave sends DCAP-formatted SGX quotes to the
client/verifier who will forward them to the MAA attestation provider to check
the enclave's validity and receive back the set of claims describing this
enclave.

![MAA based remote attestation](/Integrations/azure/ra_tls_maa/helpers/maa.svg)

The diagram above shows MAA based remote attestation. The MAA flows are very
similar to the [EPID
flows](https://gramine.readthedocs.io/en/stable/attestation.html#remote-attestation-flows-for-epid-and-dcap),
but rather than communicating with the Intel Attestation Service, the MAA flows
instead communicate with the MAA attestation provider service.

MAA attestation uses DCAP-formatted SGX quotes, so the steps 1-8 retrieve the
SGX quote similarly to the [DCAP
attestation](https://gramine.readthedocs.io/en/stable/attestation.html#remote-attestation-flows-for-epid-and-dcap).
But in contrast to the DCAP protocol, step 9 forwards the SGX quote to the MAA
attestation provider (in a so-called Attestation request), and the MAA
attestation provider replies with the Attestation response. The attestation
response embeds the JSON Web Token (JWT) that contains a set of claims about the
SGX quote. The remote user can verify the enclave measurements contained in the
JWT claims against the expected values.

In particular, the remote user should forward the received SGX quote to the
well-known MAA REST endpoint via a secure internet connection and get the MAA
attestation response (that embeds the JSON Web Token, or JWT) back. The user
then should verify the signature of the JWT (using a JWK obtained from the MAA
provider separately) and examine the contents of the JWT and decide whether to
trust the remote SGX enclave or not.

Because MAA attestation uses DCAP-formatted SGX quotes, the manifest in Gramine
must contain the following line:
```
sgx.remote_attestation = "dcap"
```

### RA-TLS library: `ra_tls_verify_maa.so`

Similarly to e.g. `ra_tls_verify_epid.so`, the `ra_tls_verify_maa.so` library
contains the verification callback that should be registered with the TLS
library during verification of the TLS certificate. It verifies the RA-TLS
certificate and the SGX quote by sending it to the Microsoft Azure Attestation
(MAA) provider and retrieving the attestation response (the JWT) from it. This
library is *not* thread-safe.

The library uses the same [SGX-specific environment variables as
`ra_tls_verify_epid.so`](https://gramine.readthedocs.io/en/stable/attestation.html#ra-tls-verify-epid-so)
and ignores the EPID-specific environment variables.  Similarly to the EPID
version, instead of using environment variables, the four SGX measurements may
be verified via a user-specified callback registered via
`ra_tls_set_measurement_callback()`.

The library uses the following MAA-specific environment variables:

- `RA_TLS_MAA_PROVIDER_URL` (mandatory) -- URL for MAA provider's REST API
  endpoints.
- `RA_TLS_MAA_PROVIDER_API_VERSION` (optional) -- version of the MAA
  provider's REST API `attest/` endpoint. If not specified, the default
  hard-coded version `2022-08-01` is used.

### Secret Provisioning library: `secret_prov_verify_maa.so`

Similarly to `secret_prov_verify_epid.so`, this library is used in
secret-provisioning services. The only difference is that this library uses MAA
based RA-TLS flows underneath.

The library uses the same [SGX-specific environment variables as
`secret_prov_verify_epid.so`](https://gramine.readthedocs.io/en/stable/attestation.html#secret-prov-verify-epid-so),
ignores the EPID-specific environment variables and expects instead the
MAA-specific environment variables.

### Building MAA libraries

The only prerequisite is that Gramine v1.5 must be installed on the system.

To build the `ra_tls_verify_maa.so` and `secret_prov_verify_maa.so` libraries,
we use the meson build system:
```sh
meson setup build/ --buildtype=release
ninja -C build/
sudo ninja -C build/ install
```

This installs the two libraries under a system-wide path. This path should be
added to the manifest file of an application that wishes to use MAA libraries
(typically manifests already contain this path).

Similarly to EPID- and DCAP-based RA-TLS/Secret Prov libraries shipped with
Gramine, the MAA-based libraries are minimized and statically linked with all
dependencies except libc ones.

### Testing MAA libraries

The MAA libraries can be tested with the
[`ra-tls-mbedtls`](https://github.com/gramineproject/gramine/tree/master/CI-Examples/ra-tls-mbedtls)
and
[`ra-tls-secret-prov`](https://github.com/gramineproject/gramine/tree/master/CI-Examples/ra-tls-secret-prov)
examples available in Gramine.

To be able to run these tests, the machine must run on the Azure cloud, with
access to the MAA attestation provider service.

For this, we provide a patch that should be applied on top of Gramine v1.5 repo:
```sh
git clone --depth 1 --branch v1.5 https://github.com/gramineproject/gramine.git
cd gramine/
git apply ../helpers/gramine-v1.5-ci-examples.patch
```

To test the `ra-tls-mbedtls` example, cd to its directory and run:
```sh
make clean
make app maa RA_TYPE=dcap

gramine-sgx ./server &

RA_TLS_ALLOW_DEBUG_ENCLAVE_INSECURE=1 \
RA_TLS_MAA_PROVIDER_URL="https://sharedcus.cus.attest.azure.net" \
RA_TLS_MRENCLAVE=<MRENCLAVE of the server enclave> \
RA_TLS_MRSIGNER=<MRSIGNER of the server enclave> \
RA_TLS_ISV_PROD_ID=<ISV_PROD_ID of the server enclave> \
RA_TLS_ISV_SVN=<ISV_SVN of the server enclave> \
./client maa

# client will successfully connect to the server via RA-TLS/MAA flows
kill %%
```

To test the `ra-tls-secret-prov` example, cd to its directory and run:
```sh
make clean
make app maa RA_TYPE=dcap

# test encrypted files client (other examples can be tested similarly)
cd secret_prov_pf

RA_TLS_ALLOW_DEBUG_ENCLAVE_INSECURE=1 \
RA_TLS_MAA_PROVIDER_URL="https://sharedcus.cus.attest.azure.net" \
./server_maa wrap_key &

gramine-sgx ./client

kill %%
```
