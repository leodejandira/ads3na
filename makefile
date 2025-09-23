APP_NAME=minha-api
PORT=8000

# Pipeline para homologação
# 1: Instalar as dependenvias como o comando `install-dep` 
# 2: Rodar a pipeline via comando `make pr-pipeline`



check-docker:
	@docker info > /dev/null 2>&1 || (echo "Docker não está rodando. Iniciando o Docker..."; open -a Docker && sleep 5 && docker info > /dev/null 2>&1 || (echo "Falha ao iniciar o Docker. Por favor, inicie o Docker manualmente." && exit 1))

docker-build: check-docker
	docker build -t $(APP_NAME) .


docker-stop:
	@echo "Parando e removendo container '$(APP_NAME)' se existir..."
	-@docker stop $(APP_NAME) 2>/dev/null || true
	-@docker rm $(APP_NAME) 2>/dev/null || true


docker-run: docker-stop
	docker run -d -p $(PORT):8000 --name $(APP_NAME) $(APP_NAME)



format:
	black .
	isort .

lint:
	flake8 .


test:
	coverage run -m pytest -v tests || true
	coverage report --show-missing --omit="tests/*"


radon:
	radon mi *
	radon cc *


bandit:
	@bandit -r . || (echo "Falha na análise de segurança com Bandit. Corrija os problemas de segurança antes de continuar."; exit 1)


install-dep:
	pip install -r requirements-esteira.txt



clean:
	rm -rf .tox .coverage .mypy_cache .pytest_cache build dist *.egg-info


pr-pipeline: lint format bandit radon docker-build docker-run
	@echo "Pipeline concluída com sucesso! Pronto para homologação."