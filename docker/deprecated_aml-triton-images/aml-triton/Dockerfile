# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

FROM mcr.microsoft.com/azureml/o16n-base/python-assets:20201124.26665401 AS inferencing-assets

# DisableDockerDetector "Deprecated"
FROM nvcr.io/nvidia/tritonserver:20.10-py3

USER root:root

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV DEBIAN_FRONTEND noninteractive

# Install Common Dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    # SSH and RDMA
    libmlx5-1 \
    librdmacm1 \
    libibverbs1 \
    libdapl2 \
    dapl2-utils \
    psmisc \
    iproute2 && \
    # Others
    apt-get install -y \
    nginx-light \
    runit \
    rsyslog \
    curl \
    bzip2 \
    libbz2-1.0 \
    wget \
    cpio \
    ca-certificates \
    libcurl3-gnutls \
    libcurl4 \
    libcurl4-openssl-dev && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/*

# Inference
# Copy logging utilities and rsyslog configuration files, etc.
COPY --from=inferencing-assets /artifacts /var/

# Remove unused parts and replace with Triton stuff
RUN rm -rf /var/iot-server && \
    rm -rf /var/runit/iot-server && \
    rm -rf /var/runit/nginx && \
    rm -rf /var/runit/gunicorn
COPY --from=inferencing-assets /artifacts/triton_runit/triton /var/runit/triton
COPY --from=inferencing-assets /artifacts/triton_runit/gunicorn /var/runit/gunicorn

RUN cp /var/configuration/rsyslog.conf /etc/rsyslog.conf

# Conda Environment
ENV MINICONDA_VERSION 4.7.12.1
ENV PATH /opt/miniconda/bin:$PATH
RUN wget -qO /tmp/miniconda.sh https://repo.continuum.io/miniconda/Miniconda3-${MINICONDA_VERSION}-Linux-x86_64.sh && \
    bash /tmp/miniconda.sh -bf -p /opt/miniconda && \
    conda clean -ay && \
    rm -rf /opt/miniconda/pkgs && \
    rm /tmp/miniconda.sh && \
    find / -type d -name __pycache__ | xargs rm -rf

# Fix components vulnerability alerts
RUN apt-get update && apt-get install -y libgnutls28-dev pkg-config
RUN wget https://ftp.gnu.org/gnu/wget/wget-1.20.3.tar.gz
RUN tar -xzf wget-1.20.3.tar.gz && cd wget-1.20.3 && \
    ./configure --prefix=/ && make && make install
RUN rm -rf wget-1.20.3.tar.gz wget-1.20.3

RUN apt-get --purge remove -y wget \
    perl \
    vim \
    gcc-7-base \
    gpg \
    python3-pip && \
    apt-get -y autoremove && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y libgomp1

COPY ./fix_model_dir.sh /tmp
RUN bash /tmp/fix_model_dir.sh
RUN rm /tmp/fix_model_dir.sh

# Setup trtion inference server
ENV OMP_WAIT_POLICY=PASSIVE
ENV AZUREML_ASYNC_SERVING=True
EXPOSE 5001 8000 8001 8002

ENTRYPOINT []
