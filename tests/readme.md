# Introduction
This tests are designed for validating changes to any docker file using pytest. Each framework has a pipeline
set up that will execute specific tests. The tests use training SDK to validate changes.

# Test setup

Each image has a tests folder that contains test config and training scripts

base_images/
    docker/
        amlbase/
            tests/
                sample_scripts/     [This folder contians all the training scripts for this base image]
    tests/
        conftest.py                 [common test setup]
        utils.py                    [AML common methods]
        estimator/                  [Estiamtor related tests]
             test_estimator.py      [tests specific to estimator]


# How to run the tests

This example is based on running single node training for generic estimator

AzureMlCli\base_images> pytest .\tests\estimators\test_estimator.py --source_directory
.\docker\amlbase\tests\sample_scripts --config_file "full path to the config json file"
--base_image_name "image_name" --base_image_address "address" --base_image_username "username"
--base_image_password "password" --aad_sp_password "aad password"

source_directory          [required; specify the directory that contains the training script]
config_file               [required; specify the full path of the config file with test input combinations]
base_image_name           [required; image name of the base image to be used in the test]
base_image_address        [required; repository address of the base image to be used in the test]
base_image_username       [required; user name for the repository that contains the base image]
base_image_password       [required; password for the repository that contains the base image]
aad_sp_password           [required; AAD password to authenticate to the workspace SP]