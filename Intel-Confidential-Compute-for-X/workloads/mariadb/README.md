# Intel® Confidential Compute for MariaDB

In the following two sections, we explain how a Docker image for a Gramine-protected MariaDB
version can be built and how the image can be executed. We assume that the
[prerequisites](../../README.md) for the build and the execution phase are met.

## Build a Gramine-protected MariaDB image

Perform the following steps on your system:

1. Clone the Gramine Contrib repository:
   ```sh
   git clone --depth 1 https://github.com/gramineproject/contrib.git
   ```

2. Move to the Intel® Confidential Compute for X folder:
   ```sh
   cd contrib/Intel-Confidential-Compute-for-X
   ```

3. If a new MariaDB database should be used, use the following commands to initialize the database
   and to stop the initialized database afterwards. If you want to use an existing MariaDB
   database, skip this step. Note that the following steps assume a new database and you need to
   adjust the commands when an existing database is used.
   ```sh
   mkdir workloads/mariadb/test_db
   docker run --rm --net=host --name init_test_db \
       -v $PWD/workloads/mariadb/test_db:/test_db \
       -e MARIADB_RANDOM_ROOT_PASSWORD=yes -e MARIADB_DATABASE=test_db mariadb:11.0.3-jammy \
       --datadir /test_db &
   docker stop init_test_db
   sudo chown -R $USER:$USER $PWD/workloads/mariadb/test_db
   ```
   Note: The user is supposed to remember the generated root password printed to stdout
   `(GENERATED ROOT PASSWORD: .....)`.

4. Encrypt MariaDB database:

   1. [Install Gramine](https://gramine.readthedocs.io/en/stable/installation.html)
      as the encryption is done using the `gramine-sgx-pf-crypt` tool which is part of Gramine
      installation.

   2. Use the `gramine-sgx-pf-crypt` tool to encrypt the database `workloads/mariadb/test_db`.
      The encrypted database will be stored in the `test_db_encrypted` directory under the newly
      created `tmpfs` mount point `/mnt/tmpfs`.
      ```sh
      sudo mkdir -p /mnt/tmpfs
      sudo mount -t tmpfs tmpfs /mnt/tmpfs
      mkdir /mnt/tmpfs/test_db_encrypted

      dd if=/dev/urandom bs=16 count=1 > workloads/mariadb/base_image_helper/encryption_key
      rm -rf /mnt/tmpfs/test_db_encrypted/*
      gramine-sgx-pf-crypt encrypt -w workloads/mariadb/base_image_helper/encryption_key \
         -i workloads/mariadb/test_db -o /mnt/tmpfs/test_db_encrypted
      ```
      You can learn more about Gramine's support of encrypted files in the
      [corresponding documentation](https://gramine.readthedocs.io/en/stable/manifest-syntax.html#encrypted-files).

5. Perform one of the following alternatives:
    - To generate a Gramine-protected, pre-configured, non-production ready, test image for MariaDB,
      execute the following script:
      ```sh
      python3 ./curate.py mariadb mariadb:11.0.3-jammy --test
      ```
    - To generate a Gramine-protected, pre-configured MariaDB image based on a user-provided MariaDB
      image, execute the following to launch an interactive setup script:
      ```sh
      python3 ./curate.py mariadb <your_image>
      ```

      Please provide the following inputs to the script:
      - `--datadir <database_abs_path>` when prompted for command-line arguments.
      - `-v <abs_path_to_encrypted_database>:<abs_path_to_encrypted_database>` when prompted for
        additional docker flags.
      - `<abs_path_to_encrypted_database>` and `<encryption_key>` when prompted for encrypted
        files and encryption key respectively.

## Execute Gramine-protected MariaDB image

Follow the output of the image build script `curate.py` to run the generated Docker image.

Note that validation was only done on a Standard_DC8s_v3 Azure VM.

## Connect MySQL client

MariaDB is fully compatible with MySQL client. Install MySQL client:
```sh
sudo apt-get -y install mysql-client
```

Connect the client to test the MariaDB server:
```sh
mysql -h 127.0.0.1 -uroot -p'my-random-root-pw'
# replace my-random-root-pw with generated root password in step 3
```

## Decrypt MariaDB database

Execute the following command to decrypt the MariaDB database:
```sh
gramine-sgx-pf-crypt decrypt -w workloads/mariadb/base_image_helper/encryption_key \
      -i /mnt/tmpfs/test_db_encrypted -o workloads/mariadb/test_db_plain
```

## Contents

This directory contains the following artifacts, which help to create a Gramine-protected MariaDB
image:

    .
    |-- mariadb-gsc.dockerfile.template     # Template used by `curation_script.sh` to create a
    |                                         wrapper dockerfile `mariadb-gsc.dockerfile` that
    |                                         includes user-provided inputs, e.g., `ca.cert` file
    |                                         etc. into the graminized MariaDB image.
    |-- mariadb.manifest.template           # Template used by `curation_script.sh` to create a
    |                                         user manifest file (with basic set of values defined
    |                                         for graminizing MariaDB images) that will be passed
    |                                         to GSC.
    |-- base_image_helper/                  # This directory contains `encrypted_files.txt` which
    |                                         contains encrypted database directory required for
    |                                         running the test MariaDB image.
    |-- docker_run_flags.txt                # This file contains docker run flags required for
    |                                         running the test MariaDB image.
    |-- insecure_args.txt                   # This file contains command line arguments required
    |                                         for running the test MariaDB image.
