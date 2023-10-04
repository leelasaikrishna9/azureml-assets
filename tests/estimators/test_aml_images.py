import pytest
import json

from azureml.core import ScriptRunConfig, Environment
from azureml.core.runconfig import RunConfiguration
from tests.utils import _get_aml_compute_target, _get_aml_windows_compute_target


class TestAMLImage(object):

    def get_config():
        config_file_path = pytest.config.getoption('--config_file')
        with open(config_file_path) as f:
            return json.load(f)

    def compose_script_run_config(self, workspace, environment_definition, config, windows_docker):
        node_count = config["node_count"] if "node_count" in config else 1
        # Since we are submitting parallel runs set max node count of AmlCompute target to 10 always
        if windows_docker:
            compute_target = _get_aml_windows_compute_target(workspace, config["vm_size"], node_count)
        else:
            compute_target = _get_aml_compute_target(workspace, config["vm_size"], 10)

        test_env = Environment(name="testenv")
        test_env.docker.enabled = True
        test_env.docker.base_image = environment_definition.docker.base_image
        test_env.docker.base_image_registry.username = \
            environment_definition.docker.base_image_registry.username
        test_env.docker.base_image_registry.address = \
            environment_definition.docker.base_image_registry.address
        test_env.docker.base_image_registry.password = \
            environment_definition.docker.base_image_registry.password

        if windows_docker:
            test_env.docker.platform.os = "Windows"

        if "pip_packages" in config:
            for package in config["pip_packages"]:
                test_env.python.conda_dependencies.add_pip_package(package)
            test_env.python.user_managed_dependencies = False
        else:
            test_env.python.user_managed_dependencies = True
            test_env.spark.precache_packages = False

        script_run_config = ScriptRunConfig(source_directory=config["source_directory"],
                                            compute_target=compute_target,
                                            script=config["script_name"],
                                            environment=test_env)
        return script_run_config

    def compose_estimator_script_run_config(self, workspace, environment_definition, config):
        node_count = config["node_count"] if "node_count" in config else 1
        # Since we are submitting parallel runs set max node count of AmlCompute target to 10 always
        compute_target = _get_aml_compute_target(workspace, config["vm_size"], 10)

        run_config = RunConfiguration(framework="python")
        run_config.arguments = config["script_arguments"] if "script_arguments" in config else []
        run_config.target = compute_target.name
        run_config.node_count = node_count
        run_config.mpi.process_count_per_node = config["process_count_per_node"] if "process_count_per_node" in config\
            else 1
        run_config.environment.docker.enabled = True
        run_config.target = compute_target
        run_config.framework = config["framework"] if "framework" in config else "Python"
        run_config.tensorflow.parameter_server_count = config["parameter_server_count"] if \
            "parameter_server_count" in config else 1
        run_config.tensorflow.worker_count = config["worker_count"] if "worker_count" in config else 1
        run_config.communicator = config["communicator"] if "communicator" in config else None
        # Since pip_packages will trigger an image build, add 25 minutes timeout for each run
        # A lot of runs will be queued if all images are edited.
        # Setting time out to 4 hours to accommodate queue time.
        run_config.max_run_duration_seconds = 14400

        if "pip_packages" in config:
            for package in config["pip_packages"]:
                run_config.environment.python.conda_dependencies.add_pip_package(package)
            run_config.environment.python.user_managed_dependencies = False
        else:
            run_config.environment.python.user_managed_dependencies = True
            run_config.environment.spark.precache_packages = False

        run_config.environment.docker.base_image = environment_definition.docker.base_image
        run_config.environment.docker.base_image_registry.username = \
            environment_definition.docker.base_image_registry.username
        run_config.environment.docker.base_image_registry.address = \
            environment_definition.docker.base_image_registry.address
        run_config.environment.docker.base_image_registry.password = \
            environment_definition.docker.base_image_registry.password

        if "use_gpu" in config and config["use_gpu"]:
            run_config.environment.docker.gpu_support = True

        run_config.environment.environment_variables = config["environment_variables"] if \
            "environment_variables" in config else run_config.environment.environment_variables
        run_config.environment.python.interpreter_path = config["python_interpreter_path"] if \
            "python_interpreter_path" in config else run_config.environment.python.interpreter_path

        script_run_config = ScriptRunConfig(source_directory=config["source_directory"],
                                            script=config["script_name"],
                                            arguments=run_config.arguments,
                                            run_config=run_config)
        return script_run_config

    @pytest.mark.parametrize("config", get_config())
    def test_aml_image(self, workspace, experiment, environment_definition, config):
        print("=== Starting a new AML image test ===")
        print("Test Configuration: {}".format(json.dumps(config, indent=4, sort_keys=True)))
        windows_docker = False
        if "os_platform" in config and config["os_platform"].lower() == "windows":
            windows_docker = True

        if windows_docker:
            script_run_config = self.compose_script_run_config(
                workspace, environment_definition, config, windows_docker)
        else:
            script_run_config = self.compose_estimator_script_run_config(
                workspace, environment_definition, config)

        run = experiment.submit(script_run_config)
        with open("/tmp/run_information.txt", 'w+') as file:
            file.write("{} {}".format(experiment.name, run.id))
        print("Submitted run: id={}, number={}".format(run.id, run.number))
        run.wait_for_completion(show_output=True, wait_post_processing=True)
        details = run.get_details()
        print("Run Details: {}".format(details))
        assert "Completed" == details["status"]
