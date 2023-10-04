#!/bin/bash

# All images added to the ACR before n number of days will be deleted

acr_registry_name=$1
n=$2
repository_prefix=$3

echo "Deleting from ACR registry $acr_registry_name all images older than $n days"
retention_start_date=$(date -d "$x -$n days" +%Y-%m-%d)
echo "Retention days: $n"
echo "Retention start date: $retention_start_date"

# Each repository image should be deleted
# Repository names are folder names within private and public folder
repository_names=$(ls -l base_images/docker/private | egrep '^d' | awk '{print $9}')
# Add empty space between the two ls commands. Without space it will append to end of ls result
repository_names+=" "
repository_names+=$(ls -l base_images/docker/public | egrep '^d' | awk '{print $9}')

# Loop through all repository names and delete older images
for repository_name in ${repository_names[@]}
do
    if [[ $repository_name == _* ]]; then
        repository_name=${repository_name#"_"}
    fi
    if [ ! -z "$3" ]
    then
        echo "repository prefix was provided"
        repository_name=$repository_prefix/$repository_name
    fi
    echo "Deleting old images from repository $repository_name"
    az acr repository show-manifests --name $acr_registry_name --repository $repository_name --orderby time_asc --query "[?timestamp < '$retention_start_date'].digest" -o tsv | xargs -I% az acr repository delete --name $acr_registry_name --image $repository_name@% --yes
    echo "Deleted old images successfully from $repository_name"
done