This is a readme to help you understand how Azure ML training images are maintained in this repository.

## Table of Contents
* Folder structure
* Image tagging
* Build pipeline
* Release pipeline
* Modify existing image
* Add a new image
* Open source
* How to patch Windows base Docker image

## Folder structure
```
base_images/
    devREADME.md              [you are here]
    docker/                   [All Docker files are committed here]
       public/                [All Docker files that are open sourced]
           base/              [CPU images]
           base-gpu/          [GPU images]
    scripts/                  [vsts build related scripts]
    tests/                    [Integration tests setup for the Docker images]
```

## Public/Base Images
Base images for both CPU and GPU are open sourced in [Azure ML containers](https://github.com/Azure/AzureML-Containers) repository. The base folder has all CPU images. The base-gpu folder has all GPU images. CPU images are built on top of `ubuntu:16.04` images. GPU images are built on top of nvidia images for a given cuda version. Azure ML training supports both Intel MPI and Open MPI.

Inside these folders, each image has a dedicated folder. For example, let's look at CPU image for Intel MPI - `public/base/intelmpi2018.3-ubuntu16.04`.
* `Dockerfile` - This is the major portion of the Docker image. These are the contents of the DockerFile that are open sourced.
* `Dockerfile.private` - Not all content of a dockerfile needs to be open sourced. For example, the part where we copy ThirdPartyNotices(TPN) and license file is not information that needs to be open sourced. Such contents of the Docker image are added in `Dockerfile.private`. This separation is only for what information is open sourced. When we build a Docker image the contents of `Dockerfile` and `Dockerfile.private` are combined.
* `LICENSE.txt` - This is the license file for the Docker image. Reach out to legal team if you have any questions on these contents.
* `tests.json` - This file contains the combinations that are tested for this particular image. The most common training combinations to test are single node training and distributed training. In this json, you can also see the training script that has the python script to run the training.
* `ThirdPartyNotices.txt` - For every component installed in the image, TPN content should be added. The content is given by legal team.

## Image tagging
We follow stable tagging for the Azure ML training images.

### Naming convention
All contents related to an image are placed in a dedicated folder. Make sure the folder names are meaningful and convey basic information about the image. For example, `intelmpi2018.3-ubuntu16.04` conveys that this images has Intel MPI version 2018.3 and Ubuntu 16.04. In case of framework images, the folder name is generally the version and CPU/GPU information.

### Compatibility
The OS image for Windows Server 2019 only supports Windows containers based on Windows Server 2019. Only process isolation is enabled, not Hyper-V. All the information on windows container compatibility can be found [here](https://docs.microsoft.com/en-us/virtualization/windowscontainers/deploy-containers/version-compatibility?tabs=windows-server-2019%2Cwindows-10-2004).

## Build pipeline
All images in this folder are tested using the [AzureML-Images-CI pipeline](https://msdata.visualstudio.com/Vienna/_build?definitionId=5596). You can edit this pipeline to look at all the steps involved in testing the images.

Images modified are built and pushed to a staging ACR and then tested against the most recent version of azureml-sdk. If all tests succeeded, the image is ready to be released.

More information about variables and major steps in the pipeline is provided below.

### Queue time variables
A few variables are configurable at queue time to affect how the pipeline runs:
* `release_num` - The release number that will be used in MCR image tags, which follow the format `YYYYMMDD.v#`, where `YYYYMMDD` is derived from the current date and `#` is the release number. Defaults to 1, but can be incremented if multple versions of an image are promoted to MCR in one day. Cannot be used with `release_tag`.
* `release_tag` - The full tag that will be used for images. Similar to `release_num`, but sets the full tag. This is useful if you ever need to set a tag based on a date other than today. Cannot be used with `release_num`.
* `docker_files_path` - The folder containing Docker files of the images to be built. Defaults to `base_images/docker/public`.

### Discover new/updated images
This step compares your PR with the master branch to identify which images are new or updated. A change to any file inside the folder that has a Dockerfile will be considered a change to the image itself. For example, editting `LICENSE.txt` will consider that Docker image as having been modified by your PR. If no files were identified by this process, then all the images in the path defined by the build env variable `docker_files_path` will be considered as modified images. For more details look at `base_images/scripts/vsts_build_scripts/discover_modified_dockers.py`

A `release.json` file is created in build artifacts. This file will have all the necessary information required by the release pipeline.

### Build images
All new/updated Docker images will be built in this step. These images are tagged with the build number so that the images from each build have unique names in the ACR. For more information, review `base_images/scripts/vsts_build_scripts/docker_operations.sh`, specifically the build condition's code block.

### ACR login
This step logs into the staging ACR.

### Push images
The images are pushed to the staging ACR. Take a look at `base_images/scripts/vsts_build_scripts/docker_operations.sh`, specifically the push condition's code block. The build number is appended to image names to identify which build an image belongs to. An example of an image in the staging ACR will be `base:intelmpi2018.3-ubuntu16.04--buildNumber`.

### Test images
The images pushed to the staging ACR are tested. This is an integration test for these image against the latest azureml-sdk package. Currently all the tests are submitted as estimator/training runs. Take a look at `base_images/scripts/vsts_build_scripts/docker_operations.sh`, specifically the test condition's code block. This code block invokes `pytest` for `base_images/tests/estimators/test_aml_images.py` for each image. If you require a different scenario you'll need to create new tests in `base_images/tests` and update the test clode block.

The combinations to test are determined from the `tests.json` file associated with an image. If an image folder has no `tests.json` file then no integration tests will be performed against that image. However it's generally is not a good practice to add an image without tests.

These tests are all run in the same workspace: `/subscriptions/13e50845-67bc-4ac5-94db-48d493a6d9e8/resourceGroups/aml_images_eastus/providers/Microsoft.MachineLearningServices/workspaces/ci_cd_04_08_2019`. An experiment is created with a name based on the current date, which makes it easier to keep track of experiments. If needed, you can check this workspace for the runs created from this pipeline.

### Delete from temp ACR
If one of the previous steps failed, the image can't be released. Since the pipeline doesn't support partial releases, all images created during the pipeline run are deleted from the staging ACR. If you look at the control options section, you'll see that this step only runs if a previous step has failed.

### Cancel all runs
Integration tests submit a lot of runs to Azure ML. If one of the runs fails there's no point in waiting on any of the other ones. This step will cancel all runs submitted to Azure ML during the pipeline run. This step also runs only if any of the previous steps failed. There is a `/tmp/run_information.txt` artifact that keeps track of all the runs submitted by the pipeline run and is used to identify all the runs to be deleted. Creation of this file can be seen in `base_images/tests/estimators/test_aml_images.py`.

### Publish Artifact
These steps publish various artifacts produced during the pipeline run.
* release_config is the `release.json` file
* base_images is the full `base_images` folder

### Create import config
Creates an `import.cfg` file that contains references to the images in the staging ACR and their MCR repo names and tags.

### Create drop
Creates a drop that will be used by Ev2 in the release pipeline.

## Release pipeline
[AzureML-Images-CD](https://msdata.visualstudio.com/Vienna/_release?definitionId=1440) is the release pipeline, which imports images from the staging ACR into a secure production ACR. A webhook on this ACR notifies MCR for each image import, and then MCR promotes the images, making them available to use in Azure ML SDK.

The release pipeline depends on the `import.cfg` file created by the build pipeline, and will have an entry for each image to be pushed to MCR. This is an example entry from the file:

```json
{
   "source": {
      "imageName": "base2reg.azurecr.io/test1:20220302.v6",
      "registryUsername": "<sp_client_id>",
      "registryPassword": "<sp_secret>"
   },
   "destination": {
      "imageNames": [
         "public/azureml/test1:20220302.v1",
         "public/azureml/test1:latest"
      ]
   }
}
```

* `imageName` - The reference to the image in the staging ACR
* `registryUsername` - The client ID of a service principal with read-only access to the staging ACR
* `registryPassword` - The secret associated with the service principal
* `imageNames` - The list of image names used during the import into the secure production ACR. These may be different than the one listed in `imageName`

## Modify existing image
If you are modifying an existing image, once you submit the PR, the build pipeline will be automatically kicked off. If the build pipeline succeeds, you can start a release pipeline and have your images in the final ACR. If the build pipeline fails, try looking at the build pipeline logs for more information. You can also go the workspace portal and look for information there.

While modifying if you are installing new packages, make sure that packages are mentioned in the `ThirdPartyNotices.txt`. Similarly if you are removing, make sure TPN is up to date with your changes. If your changes are starting to support a new training scenario, make sure you are updating tests.json to reflect the same. If your changes are starting to support a entirely new scenario that is not based on training runs, take the time to create tests for the new scenario and update docker_operations.sh to make sure it is tested.

If you are modifying an image in public folder, make sure to update the Dockerfiles and Readme in the [AzureML-Containers](https://github.com/Azure/AzureML-Containers) repository. There are also package information in estimator doc string in azureml-train-core packages. Make sure to update those doc strings to reflect your changes.

If you are modifying one of the base images, then make sure to build and push framework images after your changes. The framework images are built on top of base images. Any change in base image should be reflected in framework images. The steps to do this are
* Create your PR for base images, merge the PR.
* Create a release pipeline for that PR and make sure the base images are updated in final ACR.
* Create a manual build for framework images. For manual build, since there is no PR the build env variable docker_files_path will be used to determine what files are tested. You can specify multiple paths separated by ; here.
* Once the manual build succeeds, create a release pipeline from here.

## Add a new image
If you are adding a new image, make sure your image confirms to the folder structure. Make sure there is a parent folder and image folder that will give enough information as image name and image tags. See the Tagging section in this readme to understand why this convention is important.

Within the image folder, make sure to add tests.json file. This will the list of combinations you want to test on your image. The existing pipeline only supports tests on Azure ML training runs. If you are adding an image for something like AutoML or inference, this pipeline will need some modifications. Create tests for your scenario and modify build pipeline to adapt to that change.

If you are adding an image in public folder, make sure to update the Dockerfiles and Readme in the [AzureML-Containers](https://github.com/Azure/AzureML-Containers) repository. If you want to update Azure ML training documentation to give information about your image, do that change too.

Make sure to add LICENSE and TPN files. You have to reach out ot legal team for contents of these files.

## Open source
All images in public folder are open sourced in [AzureML-Containers](https://github.com/Azure/AzureML-Containers) repository. Any change to the public folder, please send a PR to this GitHub repository after you have merged your changes to master branch.

In addition to this GitHub repository, we have also listed our images in DockerHub. This is done via MCR syndication. All images in MCR can be added to DockerHub. For more information, refer to:
* [MCR team's readme](https://msazure.visualstudio.com/MicrosoftContainerRegistry/_wiki/wikis/Microsoft%20Container%20Registry?wikiVersion=GBmaster&pagePath=%2FSections%2FSyndication&pageId=8705)
* [GitHub repo]( https://github.com/Microsoft/mcr/tree/master/teams) for Syndication yml files.
* [GitHub repo](https://github.com/Microsoft/mcrdocs/tree/master/teams) for syndication readme. This will the readme content for Azure ML images listed in DockerHub.


## How to patch windows Docker image
All Windows Docker images need to be rebuilt from the windows base Docker image and released monthly. The release date should be on the second Wednesday of each month. With this release schedule, the Windows Docker images can get the latest updates. For more details on how to update Windows containers, please refer to [How to update Windows containers](https://docs.microsoft.com/en-us/virtualization/windowscontainers/deploy-containers/update-containers)

## Useful links

1. [Image publishing process](https://msdata.visualstudio.com/Vienna/_git/vienna-wiki?path=%2FCommon%2FImagePublishingProcess.md&version=GBmaster)
