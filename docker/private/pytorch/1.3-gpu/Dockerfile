FROM mcr.microsoft.com/azureml/base-gpu:openmpi3.1.2-cuda10.1-cudnn7-ubuntu18.04

# To resolve horovod hangs due to a known NCCL issue in version 2.4.
# Can remove it once we upgrade NCCL to 2.5+.
# https://github.com/horovod/horovod/issues/893
ENV NCCL_TREE_THRESHOLD=0

# Install Horovod, temporarily using CUDA stubs
RUN ldconfig /usr/local/cuda/lib64/stubs && \
    conda install -y conda=4.6.14 python=3.6.2 && conda clean -ay && \
    # Install AzureML SDK
    pip install --no-cache-dir azureml-defaults && \
    # Install PyTorch
    pip install torch==1.3.1 && \
    pip install --no-cache-dir torchvision==0.4.1 && \
    pip install --no-cache-dir mkl==2018.0.3 && \
    # Install Horovod
    pip install --no-cache-dir horovod==0.18.1 && \
    ldconfig && \
    pip install tensorboard==1.14.0 && \
    pip install future==0.17.1