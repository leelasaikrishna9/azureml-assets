from azureml.core.workspace import Workspace
from azureml.core.authentication import ServicePrincipalAuthentication
from azureml.core.compute import ComputeTarget, AmlCompute
from azureml.core.compute_target import ComputeTargetException
from azureml.contrib.compute import AmlWindowsCompute

_WORKSPACE_NAME = "ci_cd_01_01_2022"
_SUBSCRIPTION_ID = "4f26493f-21d2-4726-92ea-1ddd550b1d27"
_RESOURCE_GROUP = "aml_images_eastus"


def _get_service_principal_auth(service_principle_pwd):
    client_id = "6233fb89-9a1a-434e-a24b-aba3515687b1"
    tenant_id = "72f988bf-86f1-41af-91ab-2d7cd011db47"

    print("Creating Auth object with SP @ client: {0}, tenant: {1}, sub: {2}".format(client_id,
                                                                                     tenant_id,
                                                                                     _SUBSCRIPTION_ID))
    # Make sure an environment variable named 'stresstestpwd' is set to the service principal password before
    # running this script.

    auth = ServicePrincipalAuthentication(tenant_id, client_id, service_principle_pwd)
    return auth


def _get_workspace(service_principle_pwd):
    return Workspace._get_or_create(_WORKSPACE_NAME,
                                    subscription_id=_SUBSCRIPTION_ID,
                                    resource_group=_RESOURCE_GROUP,
                                    location="eastus",
                                    auth=_get_service_principal_auth(service_principle_pwd))


def _get_aml_compute_target(workspace, vm_size, node_count):
    # Use vm_size as cluster name

    name = vm_size.replace("_", "")
    try:
        target = ComputeTarget(workspace=workspace, name=name)
        if target.scale_settings.maximum_node_count < node_count:
            # update to make sure we have the right number of nodes
            target.update(max_nodes=node_count)
    except ComputeTargetException:
        compute_config = AmlCompute.provisioning_configuration(vm_size=vm_size,
                                                               min_nodes=0,
                                                               max_nodes=node_count,
                                                               idle_seconds_before_scaledown='30000')
        target = ComputeTarget.create(workspace, name, compute_config)

    target.wait_for_completion()
    return target


def _get_aml_windows_compute_target(workspace, vm_size, node_count):
    # Use vm_size as cluster name

    name = "win{}".format(vm_size.replace("_", ""))
    try:
        target = ComputeTarget(workspace=workspace, name=name)
        if target.scale_settings.maximum_node_count < node_count:
            # update to make sure we have the right number of nodes
            target.update(max_nodes=node_count)
    except ComputeTargetException:
        provisioning_config = AmlWindowsCompute.provisioning_configuration(
            vm_size=vm_size,
            min_nodes=node_count,
            max_nodes=node_count,
            remote_login_port_public_access='Enabled')
        target = AmlWindowsCompute.create(workspace, name, provisioning_config)

    target.wait_for_completion(show_output=True, timeout_in_minutes=100)
    return target
