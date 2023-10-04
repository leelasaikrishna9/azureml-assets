FROM mcr.microsoft.com/azureml/base:latest

# R Packages
RUN conda install -c r -y r-essentials openssl=1.1.1c r-devtools && conda clean -ay

# AzureML SDK
ENV TAR="/bin/tar"
RUN pip install --no-cache-dir azureml-defaults rpy2 azureml-dataset-runtime[fuse,pandas] && \
    R -e "remotes::install_github(repo = 'https://github.com/Azure/azureml-sdk-for-r')"
