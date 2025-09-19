# APP_NAME=minha-api
# PORT=8000

# docker-build:
# 	docker build -t $(APP_NAME) .

# docker-stop:
# 	-@docker ps -q --filter "publish=$(PORT)" | xargs -r docker stop
# 	-@docker ps -aq --filter "publish=$(PORT)" | xargs -r docker rm

# docker-run: docker-stop
# 	docker run -d -p $(PORT):8000 --name $(APP_NAME) $(APP_NAME)

APP_NAME=minha-api
PORT=8000

docker-build:
	docker build -t $(APP_NAME) .

docker-stop:
# 	-@powershell -Command "$ids = docker ps -q --filter 'publish=$(PORT)'; if ($ids) { $ids | ForEach-Object { docker stop $_ } }"
# 	-@powershell -Command "$ids = docker ps -aq --filter 'publish=$(PORT)'; if ($ids) { $ids | ForEach-Object { docker rm $_ } }"
	docker stop $(docker ps -q)


docker-run: docker-stop
	docker run -d -p $(PORT):8000 --name $(APP_NAME) $(APP_NAME)

