FROM mcr.microsoft.com/azureml/openmpi3.1.2-cuda10.1-cudnn7-ubuntu18.04

# To resolve horovod hangs due to a known NCCL issue in version 2.4.
# Can remove it once we upgrade NCCL to 2.5+.
# https://github.com/horovod/horovod/issues/893
ENV NCCL_TREE_THRESHOLD=0

# Install Horovod, temporarily using CUDA stubs
RUN ldconfig /usr/local/cuda/lib64/stubs && \
    conda install -y python=3.6.2 pip=20.1.1 && conda clean -ay && \
    # Install AzureML SDK
    pip install --no-cache-dir azureml-defaults && \
    # Install PyTorch
    pip install torch==1.6.0 && \
    pip install --no-cache-dir torchvision==0.5.0 && \
    pip install --no-cache-dir mkl==2018.0.3 && \
    # Install Horovod
    pip install --no-cache-dir horovod==0.19.5 && \
    ldconfig && \
    pip install tensorboard==1.14.0 && \
    pip install future==0.17.1
