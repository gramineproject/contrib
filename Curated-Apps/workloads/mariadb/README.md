# Gramine Curated MariaDB
In the following two sections, we explain how a Docker image for the protected MariaDB version can
be built and how the image can be executed.
[Prerequisites](https://github.com/gramineproject/contrib/tree/master/Curated-Apps/README.md) for
both the phases are assumed to be met.

## Build a confidential compute image for MariaDB
Execute the below commands on your system.

1. Clone the Gramine Contrib repository and move to the Curated-Apps folder:
   ```sh
   git clone --depth 1 https://github.com/gramineproject/contrib.git
   cd contrib/Curated-Apps
   ```

2. Initialize MariaDB database using below commands, skip this step if users want to use their
   existing MariaDB database:
   ```sh
   mkdir workloads/mariadb/test_db
   docker run --rm --net=host --name init_test_db \
       -v $PWD/workloads/mariadb/test_db:/test_db \
       -e MARIADB_ALLOW_EMPTY_ROOT_PASSWORD=true -e MARIADB_DATABASE=test_db mariadb:10.7 \
       --datadir /test_db &

   # Stop MariaDB server container using below command when database is initialized
   docker stop init_test_db
   # To allow running MariaDB server under the current non-root user.
   sudo chown -R $USER:$USER $PWD/workloads/mariadb/test_db
   ```

3. Encrypt MariaDB database

   1. Install prerequisites for encrypting MariaDB database

      [Install Gramine](https://gramine.readthedocs.io/en/latest/quickstart.html#install-gramine):
      Encryption is done using `gramine-sgx-pf-crypt` tool which is part of Gramine installation.

   2. Encrypt MariaDB database following below steps:
      ```sh
      # Create test encyption key which should not be used in production
      dd if=/dev/urandom bs=16 count=1 > workloads/mariadb/base_image_helper/encryption_key

      sudo rm -rf /var/run/test_db_encrypted
      sudo gramine-sgx-pf-crypt encrypt -w workloads/mariadb/base_image_helper/encryption_key \
          -i workloads/mariadb/test_db -o /var/run/test_db_encrypted
      ```
      The above commands encrypt MariaDB database `workloads/mariadb/test_db` to
      `/var/run/test_db_encrypted` with encryption key
      `workloads/mariadb/base_image_helper/encryption_key`.
      Learn more about [Encrypted files](https://gramine.readthedocs.io/en/stable/manifest-syntax.html#encrypted-files)
      support in Gramine.

4. Generate the test confidential compute image with encrypted database.
   ```sh
   python3 ./curate.py mariadb mariadb:10.7 test
   ```

5. Or, to generate a custom confidential compute image based on a user-provided MariaDB image,
   execute the following to launch an interactive setup script. Please input command-line argument
   as `--datadir /var/run/test_db_encrypted`.
   ```sh
   python3 ./curate.py mariadb <your_image>
   ```

## Run the confidential compute image for MariaDB

- This example was tested on a Standard_DC8s_v3 Azure VM.
- Follow the output of the `curate.py` script to run the generated Docker image(s).

## Connect MySQL client

   Install MySQL client using command:
   ```sh
   sudo apt-get -y install mysql-client
   ```

   Connect the client to the test MariaDB server created at step 4:
   ```sh
   mysql -h 127.0.0.0 -uroot
   ```

## Decrypt MariaDB database

   Execute below command to decrypt the MariaDB database:
   ```sh
   gramine-sgx-pf-crypt decrypt -w workloads/mariadb/base_image_helper/encryption_key \
       -i /var/run/test_db_encrypted -o test_db_plain
   ```

## Contents
This sub-directory contains artifacts which help in creating curated GSC MariaDB image, as explained
below:

    .
    |-- mariadb-gsc.dockerfile.template     # Template used by `curation_script.sh` to create a
    |                                       wrapper dockerfile `mariadb-gsc.dockerfile` that
    |                                       includes user-provided inputs e.g. `ca.cert` file etc.
    |                                       into the graminized MariaDB image.
    |-- mariadb.manifest.template           # Template used by `curation_script.sh` to create a
    |                                       user manifest file (with basic set of values defined
    |                                       for graminizing MariaDB images), that will be passed to
    |                                       GSC.
