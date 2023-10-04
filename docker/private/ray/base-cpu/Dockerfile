FROM mcr.microsoft.com/azureml/openmpi3.1.2-ubuntu18.04:20200423.v1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /usr/share/man/*