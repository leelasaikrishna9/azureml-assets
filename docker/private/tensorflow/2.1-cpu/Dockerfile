FROM mcr.microsoft.com/azureml/openmpi3.1.2-ubuntu18.04:20200423.v1

RUN conda install -y conda=4.6.14 python=3.6.2 && conda clean -ay && \
    # Install AzureML SDK
    pip install --no-cache-dir azureml-defaults && \
    # Install Tensorflow
    pip install --no-cache-dir tensorflow==2.1.0 && \
    # Install Horovod
    pip install --no-cache-dir horovod==0.19.1