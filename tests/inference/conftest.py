def pytest_addoption(parser):
    parser.addoption("--base_image_name", help="Base image name")


def pytest_generate_tests(metafunc):
    try:
        # Image details
        base_image_name = metafunc.config.getoption('--base_image_name')

        metafunc.parametrize("base_image_name", [base_image_name])

    except Exception as e:
        raise Exception("Exception occurred: {}".format(e))
