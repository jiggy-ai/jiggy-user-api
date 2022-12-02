
.PHONY: help build push all

help:
	    @echo "Makefile commands:"
	    @echo "build"
	    @echo "push"
	    @echo "all"

.DEFAULT_GOAL := all

build:
	    docker build -t jiggyai/jiggy-user-api:${TAG} .

push:
	    docker push jiggyai/jiggy-user-api:${TAG}

all: build push
