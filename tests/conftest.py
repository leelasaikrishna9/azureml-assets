from datetime import datetime

from azureml.core.experiment import Experiment
from azureml.core.runconfig import EnvironmentDefinition
from tests.utils import _get_workspace


DATETIME_FMT_STR = "%Y%m%d"


def pytest_addoption(parser):
    parser.addoption("--config_file", help="File that contains test configuration")
    parser.addoption("--base_image_name", help="Base image name")
    parser.addoption("--base_image_address", help="Base image address")
    parser.addoption("--base_image_username", help="Base image username")
    parser.addoption("--base_image_password", help="Base image password")
    parser.addoption("--aad_sp_password", help="AAD Service principle password")


def pytest_generate_tests(metafunc):
    try:
        # Image details
        base_image_name = metafunc.config.getoption('--base_image_name')
        base_image_address = metafunc.config.getoption('--base_image_address')
        base_image_username = metafunc.config.getoption('--base_image_username')
        base_image_password = metafunc.config.getoption("--base_image_password")
        aad_password = metafunc.config.getoption("--aad_sp_password")

        if base_image_name is None or base_image_address is None or base_image_username is None or \
                base_image_password is None:
            raise Exception("Base image details are required input parameters. Please specify repository details.")

        workspace = _get_workspace(aad_password)
        # metafunc.function.__name__ is the name of the test
        # Using test name to have different experiments for each type of test
        experiment = Experiment(workspace, "{}_{}".format(metafunc.function.__name__,
                                                          datetime.now().strftime(DATETIME_FMT_STR)))

        # Common parameters
        metafunc.parametrize("workspace", [workspace])
        metafunc.parametrize("experiment", [experiment])

        if 'environment_definition' in metafunc.fixturenames:
            environment_definition = EnvironmentDefinition()
            environment_definition.docker.base_image = base_image_name
            environment_definition.docker.base_image_registry.username = base_image_username
            environment_definition.docker.base_image_registry.address = base_image_address
            environment_definition.docker.base_image_registry.password = base_image_password

            metafunc.parametrize("environment_definition", [environment_definition])

    except Exception as e:
        raise Exception("Exception occurred: {}".format(e))
