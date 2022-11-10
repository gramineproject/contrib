# Enclave signing with Azure Key Vault's Managed HSM

SGX enclaves need to build and signed using a 3072-bit RSA key. This key needs
to be protected and must not be disclosed to anyone. Typically for production
deployments, you must use a key secured in a Hardware Security Module (HSM).

This directory contains a plugin to Gramine tools that enables support for
production signing of SGX enclaves using keys from Azure Key Vault (AKV) Managed
HSM.

## Installation

Make sure that Gramine is installed on the system. Then copy the file
`gramine-sgx-akv-sign` into Gramine installation directory like this:
```
cp gramine-sgx-akv-sign $(dirname $(which gramine-sgx-sign))
```

You may need to run the above command with `sudo` if Gramine was installed in a
system-wide directory.

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
gramine-sgx-akv-sign \
  --manifest <your-app-manifest> --output <your-app-manifest>.sgx \
  --key https://myakv-mhsm.managedhsm.azure.net:sgx_sign_key
```

where `sgx_sign_key` is the name of the RSA private key created in the AKV's
Managed HSM with URL `https://myakv-mhsm.managedhsm.azure.net`.
