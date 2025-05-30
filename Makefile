IMAGE_ROOT?=ghcr.io/csc-training
IMAGE=slidefactory
IMAGE_VERSION?=$(shell grep -m1 -oP '(?<=VERSION = ").+(?=")' slidefactory.py)


build: Dockerfile slidefactory.py
	docker build \
		--label "org.opencontainers.image.source=https://github.com/csc-training/slidefactory" \
		--label "org.opencontainers.image.description=slidefactory" \
		--build-arg VERSION=${IMAGE_VERSION} \
		-t ${IMAGE_ROOT}/${IMAGE}:${IMAGE_VERSION} \
		.

push:
	docker push ${IMAGE_ROOT}/${IMAGE}:${IMAGE_VERSION}

singularity:
	rm -f $(IMAGE).sif $(IMAGE).tar
	docker save $(IMAGE_ROOT)/$(IMAGE):$(IMAGE_VERSION) -o $(IMAGE).tar
	singularity build $(IMAGE).sif docker-archive://$(IMAGE).tar
	rm -f $(IMAGE).tar

clean:
	rm -f $(IMAGE).sif $(IMAGE).tar
