FROM mcr.microsoft.com/azureml/openmpi3.1.2-cuda10.1-cudnn7-ubuntu18.04

# Install Horovod, temporarily using CUDA stubs
RUN ldconfig /usr/local/cuda/lib64/stubs && \
    conda install -y python=3.6.2 pip=20.1.1 && conda clean -ay && \
    # Install AzureML SDK
    pip install --no-cache-dir azureml-defaults && \
    # Install Tensorflow
    pip install --no-cache-dir tensorflow-gpu==2.2.0 && \
    # Install Horovod
    pip install --no-cache-dir horovod==0.19.5 && \
    ldconfig