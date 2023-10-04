import json
import os
import re

PUBLIC_IMAGE_PREFIX = "public/azureml/"

# Example: openmpi3.1.2-cuda10.0-cudnn7-ubuntu18.04:20220113.v1
IMAGE_NAME_RE = re.compile(r"^(.+):((\d{8}\.v)(\d+))$")

# Global var for convenience
release_configs = []


def get_config_if_exists(image_name):
    for config in release_configs:
        if config["image_name"] == image_name:
            return config
    return None


def update_release_config(image_name, tag, path):
    config = get_config_if_exists(image_name)
    if config is None:
        print("Config not found. tags = {}".format(tag))
        release_configs.append({
            "image_name": image_name,
            "is_public": True if "public" in path else False,
            "tags": [tag] if tag is not None else [],
            "image_path": path
        })
    elif tag and tag not in config["tags"]:
        # If tag is already in the list don't duplicate
        print("Config found. tags = {}".format(tag))
        config["tags"].append(tag)


# If a image_name is specified, it will only parse tags for that image name
# If not, it will parse all the images in the file
def parse_tag_file(file_name, image_name=""):
    # Tags file will be in the format image_name:tag image_name:another_tag
    # The folder structure is image_name/tag
    # Parse the tags file and add to configs. The tag file can have more than one image
    with open(file_name) as file:
        all_tags = file.read().splitlines()
        for tags in all_tags:
            tag_mapping = tags.split(" ")
            source_tag = tag_mapping[0]
            target_tag = tag_mapping[1]
            # Tag should be of format image_name:tag
            if (len(source_tag.split(":")) != 2) or (len(source_tag.split(":")) != 2):
                print("Incorrect tag format specified in {}.".format(file_name))
                exit(1)
            if image_name == "" or image_name == source_tag:
                tags_parent_dir = os.path.dirname(file_name)
                dockerfile_parent_folder = source_tag.split(":")[1]
                image_path = os.path.join(tags_parent_dir, dockerfile_parent_folder)
                update_release_config(source_tag, target_tag, image_path)


def create_release_config_file(modified_files, release_config_file_path, build_number):
    if len(modified_files) < 1:
        print("No files were modified. No tests will be run.")
        exit(0)

    for file in modified_files:
        if file.endswith("tags"):
            # Tags file was edited
            parse_tag_file(file)
        else:
            # A docker file was edited
            # Add that docker file to config
            # A docker file path is similar to docker/public(private)/image_name/tag_name
            file_name_parts = file.split("/")
            image_name_with_tag = ""
            if "private" in file:
                image_name_with_tag = "{}:{}".format(
                    file_name_parts[len(file_name_parts) - 2],
                    file_name_parts[len(file_name_parts) - 1]
                )
            else:
                image_name_with_tag = "{}:{}".format(
                    file_name_parts[len(file_name_parts) - 1],
                    build_number
                )
            update_release_config(image_name_with_tag, None, file)

            # If there is a tag file, all tags corresponding this edited docker file should be updated
            # Tag files will be at the parent folder level
            # If there is no tag file, there should still be an entry in release_configs
            parent_dir = os.path.dirname(file)
            tag_file_path = os.path.join(parent_dir, "tags")
            if os.path.isfile(tag_file_path):
                parse_tag_file(tag_file_path, image_name=image_name_with_tag)

    with open(release_config_file_path, 'w') as f:
        json.dump(release_configs, f)
    print("Created release manifest file")
    print(json.dumps(release_configs, indent=2))


def print_dockers_to_build(release_config_file_path):
    with open(release_config_file_path, 'r') as f:
        release_configs = json.load(f)
        for config in release_configs:
            print(config["image_path"])


# print all tag information in the format source_tag target_tag
def print_image_release_information(release_config_file_path):
    with open(release_config_file_path, 'r') as f:
        release_configs = json.load(f)
        for config in release_configs:
            # Create a tag entry for the image name itself
            # The image in staging ACR will be tagged with build number information
            # Add a docker tag
            # from staging_acr/image_name_with_build_number to target_acr/image_name_without_build_number
            print("{},{},{}".format(config["is_public"], config["image_name"], config["image_name"]))
            for tag in config["tags"]:
                print("{},{},{}".format(config["is_public"], config["image_name"], tag))


# Transform a release config into an import config
def create_import_config(release_config_file_path, import_config_file_path,
                         registry_address, registry_username=None, registry_password=None,
                         release_num=None, release_tag=None):
    images = []

    # Create in memory from contents of release config
    with open(release_config_file_path, 'r') as f:
        release_configs = json.load(f)
        for config in release_configs:
            # Skip private ones
            if not config['is_public']:
                continue

            # Get image name
            image_name_with_tag = config['image_name']

            # Extract name and tag from image name
            match = IMAGE_NAME_RE.match(image_name_with_tag)
            if not match:
                raise Exception(f"Failed to parse image name {image_name_with_tag}")
            image_name = match.group(1)
            if release_tag:
                # Use specified release tag
                image_tag = release_tag
            elif release_num:
                # Use just the release number
                image_tag = match.group(3) + release_num
            else:
                # Carry over the existing tag
                image_tag = match.group(2)

            # Generate target image names
            destination_images = [f"{PUBLIC_IMAGE_PREFIX}{image_name}:{tag}" for tag in [image_tag, "latest"]]

            # Store image info
            source = {
                'imageName': f"{registry_address}/{image_name_with_tag}",
            }
            if registry_username is not None and registry_password is not None:
                source['registryUsername'] = registry_username
                source['registryPassword'] = registry_password
            images.append({
                'source': source,
                'destination': {
                    'imageNames': destination_images
                }
            })

    # Create on disk
    import_config = {'images': images}
    with open(import_config_file_path, 'w') as f:
        json.dump(import_config, f, indent=2)
    print("Created import manifest file")
