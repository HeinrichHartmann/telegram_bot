REGISTRY=docker.heinrichhartmann.net:5000
IMAGEID=telegram_bot
IMAGE=${REGISTRY}/${IMAGEID}

image: dist
	docker build . --tag ${IMAGE}
	# Short name for reference
	docker tag docker.heinrichhartmann.net:5000/telegram_bot:latest ${IMAGEID}

push:
	docker push ${IMAGE}

dist:
	poetry build
