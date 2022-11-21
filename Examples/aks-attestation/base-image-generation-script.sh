# Create Server image
docker build -f aks-secret-prov-server.dockerfile -t aks-secret-prov-server-img .

# Create Client image
docker build -f aks-secret-prov-client.dockerfile -t aks-secret-prov-client-img .

# Clone GSC repo
git clone --depth 1 https://github.com/gramineproject/gsc.git
cd gsc
cp ../config.yaml.template config.yaml

# Generate an unsigned GSC image
./gsc build aks-secret-prov-client-img ../aks-secret-prov-client.manifest

# Create a test signing key, and generate the signed image
openssl genrsa -3 -aes128 -passout pass:test@123 -out enclave-key.pem 3072
./gsc sign-image aks-secret-prov-client-img enclave-key.pem -p test@123
