# Install Gramine, and build the ra-tls-secret-prov files and
# relevant libraries to be used in the server and client Dockerfiles.
bash ./install_gramine.sh

# Create Server image
cd gramine/CI-Examples/ra-tls-secret-prov
make clean && make dcap
cd ../../../
docker build -f aks-secret-prov-server.dockerfile -t aks-secret-prov-server-img .

# Create Client image
cd gramine/CI-Examples/ra-tls-secret-prov
make clean && make secret_prov_min_client
cd ../../../
docker build -f aks-secret-prov-client.dockerfile -t aks-secret-prov-client-img .

rm -rf gramine/
