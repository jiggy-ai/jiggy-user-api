
.PHONY: help build push all

help:
	    @echo "Makefile commands:"
	    @echo "build"
	    @echo "push"
	    @echo "all"

.DEFAULT_GOAL := all

build:
	    docker build -t wskish/jiggy-user-api:${TAG} .

push:
	    docker push wskish/jiggy-user-api:${TAG}

all: build push
