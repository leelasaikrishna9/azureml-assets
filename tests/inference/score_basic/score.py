import time
import json


def init():
    pass


def run(data):
    try:
        # sleep 2 sec and echo
        print("------------ test logging, received:", data)
        start_time = time.time()
        time.sleep(2)
        output_string = data
        output = json.loads(output_string)
        output["TotalTime"] = time.time() - start_time
        return output
    except Exception as e:
        error = str(e)
        return error
