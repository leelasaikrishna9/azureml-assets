#
# tritonserver-21.02-py3-inference static Dockerfile
#

# DisableDockerDetector "Deprecated"
ARG PYTHON_ASSETS_IMAGE=mcr.microsoft.com/azureml/o16n-base/python-assets
ARG PYTHON_ASSETS_TAG=20210525.38560113
ARG BASE_TRITON_IMAGE=nvcr.io/nvidia/tritonserver
ARG BASE_TRITON_TAG=21.02-py3

FROM $PYTHON_ASSETS_IMAGE:$PYTHON_ASSETS_TAG AS inferencing-assets
FROM $BASE_TRITON_IMAGE:$BASE_TRITON_TAG

USER root:root

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV DEBIAN_FRONTEND noninteractive
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

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
    rm -rf /var/runit/gunicorn && \
    rm -rf /var/configuration/nginx.conf
COPY --from=inferencing-assets /artifacts/triton_runit/triton /var/runit/triton
COPY --from=inferencing-assets /artifacts/triton_runit/nginx/app /var/configuration/app
COPY --from=inferencing-assets /artifacts/triton_runit/aml_logger/start_logger.sh /var/azureml-logger/start_logger.sh

RUN cp /var/configuration/rsyslog.conf /etc/rsyslog.conf && \
    cp /var/configuration/app /etc/nginx/sites-available/app && \
    ln -s /etc/nginx/sites-available/app /etc/nginx/sites-enabled/app && \
    rm -f /etc/nginx/sites-enabled/default

ENV SVDIR=/var/runit
ENV WORKER_TIMEOUT=300
EXPOSE 5001 8000 8001 8002

