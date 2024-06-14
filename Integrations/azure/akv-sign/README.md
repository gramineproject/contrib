# Enclave signing with Azure Key Vault's Managed HSM

SGX enclaves must be signed using a 3072-bit RSA key. This key needs to be
protected and must not be disclosed to anyone. Typically for production
deployments, you should use a key secured in a Hardware Security Module (HSM).

This directory contains the plugin to Gramine tools as well as Dockerfile
templates that enable support for production signing of SGX enclaves using keys
from Azure Key Vault (AKV) Managed HSM.

## Prerequisites for SGX enclave signing

- Azure Subscription with access to Azure Key Vault's Managed HSM.
- 3072-bit RSA private key with a public exponent 3 created in this HSM. Please
  note that only Managed HSM supports setting public exponent.
- Granted access permissions to the person who will use the key for signing the
  SGX enclave (the "Managed HSM Crypto User" using `az keyvault role
  assignment`).
- Logged into Azure CLI.

Please see [`create_rsa_key`](https://azuresdkdocs.blob.core.windows.net/$web/python/azure-keyvault-keys/latest/azure.keyvault.keys.html#azure.keyvault.keys.KeyClient.create_rsa_key)
for creating the key in Azure Key Vault Managed HSM.

## Running

The command to sign the enclave with AKV's Managed HSM looks like this:
```
./gramine-sgx-akv-sign \
  --manifest <your-app-manifest> --output <your-app-manifest>.sgx \
  --url https://myakv-mhsm.managedhsm.azure.net --key sgx_sign_key
```

where `sgx_sign_key` is the name of the RSA private key created in the AKV's
Managed HSM with Vault URL `https://myakv-mhsm.managedhsm.azure.net`.

## Templates for use with Gramine Shielded Containers (GSC)

This directory contains two Dockerfile templates, intended for use with GSC's
`sign-image` command. GSC `sign-image` command can take in a user supplied
Dockerfile as an argument to `--template` to sign the graminized docker image.
Please note that these are templates and the users need to update the template
with the required details to make it a self-contained Dockerfile before passing
it to `gsc sign-image` command.
