FROM mcr.microsoft.com/azureml/base:openmpi3.1.2-ubuntu18.04

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /usr/share/man/*

RUN conda install -y conda=4.7.12 python=3.6.2 && conda clean -ay && \
    # Install AzureML SDK
    pip install --no-cache-dir azureml-defaults && \
    # Install AzureML Reinforcement Learning Package
    pip install --no-cache-dir azureml-contrib-reinforcementlearning && \
    # Install Tensorflow
    pip install --no-cache-dir tensorflow==1.14.0 && \
    # Install Ray & related utilities
    pip install --no-cache-dir ray[rllib,dashboard]==0.8.1 && \
    pip install --no-cache-dir psutil && \
    pip install --no-cache-dir setproctitle && \
    pip install --no-cache-dir gym[atari] && \
    conda install opencv
