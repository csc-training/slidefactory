IMAGE_ROOT?=ghcr.io/csc-training
IMAGE=slidefactory
IMAGE_TAG?=$(shell git rev-parse --abbrev-ref HEAD | tr '/' '-')
BUILD_VERSION?=$(shell git describe --tags --always --dirty | sed 's/^v//')
CONTAINER_CMD=$(shell command -v podman >/dev/null 2>&1 && echo podman || echo docker)

build: Dockerfile slidefactory.py
	${CONTAINER_CMD} build \
		--platform "linux/amd64,linux/arm64" \
		--label "org.opencontainers.image.source=https://github.com/csc-training/slidefactory" \
		--label "org.opencontainers.image.description=slidefactory" \
		--build-arg VERSION=${BUILD_VERSION} \
		-t ${IMAGE_ROOT}/${IMAGE}:${IMAGE_TAG} \
		.

push:
	${CONTAINER_CMD} push ${IMAGE_ROOT}/${IMAGE}:${IMAGE_TAG}

singularity:
	rm -f $(IMAGE).sif $(IMAGE).tar
	${CONTAINER_CMD} save $(IMAGE_ROOT)/$(IMAGE):$(IMAGE_TAG) -o $(IMAGE).tar
	singularity build $(IMAGE).sif docker-archive://$(IMAGE).tar
	rm -f $(IMAGE).tar

clean:
	rm -f $(IMAGE).sif $(IMAGE).tar
