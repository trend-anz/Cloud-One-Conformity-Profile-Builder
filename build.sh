# Helper to build docker images
# Expects env.sh file with
# eg:
# DOCKER_USER=myuser
# DOCKER_NAME=cc_dev
# CONTAINER_NAME=${DOCKER_NAME}_cont
. env.sh

IMAGE_NAME="$DOCKER_USER/$DOCKER_NAME"
echo "Building $IMAGE_NAME"
# Toggle to force clean build
docker build -t ${IMAGE_NAME} .
# docker build -t ${IMAGE_NAME} . --no-cache
