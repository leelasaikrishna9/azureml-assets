 
Nvidia's Triton Server releases correspond to release [tags][tritonserver-tags] in 
Nvidia's TritonServer Github [project][tritonserver-github].  

For example, as specified [here][nvidia-dl-frameworks-matrix], nvcr.io/nvidia/tritonserver:21.02-py3 
corresponds to Triton Inference Server tag [v2.7.0][tritonserver-v2.7.0].

test-triton.sh implements [QuickStart][tritonserver-quickstart] from the Github project.

When Nvidia releases new TritonServer container image, there may be corresponding changes
in the [QuickStart][tritonserver-quickstart].  

test-triton.sh should be kept up to date with such changes to validate aml-triton base image.

Apply any changes from [docs/examples/fetch_models.sh][tritonserver-fetch_models] to test-triton.sh.

Steps to locally run test-triton.sh.
```bash
1. Build aml-triton Dockerfile locally 
cd base_images/docker/public/base-triton/aml-triton
cat Dockerfile > Dockerfile.loc
cat Dockerfile.private >> Dockerfile.loc
image_name=aml-triton
docker build $image_name -f Dockerfile.loc .
2. Run test
cd base_images/tests/triton
test-triton.sh $image_name
```

If Dockerfile.client fails to build in test-triton.sh, refer to [Dockerfile.sdk][tritonserver-dockerfile-sdk].

[aml-triton-dockerfile]: https://msdata.visualstudio.com/DefaultCollection/Vienna/_git/AzureMlCli?path=%2Fbase_images%2Fdocker%2Fpublic%2Fbase-triton%2Faml-triton%2FDockerfile&version=GBmaster&line=6&lineEnd=7&lineStartColumn=1&lineEndColumn=1&lineStyle=plain&_a=contents
[nvidia-dl-frameworks-matrix]: https://docs.nvidia.com/deeplearning/frameworks/support-matrix/index.html
[tritonserver-quickstart]: https://github.com/triton-inference-server/server/blob/master/docs/quickstart.md
[tritonserver-tags]: https://github.com/triton-inference-server/server/tags
[tritonserver-github]: https://github.com/triton-inference-server/server
[tritonserver-v2.7.0]: https://github.com/triton-inference-server/server/tree/v2.7.0
[tritonserver-fetch_models]: https://github.com/triton-inference-server/server/blob/master/docs/examples/fetch_models.sh
[tritonserver-dockerfile-sdk]: https://github.com/triton-inference-server/server/blob/master/Dockerfile.sdk