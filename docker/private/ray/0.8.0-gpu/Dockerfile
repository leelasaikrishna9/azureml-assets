FROM mcr.microsoft.com/azureml/openmpi3.1.2-cuda10.0-cudnn7-ubuntu18.04:20200704.v1

RUN apt-get update &&  apt-get install -y --no-install-recommends \
    python-opengl \
    rsync \
    xvfb && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /usr/share/man/*

RUN ldconfig /usr/local/cuda/lib64/stubs && \
    conda install -y conda=4.8.3 python=3.6.2 && conda clean -ay && \
    pip install --no-cache-dir \
    azureml-defaults \
    azureml-dataset-runtime[fuse,pandas] \
    azureml-contrib-reinforcementlearning \
    gputil \
    cloudpickle==1.3.0 \
    tensorboardX \
    tensorflow-gpu==1.14.0 \
    tabulate \
    dm_tree \
    lz4 \
    ray==0.8.0 \
    ray[rllib,dashboard,tune]==0.8.0 \
    psutil \
    setproctitle \
    gym[atari] && \
    conda install -y -c conda-forge x264='1!152.20180717' ffmpeg=4.0.2 && \
    conda install opencv && \
    ldconfig
