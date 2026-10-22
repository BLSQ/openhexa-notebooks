# Every target has a short alias and a long name; `make` or `make help` lists them.

.DEFAULT_GOAL := help

COMPOSE := docker compose

.PHONY: help h b build r run rh run_hub

h help: ## Show this help
	@awk 'BEGIN { FS = ":.*## " } \
		/^[a-zA-Z0-9_ -]+:.*## / { target = $$1; gsub(/ /, ", ", target); printf "  \033[36m%-16s\033[0m %s\n", target, $$2 }' $(MAKEFILE_LIST)

b build: ## Build the hub docker image
	$(COMPOSE) build

r run: ## Run the hub with locally built images
	$(COMPOSE) up

rh run_hub: ## Run the hub with the published Docker Hub images (faster)
	$(COMPOSE) -f docker-compose.yml -f docker-compose-withdockerhub.yml up
