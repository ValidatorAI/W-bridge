#!/usr/bin/env bash
set -euo pipefail

# Config (override with env vars if needed)
IMAGE_NAME="${IMAGE_NAME:-w-bridge}"
TAG="${TAG:-ot}"
REGISTRY="${REGISTRY:-registry2.siavashmohammady.ir}"

LOCAL_IMAGE="${IMAGE_NAME}:${TAG}"
REMOTE_IMAGE="${REGISTRY}/${IMAGE_NAME}:${TAG}"

echo "Building ${LOCAL_IMAGE} ..."
docker build -t "${LOCAL_IMAGE}" .

echo "Tagging ${LOCAL_IMAGE} as ${REMOTE_IMAGE} ..."
docker tag "${LOCAL_IMAGE}" "${REMOTE_IMAGE}"

echo "Pushing ${REMOTE_IMAGE} ..."
docker push "${REMOTE_IMAGE}"

echo "Done: ${REMOTE_IMAGE}"
