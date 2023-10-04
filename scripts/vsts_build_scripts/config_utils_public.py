import json
import os

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


def create_release_config_file(dockers, release_config_file_path, build_number):
    if len(dockers) < 1:
        print("No files were modified. No tests will be run.")
        exit(0)

    for file in dockers:
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
