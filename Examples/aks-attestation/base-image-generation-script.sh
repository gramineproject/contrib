# Install Gramine, and build the ra-tls-secret-prov files and
# relevant libraries to be used in the server and client Dockerfiles.
/bin/sh install_gramine.sh

# Create Server image
cd gramine/CI-Examples/ra-tls-secret-prov
#- Secret Provisioning flows, ECDSA-based (DCAP) attestation:

```sh
make clean && make app dcap RA_TYPE=dcap

# test encrypted files client (other examples can be tested similarly)
cd secret_prov_pf
RA_TLS_ALLOW_DEBUG_ENCLAVE_INSECURE=1 \
RA_TLS_ALLOW_OUTDATED_TCB_INSECURE=1 \
./server_dcap wrap_key &

gramine-sgx ./client

kill %%
```
cd ../../../
docker build -f aks-secret-prov-server-azure.dockerfile -t aks-secret-prov-server-img .

# Create Client image
cd gramine/CI-Examples/ra-tls-secret-prov
make clean && make secret_prov_min_client
cd ../../../
docker build -f aks-secret-prov-client.dockerfile -t aks-secret-prov-client-img .

rm -rf gramine/
