#! /bin/bash
# Run docker image
# Allows passing optional param to override default command (nginx -g)
# https://github.com/nginxinc/docker-nginx/blob/master/stable/alpine-perl/Dockerfile#L120
. env.sh
docker run -ti --rm --name "$CONTAINER_NAME" "$DOCKER_USER/$DOCKER_NAME:latest" "$1"
