import os
import argparse
import glob

from git import Repo
from pprint import pprint
from config_utils import create_release_config_file


_DOCKER_IMAGES_FOLDER = "base_images/docker/public"

# Commented building private images task because we are not supporting.
# Verify a edited tags file.
# Two images can't be tagged with the same name
# A tag file is of format image_name_with_tag image_name_with_different_tag
# This will check if the edited tag file has distinct image_name_with_different_tag


def verify_tags(tag_file_path):
    # The file should exist as the file name was determined by git diff
    if not os.path.isfile(tag_file_path):
        print("Tag file {} doesn't exist.".format(tag_file_path))
        exit(0)

    with open(tag_file_path) as f:
        tags = f.read().splitlines()

    distinct_tags = set([tag.split(" ")[1] for tag in tags])
    if len(distinct_tags) != len(tags):
        print("Tags file {} has duplicate tags.".format(tag_file_path))
        exit(0)


# Find Modified files
def find_modified_files(repo, source_branch, compare_target):
    print('Getting common ancestor of', source_branch, 'and', compare_target)
    common_ancestor = str(repo.merge_base(source_branch, compare_target)[0])
    print('Finding modified docker using diff between', common_ancestor, 'and', source_branch)
    response = repo.git.diff('--name-status', common_ancestor, source_branch)
    print('\nResponse to git diff:\n' + response)

    modified_files = []
    deleted_files = []

    for line in response.splitlines():
        # Each diff is listed as [M	base_images/docker/public/base/intelmpi2018.3-ubuntu16.04/Dockerfile]
        # diff[0] will refer to the edit action
        # diff[1] will be the complete path to the edited file
        diff = line.split()

        # Rename is a special case which needs to be handled a little bit differently
        # [R081 base_images/.../image_1/Dockerfile R081 base_images/.../image_2/Dockerfilee]
        if diff[0].startswith('R'):
            diff[1] = diff[2]

        diff_parent_dir = os.path.dirname(diff[1])

        # For parent folders which contain Dockerfile should trigger build and test
        if diff_parent_dir.startswith(_DOCKER_IMAGES_FOLDER):
            # Check if edited file folder contains Dockerfile.
            if os.path.isfile("{}/Dockerfile".format(diff_parent_dir)):
                print("Appending to list of edited files = {}".format(diff))
                # For each edit to a docker folder, have only one entry
                # If both tests.json and the docker file were edited, run the test only once for both these changes.
                docker_parent_folder = diff[1].rsplit('/', 1)[0]
                if diff[0] == 'D' and "Dockerfile" in diff[1]:
                    # Check delete only for the docker file itself.
                    # If other entities in the folder got deleted, still requires the build
                    deleted_files.append(docker_parent_folder)
                elif docker_parent_folder not in modified_files:
                    # Modifying any item in a docker folder should trigger image build and test for that image
                    modified_files.append(docker_parent_folder)
            # If a tag file is edited, add that information to list of edited files
            if diff[1].endswith("tags"):
                # If a tag file is deleted, don't act on that
                if diff[0] != 'D':
                    verify_tags(diff[1])
                    modified_files.append(diff[1])

    # Exclude the dockers which has dockerfile deleted
    modified_files = [docker for docker in modified_files if docker not in deleted_files]
    return modified_files


# Find docker files in given path
def find_files(parent_dir):
    print('Finding all docker files in ', parent_dir)

    # Glob finds all files recursively
    # https://docs.python.org/3/library/glob.html
    docker_files = glob.glob("{}/**/Dockerfile".format(parent_dir), recursive=True)
    print("\n Identified docker files in given path")
    print(docker_files)
    return [os.path.dirname(file) for file in docker_files]


# main: where all the magic happens
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Discover the dockers that have been modified',
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--source_branch_commit', help='Source branch')
    parser.add_argument('--master_branch_commit', help='Master branch')
    parser.add_argument('--docker_files_path', help='Identify all docker files in this path. '
                                                    'Specify multiple paths separated with ;')
    parser.add_argument('--release_config_file_path', help='File path to release config file.')
    parser.add_argument('--build_number', help='The build number assigned to the build by VSTS.')
    args = parser.parse_args()

    dockers = []

    # Check for git diff first
    repo = Repo(os.getcwd())
    dockers = find_modified_files(repo, args.source_branch_commit, args.master_branch_commit)
    print("docker files input = {}".format(args.docker_files_path))
    # if docker_files_path is specified and git diff didn't find any changes, trigger manual build
    if args.docker_files_path and len(dockers) == 0:
        all_docker_files_path = args.docker_files_path.split(",")
        for docker_files_path in all_docker_files_path:
            if not os.path.isdir(docker_files_path) and not os.path.exists(docker_files_path):
                print("Input path specified {} doesn't exist.".format(docker_files_path))
                exit(1)
            if docker_files_path.endswith("Dockerfile"):
                print("A dockerfile was specified in list of paths. Using the parent directory of this file.")
                dockers.append(os.path.dirname(docker_files_path))
            else:
                print("Getting docker files in {}".format(docker_files_path))
                dockers.extend(find_files(docker_files_path))

    if not len(dockers):
        print("No docker files were identified for build.")
        exit(1)

    print('\n Dockers:')
    pprint(dockers)

    create_release_config_file(dockers, args.release_config_file_path, args.build_number)
    exit(0)
