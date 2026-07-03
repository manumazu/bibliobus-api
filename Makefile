export UID:=$(shell id -u)
export GID:=$(shell id -u)

build:
	docker build -t bibliobus-api --build-arg=uid=$(UID) .
up:
	docker run  --name bibliobus-api --env-file .env --rm -it --user $(UID):$(GID) -p 80:8000 -w /app -v `pwd`:/app bibliobus-api
restart:
	make stop && make up
down:
	docker stop bibliobus-api
logs:
	docker logs -f bibliobus-api