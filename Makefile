IMAGE_ROOT?=ghcr.io/csc-training
IMAGE=slidefactory
IMAGE_VERSION=$(shell grep -m1 'VERSION = "' slidefactory.py | sed -E 's/.*VERSION = "(.*)".*/\1/')
CONTAINER_CMD=$(shell command -v podman >/dev/null 2>&1 && echo podman || echo docker)

build: Dockerfile slidefactory.py
	${CONTAINER_CMD} build \
		--platform "linux/amd64,linux/arm64" \
		--label "org.opencontainers.image.source=https://github.com/csc-training/slidefactory" \
		--label "org.opencontainers.image.description=slidefactory" \
		--build-arg VERSION=${IMAGE_VERSION} \
		-t ${IMAGE_ROOT}/${IMAGE}:${IMAGE_VERSION} \
		.

push:
	${CONTAINER_CMD} push ${IMAGE_ROOT}/${IMAGE}:${IMAGE_VERSION}

singularity:
	rm -f $(IMAGE).sif $(IMAGE).tar
	${CONTAINER_CMD} save $(IMAGE_ROOT)/$(IMAGE):$(IMAGE_VERSION) -o $(IMAGE).tar
	singularity build $(IMAGE).sif docker-archive://$(IMAGE).tar
	rm -f $(IMAGE).tar

clean:
	rm -f $(IMAGE).sif $(IMAGE).tar
