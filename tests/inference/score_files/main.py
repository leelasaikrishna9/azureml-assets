from azureml.contrib.services.aml_request import rawhttp
from azureml.contrib.services.aml_response import AMLResponse


def init():
    print("This is init() of main.py")


@rawhttp
def run(request):
    print("This is run() of main.py")
    print("Request: [{0}]".format(request))
    if request.method == 'GET':
        respBody = str.encode(request.full_path)
        return AMLResponse(respBody, 200)
    elif request.method == 'POST':
        reqBody = request.get_data(False)
        respBody = bytearray(reqBody)
        respBody.reverse()
        respBody = bytes(respBody)
        return AMLResponse(respBody, 200)
    else:
        return AMLResponse("bad request", 500)
