FROM mcr.microsoft.com/azureml/base-gpu:openmpi3.1.2-cuda10.1-cudnn7-ubuntu18.04

# To resolve horovod hangs due to a known NCCL issue in version 2.4.
# Can remove it once we upgrade NCCL to 2.5+.
# https://github.com/horovod/horovod/issues/893
ENV NCCL_TREE_THRESHOLD=0

# Install Horovod, temporarily using CUDA stubs
RUN ldconfig /usr/local/cuda/lib64/stubs && \
    conda install -y conda=4.8.4 python=3.6.2 && \
    conda clean -ay && \
    # ruamel.yaml is vulnerable, up to version 0.16.7
    # https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2019-20478
    # install ruamel.yaml version 0.16.10
    conda install -y ruamel.yaml==0.16.10 && \
    # ruamel_yaml is a copy of ruamel.yaml package
    # conda installs version ruamel_yaml v0.15.87 which is vulnerable
    # force uninstall it leaving other packages intact
    conda remove --force -y ruamel_yaml && \

    # Install AzureML SDK
    pip install --no-cache-dir azureml-defaults && \
    # Install PyTorch
    pip install torch==1.5.0 && \
    pip install --no-cache-dir torchvision==0.5.0 && \
    pip install --no-cache-dir mkl==2018.0.3 && \
    # Install Horovod
    pip install --no-cache-dir horovod==0.19.1 && \
    ldconfig && \
    pip install tensorboard==1.14.0 && \
    pip install future==0.17.1