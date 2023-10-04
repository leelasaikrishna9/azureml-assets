FROM mcr.microsoft.com/azureml/openmpi3.1.2-cuda10.0-cudnn7-ubuntu18.04:20200704.v1

# Install Horovod, temporarily using CUDA stubs
RUN ldconfig /usr/local/cuda/lib64/stubs && \
    conda install -y conda=4.6.14 python=3.6.2 && conda clean -ay && \
    # Install AzureML SDK
    pip install --no-cache-dir azureml-defaults && \
    # Install AzureML DataPrep to enable mounting of datasets
    pip install --no-cache-dir azureml-dataset-runtime[fuse,pandas] && \
    # Install TensorFlow
    pip install --no-cache-dir tensorflow-gpu==2.0.0 && \
    # Install Horovod
    pip install --no-cache-dir horovod==0.18.1 && \
    ldconfig
