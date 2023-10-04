FROM mcr.microsoft.com/azureml/base:openmpi3.1.2-ubuntu18.04

# Install apt-utils, tools and dependencies, upgrade pip
RUN apt-get update && \
    apt-get install -y --no-install-recommends apt-utils \
        software-properties-common \
        build-essential \
        libboost-all-dev \
        zlib1g-dev \
        cmake && \
    pip install --upgrade pip
    
# Build and install Vowpal Wabbit
RUN git clone --branch 8.8.0 --recursive https://github.com/VowpalWabbit/vowpal_wabbit.git && \
    cd vowpal_wabbit && \
    mkdir build && \
    cd build && \
    cmake .. -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTS=OFF -DVW_INSTALL=ON -DBUILD_PYTHON=ON -DPY_VERSION=3.7 && \
    make install && \
    cd .. && \
    pip install .
