install-uv:
	pip install uv

install-deps:
	uv pip install -r requirement.txt
image:
	IMAGE_NAME=w-bridge TAG=ot REGISTRY=registry2.siavashmohammady.ir ./docker_build_tag_push.sh