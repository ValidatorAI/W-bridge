install-uv:
	pip install uv

install-deps:
	uv pip install -r requirement.txt

image:
	IMAGE_NAME=w-bridge TAG=ot REGISTRY=registry2.siavashmohammady.ir ./docker_build_tag_push.sh

migrate:
	python3 -m alembic upgrade head

# `env -u PYTHONPATH`: this repo's top-level dirs (agent/, bus/, db/, space/) are
# namespace packages, so a PYTHONPATH that carries another `agent` package (e.g. a
# Hermes install) would shadow them.
test:
	env -u PYTHONPATH ./bridge/bin/python -m pytest -q