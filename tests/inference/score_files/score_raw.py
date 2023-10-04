import time
import json

from azureml.contrib.services.aml_response import AMLResponse
from azureml.contrib.services.aml_request import rawhttp


def init():
    pass


@rawhttp
def run(data):
    try:
        # sleep 2 sec and echo
        start_time = time.time()
        input_string = data.get_data()
        print("------------ test logging, received:", input_string)
        time.sleep(2)
        output_string = "{}" if input_string == b'' else input_string
        output = json.loads(output_string)
        output["TotalTime"] = time.time() - start_time
        return AMLResponse(output, 200, {}, json_str=True)
    except Exception as e:
        error = str(e)
        return AMLResponse({"error": error}, 500, {}, json_str=True)
