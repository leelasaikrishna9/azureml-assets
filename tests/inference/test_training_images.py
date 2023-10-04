import json
import os
import subprocess
import time

import requests

from tests.inference.inference_utils import (
    start_docker,
    assert_response_headers,
    get_swagger,
    score_with_post,
    send_post_rawhttp_requests,
    send_get_rawhttp_requests
)

GENERAL_RESOURCE_FOLDER_NAME = "score_files"
MODEL_RESOURCE_FOLDER_NAME = "score_with_model"
BASIC_RESOURCE_FOLDER_NAME = "score_basic"
SCORE_SCRIPT = "score.py"
RAW_SCORE_SCRIPT = "score_raw.py"
SCHEMA_SCORE_SCRIPT = "score_schema.py"
MODEL_PATH = "model/1"

port = 5001


def test_send_rawhttp_with_main_py(base_image_name):
    try:
        print('Starting server at port:{}'.format(port))

        container = start_docker(
            base_image_name,
            GENERAL_RESOURCE_FOLDER_NAME,
            ports=port
        )

        time.sleep(5)
        target_url = 'http://127.0.0.1:{}'.format(port)

        data = bytes([1, 2, 3])
        status_code, response_body = send_post_rawhttp_requests(data, target_url)
        assert 200 == status_code
        body = bytearray(data)
        body.reverse()
        body = bytes(body)
        assert response_body == body

        # send get request
        status_code, _ = send_get_rawhttp_requests(target_url)
        assert 200 == status_code
        assert "Starting AzureML Inference Server HTTP." in container.logs().decode("UTF-8")
    finally:
        container.remove(force=True)


def test_post_with_score_py(base_image_name):
    try:
        print('Starting server at port:{}'.format(port))

        environment_variables = {
            "AZUREML_ENTRY_SCRIPT": SCORE_SCRIPT
        }

        container = start_docker(
            base_image_name,
            GENERAL_RESOURCE_FOLDER_NAME,
            ports=port,
            environment_variables=environment_variables
        )

        time.sleep(5)

        headers = {"Content-Type": "application/json"}
        payload_data = "score_py"
        payload = json.dumps({"data": payload_data})

        req = score_with_post(data=payload, headers=headers, port=port)
        assert_response_headers(req.headers)

        assert payload in container.logs().decode("UTF-8")
        assert req._content == b'{"bar": 24}'
    finally:
        container.remove(force=True)


def test_post_with_model(base_image_name):
    try:
        print('Starting server at port:{}'.format(port))

        environment_variables = {
            "AZUREML_ENTRY_SCRIPT": SCORE_SCRIPT,
            "AZUREML_MODEL_DIR": MODEL_PATH
        }

        data_path = os.path.join(".", "score_with_model", "sample-request.json")

        with open(data_path) as f:
            payload_data = json.load(f)

        container = start_docker(
            base_image_name,
            MODEL_RESOURCE_FOLDER_NAME,
            ports=port,
            environment_variables=environment_variables
        )

        time.sleep(5)

        headers = {"Content-Type": "application/json"}

        payload = json.dumps(payload_data)

        req = score_with_post(data=payload, headers=headers, port=port)
        assert_response_headers(req.headers)

        assert req._content == b'[11055.977245525679, 4503.079536107787]'

    finally:
        container.remove(force=True)


def test_score_basic(base_image_name):
    try:
        print('Starting server at port:{}'.format(port))

        environment_variables = {
            "AZUREML_ENTRY_SCRIPT": SCORE_SCRIPT
        }

        container = start_docker(
            base_image_name,
            BASIC_RESOURCE_FOLDER_NAME,
            ports=port,
            environment_variables=environment_variables
        )

        time.sleep(5)

        headers = {"Content-Type": "application/json"}

        url = f"http://127.0.0.1:{port}/score?from=get"
        get_response = requests.get(url=url)
        assert_response_headers(get_response.headers)

        assert get_response.status_code == 200
        assert "b'{\"from\": \"get\", \"TotalTime\":" in str(get_response._content)

        payload_data = '{"from": "post"}'

        req = score_with_post(data=payload_data, headers=headers, port=port)
        assert_response_headers(req.headers)

        assert payload_data in container.logs().decode("UTF-8")
        assert "b'{\"from\": \"post\", \"TotalTime\":" in str(req._content)

    finally:
        container.remove(force=True)


def test_score_raw(base_image_name):
    try:
        print('Starting server at port:{}'.format(port))

        environment_variables = {
            "AZUREML_ENTRY_SCRIPT": RAW_SCORE_SCRIPT
        }

        container = start_docker(
            base_image_name,
            GENERAL_RESOURCE_FOLDER_NAME,
            ports=port,
            environment_variables=environment_variables
        )

        time.sleep(5)

        headers = {"Content-Type": "application/json"}
        payload_data = '{"from": "post"}'

        url = f"http://127.0.0.1:{port}/score"
        options_response = requests.options(url=url, data=payload_data)
        assert options_response.status_code == 200
        assert_response_headers(options_response.headers)

        req = score_with_post(data=payload_data, headers=headers, port=port)
        assert_response_headers(req.headers)

        assert payload_data in container.logs().decode("UTF-8")
        assert "b'{\"from\": \"post\", \"TotalTime\":" in str(req._content)
    finally:
        container.remove(force=True)


def test_score_schema(base_image_name):
    try:
        print('Starting server at port:{}'.format(port))

        environment_variables = {
            "AZUREML_ENTRY_SCRIPT": SCHEMA_SCORE_SCRIPT
        }

        container = start_docker(
            base_image_name,
            GENERAL_RESOURCE_FOLDER_NAME,
            ports=port,
            environment_variables=environment_variables
        )

        time.sleep(5)

        headers = {"Content-Type": "application/json"}
        swagger_response = get_swagger(port=port)
        assert swagger_response.status_code == 200
        assert_response_headers(swagger_response.headers)
        assert "swagger" in swagger_response.json().keys()

        error_payload = '{"data": [[1, 2, 3, 4, 5, 6, 7, 8, 9]]}'

        req = score_with_post(data=error_payload, headers=headers, port=port)
        assert req.status_code == 500

        payload_data = '{"data": [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]]}'

        req = score_with_post(data=payload_data, headers=headers, port=port)
        assert req.status_code == 200

        assert_response_headers(req.headers)

        assert req._content == b'[55]'
    finally:
        container.remove(force=True)


def test_debuggability(base_image_name):
    try:
        print('Starting server at port:{}'.format(port))

        environment_variables = {
            "AZUREML_ENTRY_SCRIPT": SCORE_SCRIPT,
            "AML_DBG_MODEL_INFO": 'true',
            "AML_DBG_RESOURCE_INFO": 'true'
        }

        container = start_docker(
            base_image_name,
            BASIC_RESOURCE_FOLDER_NAME,
            ports=port,
            environment_variables=environment_variables
        )

        time.sleep(5)

        headers = {"Content-Type": "application/json"}

        requestID = "req-abc123"
        traceID = "trace-def456"
        headers["x-ms-request-id"] = requestID
        headers["TraceId"] = traceID
        score_script = "score_basic.py:1"
        payload = '{"from": "debug"}'
        headers["isDebug"] = 'true'

        req = score_with_post(data=payload, headers=headers, port=port)
        assert req.status_code == 200
        assert req.headers['x-ms-request-id'] == requestID
        assert req.headers['TraceId'] == traceID
        assert req.headers['x-ms-aml-model-info'] == score_script
        assert req.headers['x-ms-aml-cpu-utilization'] is not None
        assert req.headers['x-ms-aml-memory-footprint'] is not None
        assert payload in container.logs().decode("UTF-8")
    finally:
        container.remove(force=True)


def test_worker_count(base_image_name):
    try:
        print('Starting server at port:{}'.format(port))

        environment_variables = {
            "AZUREML_ENTRY_SCRIPT": SCORE_SCRIPT,
            "WORKER_COUNT": '4'
        }

        container = start_docker(
            base_image_name,
            BASIC_RESOURCE_FOLDER_NAME,
            ports=port,
            environment_variables=environment_variables
        )

        time.sleep(5)

        containerId = container.id
        command = "docker exec {} /bin/bash ./var/azureml-app/worker_script.sh".format(containerId)
        with open("/tmp/output.log", "w") as output:
            subprocess.call(command, shell=True, stdout=output, stderr=output)

        with open("/tmp/output.log") as f:
            line = f.readline().rstrip()
        assert line == "worker num: 4"
    finally:
        container.remove(force=True)
