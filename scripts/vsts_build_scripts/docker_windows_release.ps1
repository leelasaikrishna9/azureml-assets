param(
  [string]$operation,
  [string]$staging_acr_url,
  [string]$build_number,
  [string]$release_config_file_path,
  [string]$staging_acr_name,
  [string]$staging_acr_pwd,
  [string]$aad_sp_password,
  [string]$system_working_directory,
  [string]$release_num,
  [string]$framework_acr_user_name,
  [string]$framework_acr_user_pwd,
  [string]$framework_images_acr="viennaprivate.azurecr.io",
  [string]$staging_acr_subscription="589c7ae9-223e-45e3-a191-98433e0821a9",
  [string]$staging_acr_resourcegroup="ICE-BaseImage-Build-Resources"
)

$staging_acr_resource="/subscriptions/$staging_acr_subscription/resourceGroups/$staging_acr_resourcegroup/providers/Microsoft.ContainerRegistry/registries/$staging_acr_name"
$subprocess_ids=""

if ( -not (Test-Path -LiteralPath $release_config_file_path -PathType Leaf) )
{
    write-host "There is no config file, no need to build"
    exit 0
}

az account set -s $staging_acr_subscription
az acr login --name $staging_acr_name

$get_edited_folder_cmd="python base_images/scripts/vsts_build_scripts/config_operations.py image-paths --release-config $release_config_file_path"
$edited_foldernames=Invoke-Expression $get_edited_folder_cmd
write-host "List of modified edited_foldernames = $edited_foldernames"

$tagging_information=""
if ($operation -eq "release" )
{
    $get_tag_cmd="python base_images/scripts/vsts_build_scripts/config_operations.py release-info --release-config $release_config_file_path"
    $tagging_information=Invoke-Expression $get_tag_cmd
    write-host "Tagging information = $tagging_information"
    write-host $tagging_information.GetType()
}

New-Item -Path build_logs -ItemType Directory -Force
New-Item -Path image_details -ItemType Directory -Force

foreach ($folder in $edited_foldernames)
{
    Write-Host "Processing folder = $folder"
    $folder_items = $folder.Split("/")
    $image_name=$folder_items[-1]
    $image_label=$folder_items[-2]
    # If any folder with _ is built remove that from image label
    $image_label=$image_label.Replace("_", "-")
    $full_image_name=""
    if ( $folder.Contains("private") )
    {
        $full_image_name="$image_label" + ":$image_name"
    }
    else
    {
        $full_image_name="$image_name" + ":$build_number"
    }
    Write-Host "full_image_name=$full_image_name"

    $full_image_name_with_repository="$staging_acr_url/$full_image_name"
    if ($operation -eq "release" )
    {
        # Get tag information for current image
        $current_tagging_information=$tagging_information | Where-Object { $_.Contains($full_image_name) } | Select -First 1;
        # Choosing not to use az acr import as it is supported only in azure cli

        $now=(Get-Date).ToString("yyyyMMdd")
        echo "preparing release $now.v$release_num"
        foreach ($tag in $current_tagging_information)
        {
            $is_public=$tag.Split(",")[0]
            if ( $is_public -eq "True" )
            {
                Write-Host "Skip public base image release since this is only the windows docker image release"
            }
            else
            {
                if ($image_label.Contains("windowsservercore"))
                {
                    $target_tag="$image_label-$image_name" + ":$now.v$release_num"
                    Write-Host $full_image_name_with_repository
                    # Image name in framework ACR will look like viennaprivate.azurecr.io/chainer:5.1.0-cpu
                    docker pull $full_image_name_with_repository

                    $target_image_name_with_repository="$framework_images_acr/$target_tag"
                    Write-Host $target_image_name_with_repository
                    docker tag $full_image_name_with_repository $target_image_name_with_repository
                    docker push $target_image_name_with_repository
                    $latest_image_name_with_repository = "$framework_images_acr/" + "$image_label-$image_name" + ":latest"
                    Write-Host $latest_image_name_with_repository
                    docker tag $full_image_name_with_repository $latest_image_name_with_repository
                    docker push $latest_image_name_with_repository
                }
                else
                {
                    Write-Host "Skip linux docker image release since this is only the windows docker image release"
                }
            }
        }
    }
}