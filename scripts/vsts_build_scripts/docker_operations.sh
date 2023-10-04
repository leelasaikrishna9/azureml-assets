#!/bin/bash
operation=$1
staging_acr_url=$2
build_number=$3
release_config_file_path=$4
staging_acr_name=$5
staging_acr_pwd=$6
aad_sp_password=$7
system_working_directory=$8
release_num=$9
framework_acr_user_name=${10}
framework_acr_user_pwd=${11}
staging_mcr_user_name=${12}
staging_mcr_user_pwd=${13}

mcr_staging_acr_name="amlmcr"
TimeoutSec="5400"
framework_images_acr_name="viennaprivate"
framework_images_acr="viennaprivate.azurecr.io"
staging_acr_subscription="589c7ae9-223e-45e3-a191-98433e0821a9"
staging_acr_resource=/subscriptions/$staging_acr_subscription/resourceGroups/ICE-BaseImage-Build-Resources/providers/Microsoft.ContainerRegistry/registries/$staging_acr_name
subprocess_ids=""

set -e
set -x

if [ ! -f $config_file_path ]; then
    echo "There is no config file, no need to build"
    exit 0
fi

edited_foldernames=$(python base_images/scripts/vsts_build_scripts/config_operations.py image-paths --release-config $release_config_file_path)
echo "List of modified edited_foldernames = $edited_foldernames"

tagging_information=""
if [ $operation == "release" ]; then
    tagging_information=$(python base_images/scripts/vsts_build_scripts/config_operations.py release-info --release-config $release_config_file_path)
    echo "Tagging information = $tagging_information"
fi

mkdir -p build_logs
mkdir -p image_details
for folder in $edited_foldernames
do
    # The entry in file will have full path to folder. Get only the image name from the path
    # image: parent folder name, tag: leaf folder name, build number: 123456
    # The staging acr image name will be <image_flavor>:<build_number>

    image_name=$(rev<<<$folder | cut -d"/" -f 1 | rev)
    image_label=$(rev<<<$folder | cut -d"/" -f 2 | rev)
    # If any folder with _ is built remove that from image label
    image_label=${image_label#_}
    full_image_name=""
    if [[ $folder =~ "private" ]]; then
        full_image_name=$image_label:$image_name
    else
        full_image_name=$image_name:$build_number
    fi

    platform_arg=""
    if [[ $folder  == *base-windows* ]]
    then
        platform_arg="--platform windows"
    fi
    echo "platforma_arg: $platform_arg"

    full_image_name_with_repository=$staging_acr_url/$full_image_name
    build_arg=${image_label^^}"_BUILD_ARG"
    build_arg=${build_arg//-/_}
  

    echo "$operation image: $full_image_name process: $!"
    if [ $operation == "build" ]; then
            # If the folder has an private dockerfile component, append contents to Dockerfile before build
            if [ -f $folder/Dockerfile.private ]; then
                cat $folder/Dockerfile.private >> $folder/Dockerfile
            fi

            image_build_log=build_logs/BUILD-LOG--$image_label--$image_name--$build_number.txt
            # Build with the acr address
            # ACR Build for image with tag as image name, version along with repo details, whereas since we are logging image information for the customer so it contains only image name and version details.
            # Ex : $full_image_name_with_repository = base2reg.azurecr.io/openmpi3.1.2-ubuntu18.04:20220425.v1, $IMAGE_INFORMATION = openmpi3.1.2-ubuntu18.04:20220425.v1 
            az acr build --registry $staging_acr_name -t $full_image_name_with_repository $folder $platform_arg --build-arg IMAGE_NAME=$image_name --build-arg BUILD_NUMBER=$build_number --timeout $TimeoutSec > $image_build_log 2>&1 &
            echo "Contents of Dockerfile"
            cat $folder/Dockerfile
            subprocess_ids+=" $!"
    fi

    if [ $operation == "inspect" ]; then
            # Get image details
            image_details_json=image_details/IMAGE-DETAILS--$image_label--$image_name--$build_number.txt
            az acr repository show -n $staging_acr_name --image $full_image_name > $image_details_json 2>&1 &
            subprocess_ids+=" $!"
    fi

    if [ $operation == "push" ]; then
            # Push with the acr address
            docker push $full_image_name_with_repository &
            subprocess_ids+=" $!"
    fi

    if [ $operation == "inference_test" ]; then
        echo "Starting inference tests."
        /bin/bash base_images/tests/test_scripts/inference_test_script.sh $full_image_name_with_repository
        echo "Successfully completed inference tests."
    fi

    if [ $operation == "test" ]; then
            # commeting estimators testcase since they are not using latest python SDK py38 env.
            #if [[ $folder == base_images/docker/* ]]; then
                    #test_config_file=$folder/tests.json
                    #if [ -f $test_config_file ]; then
                        # The -s switch disables per-test capturing
                        # This will run three tests in parallel
                        #pytest -d --tx 3*popen//python=python3.6 -s base_images/tests/estimators/test_aml_images.py --config_file $test_config_file --base_image_name $full_image_name --base_image_address $staging_acr_url --base_image_username $staging_acr_name --base_image_password $staging_acr_pwd --aad_sp_password $aad_sp_password --junitxml=$system_working_directory/TEST--$image_name--$build_number.xml &
                        #subprocess_ids+=" $!"
                        #else
                        #echo "tests.json doesn't exist. Skipped the training tests."
                    #fi

                    #if [[ $folder == base_images/docker/public/base/* ]] || [[ $folder == base_images/docker/public/base-gpu/* ]]; then
                        #echo "Starting inference tests."
                        #pytest -d --tx 1*popen//python=python3.6 -s base_images/tests/inference/raw_http_test.py --base_image_name $full_image_name_with_repository --base_image_address $staging_acr_url --base_image_username $staging_acr_name --base_image_password $staging_acr_pwd --aad_sp_password $aad_sp_password --junitxml=$system_working_directory/TEST--$image_name-inference--$build_number.xml &
                        #subprocess_ids+=" $!"
                    #fi
            #fi     
            if [[ $folder == base_images/docker/public* ]]; then
                    test_config_file=$folder/samplehello_tests.json
                    if [ -f $test_config_file ]; then
                        # The -s switch disables per-test capturing
                        # This will run three tests in parallel
                        pytest -d --tx 3*popen//python=python3.8 -s base_images/tests/estimators/test_aml_images.py --config_file $test_config_file --base_image_name $full_image_name --base_image_address $staging_acr_url --base_image_username $staging_acr_name --base_image_password $staging_acr_pwd --aad_sp_password $aad_sp_password --junitxml=$system_working_directory/TEST--$image_name--$build_number.xml &
                        subprocess_ids+=" $!"
                        else
                           echo "sample test is not working"
                    fi
            fi
    fi

    if [ $operation == "delete" ]; then
            # Delete images from build staging ACR in case failures
             az acr repository delete --name $staging_acr_name --image $full_image_name --password $staging_acr_pwd --subscription $staging_acr_subscription --username $staging_acr_name --yes
             echo "Deleted docker $full_image_name from $staging_acr_name"
    fi

    if [ $operation == "release" ]; then
        # Get tag information for current image
        current_tagging_information=$(echo $tagging_information | tr ' ' '\n' | grep $full_image_name)
        # Choosing not to use az acr import as it is supported only in azure cli

        now=$(date +'%Y%m%d')
        echo "preparing release $now.v$release_num"
        for tag in $current_tagging_information
        do
            is_public=$(echo $tag|cut -d"," -f 1)
            if [ $is_public == "True" ]; then
                target_tag=$image_name:$now.v$release_num
                # Images in staging MCR should be prefixed with public/azureml
                # Image name in staging MCR will look like amlmcr.azurecr.io/public/azureml/intelmpi2018.3-ubuntu16.04:<build-number>
                az acr import -n $mcr_staging_acr_name --source $full_image_name -t public/azureml/$target_tag -r $staging_acr_resource --subscription $staging_acr_subscription &
                subprocess_ids+=" $!"
                az acr import -n $mcr_staging_acr_name --force --source $full_image_name -t public/azureml/$image_name:latest -r $staging_acr_resource --subscription $staging_acr_subscription &
                subprocess_ids+=" $!"
            else
                if [[ $image_label == *windowsservercore* ]]
                then
                    echo "skip windows docker image release since this is a linux docker image release pipeline"
                else
                    target_tag=$image_label:$image_name
                    # Image name in framework ACR will look like viennaprivate.azurecr.io/chainer:5.1.0-cpu
                    docker pull $full_image_name_with_repository

                    target_image_name_with_repository=$framework_images_acr/$target_tag
                    docker tag $full_image_name_with_repository $target_image_name_with_repository
                    docker push $target_image_name_with_repository &
                    subprocess_ids+=" $!"
                fi
            fi
        done
    fi
done

exit_code=0
# wait for all forked processes to finish before exiting
# wait pid will return the exit code of the pid it is waiting for
# If any subprocess fails, exit with failure
for pid in $subprocess_ids
do
    wait $pid || exit_code=1
done

exit $exit_code