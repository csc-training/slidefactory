SIF=slidefactory.sif
IMAGE=slidefactory
TAG=0.2.0


build: Dockerfile convert.py
	podman build --format docker \
		-t ${IMAGE_ROOT}/${IMAGE}:${TAG} \
		.

push:
	podman push ${IMAGE_ROOT}/${IMAGE}:${TAG}

singularity:
	rm -f $(SIF) $(SIF:.sif=.tar)
	podman save ${IMAGE_ROOT}/${IMAGE}:${TAG} -o $(SIF:.sif=.tar)
	singularity build $(SIF) docker-archive://$(SIF:.sif=.tar)
	rm -f $(SIF:.sif=.tar)

clean:
	rm $(SIF)
