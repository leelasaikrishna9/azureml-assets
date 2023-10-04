import os
import requests
import docker


def score_with_post(headers=None, data=None, port=5001):
    """
    Utility function that performs a post request

            Parameters:
                    headers: request headers
                    data: data to send
                    port: port where container is running

            Returns:
                    The response of the request to the container
    """
    url = f"http://127.0.0.1:{port}/score"
    return requests.post(url=url, headers=headers, data=data)


def assert_response_headers(res_headers):
    """
    Utility function checks the presence of the headers

            Parameters:
                    res_headers: headers
    """
    expected_headers = [
        'Server',
        'Date',
        'Content-Type',
        'Content-Length',
        'Connection',
        'x-ms-run-function-failed',
        'x-ms-request-id'
    ]
    assert all(header in res_headers for header in expected_headers)


def get_swagger(headers=None, port=5001):
    """
    Utility function that performs a post request

            Parameters:
                    headers: request headers
                    port: port where container is running

            Returns:
                    The response of the request to the container
    """
    url = f"http://127.0.0.1:{port}/swagger.json"
    return requests.get(url=url, headers=headers)


def send_get_rawhttp_requests(test_ip):
    """
    Utility function that performs a raw http get request

            Parameters:
                    test_ip: request ip address

            Returns:
                    The response status code and content of the response
    """
    header = {'Content-Type': 'application/json'}
    response = requests.get('{0}/score?param'.format(test_ip), headers=header)
    print(response.content)
    return response.status_code, response.content


def send_post_rawhttp_requests(data_payload, test_ip):
    """
    Utility function that performs a raw http get request

            Parameters:
                    data_payload: the dat payload for the post request
                    test_ip: request ip address

            Returns:
                    The response status code and content of the response
    """
    header = {'Content-Type': 'application/json'}
    response = requests.post('{0}/score'.format(test_ip), headers=header, data=data_payload)
    print(response.content)
    return response.status_code, response.content


def start_docker(
    inference_image_name,
    resources_directory,
    environment_variables={},
    overwrite_azuremlapp=True,
    ports=None,
    cap_add=[],
    volumes={},
):
    """
    Utility function that starts a docker container

            Parameters:
                    inference_image_name: Inference image name
                    resource_directory: Directory that will be mounted on the container as /var/azureml-app
                    environment_variables: Environment variables
                    overwrite_azuremlapp: Indicates if var/azureml-app will be overwritten in container
                    ports: Ports to open on container other than 5001
                    cap_add: Capabilities to add to the container
                    volumes: Additional volumes that need to be mounted to the container

            Returns:
                    container: The pointer to the running container
    """
    client = docker.from_env()

    ports = {"5001/tcp": ports}
    print("port: {}".format(ports))

    resources_directory = os.path.join(os.getcwd(), resources_directory)

    # Add resource directory to any other directories being mounted
    # The mode here indicates read only
    volumes = {resources_directory: {"bind": "/var/azureml-app", "mode": "ro"}}

    print("volumes: {}".format(volumes))
    print("The resources directory: {}".format(resources_directory))

    device_requests = []

    container = client.containers.run(
        inference_image_name,
        detach=True,
        auto_remove=True,
        ports=ports,
        volumes=volumes,
        environment=environment_variables,
        cap_add=cap_add,
        device_requests=device_requests,
    )
    return container
