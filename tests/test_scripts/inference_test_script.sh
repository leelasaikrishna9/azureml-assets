image_name=${1}
inf_image_name="${image_name}-inference"
junitxml_path=out/TEST-$image_name-results.xml

# get absolute path to this script
# reference: https://stackoverflow.com/questions/4774054/reliable-way-for-a-bash-script-to-get-the-full-path-to-itself
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd $SCRIPT_DIR/../inference

echo "Building inference image for ${1}"

docker build \
    --build-arg BASE_IMAGE=$image_name \
    -t $inf_image_name \
    .

echo "Built inference image $inf_image_name"

echo "Running the tests for the inference image ${inf_image_name}"
pytest ./test_training_images.py --base_image_name $inf_image_name

echo "Tests Completed"

echo "Removing the inference image"

docker rmi $inf_image_name