# Intel® Confidential Compute for MySQL

In the following two sections, we explain how a Docker image for a Gramine-protected MySQL version
can be built and how the image can be executed. We assume that the [prerequisites](../../README.md)
for the build and the execution phase are met.


## Build a Gramine-protected MySQL image

Perform the following steps on your system:

1. Clone the Gramine Contrib repository:
   ```sh
   git clone --depth 1 https://github.com/gramineproject/contrib.git
   ```

2. Move to the Intel® Confidential Compute for X folder:
   ```sh
   cd contrib/Intel-Confidential-Compute-for-X
   ```

3. If a new MySQL database should be used, use the following commands to initialize the database and
   to stop the initialized database afterwards. If you want to use an existing MySQL database, skip
   this step. Note that the following steps assume a new database and you need to adjust the
   commands when an exiting database is used.
   ```sh
   mkdir workloads/mysql/test_db
   docker run --rm --net=host --name init_test_db --user $(id -u):$(id -g) \
       -v $PWD/workloads/mysql/test_db:/test_db \
       -e MYSQL_ALLOW_EMPTY_PASSWORD=true -e MYSQL_DATABASE=test_db mysql:8.0.34-debian \
       --datadir /test_db &
   docker stop init_test_db
   ```

4. Encrypt MySQL database:

    1. [Install Gramine](https://gramine.readthedocs.io/en/stable/quickstart.html#install-gramine)
        as the encryption is done using the `gramine-sgx-pf-crypt` tool which is part of Gramine
        installation.

    2. Use the `gramine-sgx-pf-crypt` tool to encrypt the MySQL database `workloads/mysql/test_db`.
       The following command with generate a weak encryption key, which must not be used in
       production. The encrypted database will be stored in `/var/run/test_db_encrypted`.
       ```sh
       dd if=/dev/urandom bs=16 count=1 > workloads/mysql/base_image_helper/encryption_key
       sudo rm -rf /var/run/test_db_encrypted
       sudo gramine-sgx-pf-crypt encrypt -w workloads/mysql/base_image_helper/encryption_key \
           -i workloads/mysql/test_db -o /var/run/test_db_encrypted
       ```
       You can learn more about Gramine's support of encrypted files in the
       [corresponding documentation](https://gramine.readthedocs.io/en/stable/manifest-syntax.html#encrypted-files).

5. Perform one of the following alternatives:
    - To generate a Gramine-protected, pre-configured, non-production ready, test image for MySQL,
      execute the following script:
      ```sh
      python3 ./curate.py mysql mysql:8.0.34-debian --test
      ```
    - To generate a Gramine-protected, pre-configured MySQL image based on a user-provided MySQL
      image, execute the following to launch an interactive setup script:
      ```sh
      python3 ./curate.py mysql <your_image>
      ```

      Please provide the following inputs to the script:
      - `--datadir <database_abs_path>` when prompted for command-line arguments.
      - `-v <abs_path_to_encrypted_database>:<abs_path_to_encrypted_database>` when prompted for
        additional docker flags.
      - `<abs_path_to_encrypted_database>` and `<encryption_key>` when prompted for encrypted
        files and encryption key respectively.


## Execute Gramine-protected MySQL image

Follow the output of the image build script `curate.py` to run the generated Docker image.

Note that validation was only done on a Standard_DC8s_v3 Azure VM.


## Connect MySQL client to MySQL database

- Install MySQL client:
  ```sh
  sudo apt-get -y install mysql-client
  ```
- Connect the client to the test MySQL server:
  ```sh
  mysql -h 127.0.0.1 -uroot
  ```


## Decrypt MySQL database

- Execute the following command to decrypt the MySQL database:
  ```sh
  gramine-sgx-pf-crypt decrypt -w workloads/mysql/base_image_helper/encryption_key \
      -i /var/run/test_db_encrypted -o workloads/mysql/test_db_plain
  ```


## Contents

This directory contains the following artifacts, which help to create a Gramine-protected MySQL
image:

    .
    |-- mysql-gsc.dockerfile.template     # Template used by `curation_script.sh` to create a
    |                                       wrapper dockerfile `mysql-gsc.dockerfile` that
    |                                       includes user-provided inputs, e.g., `ca.cert` file etc.
    |                                       into the graminized MySQL image.
    |-- mysql.manifest.template           # Template used by `curation_script.sh` to create a
    |                                       user manifest file (with basic set of values defined
    |                                       for graminizing MySQL images) that will be passed to
    |                                       GSC.
