.DEFAULT_GOAL := help

-include .env
export

ENV ?= dev

COMPOSE = docker compose --env-file ./.env
BACKEND = docker exec swiswim_backend
RUN = poetry run

up: ## Start services deattached
	$(COMPOSE) up -d
upb: ## Start services with build and logs 
	$(COMPOSE) up --build
upbd: ## Start service with rebuild deattached
	$(COMPOSE) up -d --build
down: ## Stop services
	$(COMPOSE) down
down_f: ## Stop services, remove volumes
	$(COMPOSE) down -v
build: ## Build services
	$(COMPOSE) build
dlog: ## Show docker compose logs
	$(COMPOSE) logs -f

shell: ## Run shell in backend container
	$(BACKEND) bash

makemigration: ## Create alembic revision (usage: make makemigration m="msg")
	$(BACKEND) alembic revision --autogenerate -m "$(m)"
migrate: ## Run alembic upgrade head
	$(BACKEND) alembic upgrade head

db: ## Run postgresql client for dev env.
	$(COMPOSE) exec db psql -U $(DB_USER) -d $(DB_NAME)
seed: ## Run seeds,
	$(BACKEND) python -m backend.seeds.run


reset-db: ## Reset all database and seed it for dev.
	@make down_f
	@make up
	sleep 2
	@make migrate
	@make seed

test: ## Run tests
	$(BACKEND) pytest -v -s

mypy: ## Run mypy type check over src folder
	$(RUN) mypy src

create-user: ## Create test user on running instance via curl (usage: make create-user email="email")
	curl -X POST http://localhost:$(APP_PORT)/api/auth/register \
	-H "Content-Type: application/json" \
	-d "{ \
		\"email\": \"$(email)\", \
		\"password\": \"strongpassword123\", \
		\"full_name\": \"Test User\" \
	}"


help:
	@echo ""
	@echo "Available commands:"
	@echo ""
	@awk 'BEGIN {FS=":.*##"} \
		/^[a-zA-Z_-]+:.*##/ { printf "  %-16s %s\n", $$1, $$2 }' \
		$(MAKEFILE_LIST)
	@echo ""
