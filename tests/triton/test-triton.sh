#!/bin/bash
image_name=$1

set -x
set -e

# TensorFlow inception
mkdir -p model_repository/inception_graphdef/1
wget -O /tmp/inception_v3_2016_08_28_frozen.pb.tar.gz \
     https://storage.googleapis.com/download.tensorflow.org/models/inception_v3_2016_08_28_frozen.pb.tar.gz
(cd /tmp && tar xzf inception_v3_2016_08_28_frozen.pb.tar.gz)
mv /tmp/inception_v3_2016_08_28_frozen.pb model_repository/inception_graphdef/1/model.graphdef

# ONNX densenet
mkdir -p model_repository/densenet_onnx/1
wget -O model_repository/densenet_onnx/1/model.onnx \
     https://contentmamluswest001.blob.core.windows.net/content/14b2744cf8d6418c87ffddc3f3127242/9502630827244d60a1214f250e3bbca7/08aed7327d694b8dbaee2c97b8d0fcba/densenet121-1.2.onnx

# Test triton base image
docker run --name test-triton -u root -d --shm-size=1g --ulimit memlock=-1 --ulimit stack=67108864 -p9000:8000 -p9001:8001 -p9002:8002 -v $(pwd)/model_repository:/models $image_name tritonserver --model-repository=/models

for i in {1..5}
do
    status=$(curl -w "%{http_code}\n" http://localhost:9000/v2/health/ready | tail -1)
    if [ $status -eq 200 ]; then
        echo "Triton server ready, starting workers ..."
        break
    fi
    echo "Waiting for Triton server to get ready ..."

    #The sleep time is based on the current models and is bound to change if the models are changed. 
    sleep $((3+$i))
done

if [ $status -ne 200 ]; then
    echo "Triton server is not running."
    docker logs test-triton
    exit 1
fi

docker build -f Dockerfile.client -t tritonserver_client .

docker run --rm --net=host tritonserver_client /workspace/clients/bin/image_client -u localhost:9000 -m densenet_onnx -s INCEPTION /workspace/images/mug.jpg | {
    passflag=false
    while IFS= read -r line
    do
        if [[ "$line" == *"COFFEE MUG"* ]]; then
            passflag=true
        fi
    done
    if [ $passflag -ne true ]; then
        exit 1
    fi
}

docker run --rm --net=host tritonserver_client /workspace/clients/bin/image_client -u localhost:9000 -m inception_graphdef -s INCEPTION /workspace/images/mug.jpg | {
    passflag=false
    while IFS= read -r line
    do
        if [[ "$line" == *"COFFEE MUG"* ]]; then
            passflag=true
        fi
    done
    if [ $passflag -ne true ]; then
        exit 1
    fi
}

docker run --rm --net=host tritonserver_client /workspace/clients/bin/simple_http_string_infer_client -u localhost:9000
docker run --rm --net=host tritonserver_client /workspace/clients/bin/simple_http_infer_client -u localhost:9000

docker stop test-triton
docker rm -f test-triton 2>/dev/null

exit 0
