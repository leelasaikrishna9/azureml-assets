import argparse
import os
from config_utils import print_dockers_to_build, print_image_release_information, create_import_config

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="operation")

    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("--release-config", help="Path to release config file", required=True)

    subparsers.add_parser("image-paths", parents=[parent_parser])
    subparsers.add_parser("release-info", parents=[parent_parser])

    parser_create_import_config = subparsers.add_parser("create-import-config", parents=[parent_parser])
    parser_create_import_config.add_argument("--import-config", help="Path to import config file", required=True)
    parser_create_import_config.add_argument("--release-num", help="Release number to use in import config image tags",
                                             nargs="?", const="")
    parser_create_import_config.add_argument("--release-tag", help="Tag to use for all images in import config",
                                             nargs="?", const="")
    parser_create_import_config.add_argument("--registry-address", help="Address of registry login server",
                                             required=True)
    parser_create_import_config.add_argument("--registry-username", help="Registry username")
    parser_create_import_config.add_argument("--registry-password", help="Registry password")

    args = parser.parse_args()

    if not os.path.isfile(args.release_config):
        raise Exception("Config file path is required to get list of dockers to build")

    if args.operation == "image-paths":
        # This will return list of folder names that contains Dockerfile to be built.
        print_dockers_to_build(args.release_config)
    elif args.operation == "release-info":
        print_image_release_information(args.release_config)
    elif args.operation == "create-import-config":
        # Ensure both username and password are specified, or neither
        if (args.registry_username is not None) ^ (args.registry_password is not None):
            parser.error("--registry-username or --registry-password can't be used alone.")

        # Ensure only one of release num and tag is used
        if args.release_num and args.release_tag:
            parser.error("--release-num and --release-tag can't be used together.")

        create_import_config(
            args.release_config,
            args.import_config,
            args.registry_address,
            args.registry_username,
            args.registry_password,
            args.release_num,
            args.release_tag)
