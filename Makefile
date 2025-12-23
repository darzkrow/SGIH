# Makefile para comandos comunes del proyecto

.PHONY: help build up down logs shell migrate test clean

help: ## Mostrar ayuda
	@echo "Comandos disponibles:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Construir imágenes Docker
	docker-compose -f docker-compose.dev.yml build

up: ## Levantar servicios en modo desarrollo
	docker-compose -f docker-compose.dev.yml up -d

down: ## Detener servicios
	docker-compose -f docker-compose.dev.yml down

logs: ## Ver logs de todos los servicios
	docker-compose -f docker-compose.dev.yml logs -f

shell: ## Abrir shell en el contenedor web
	docker-compose -f docker-compose.dev.yml exec web python manage.py shell

migrate: ## Ejecutar migraciones
	docker-compose -f docker-compose.dev.yml exec web python manage.py migrate

makemigrations: ## Crear migraciones
	docker-compose -f docker-compose.dev.yml exec web python manage.py makemigrations

test: ## Ejecutar tests
	docker-compose -f docker-compose.dev.yml exec web python manage.py test

collectstatic: ## Recopilar archivos estáticos
	docker-compose -f docker-compose.dev.yml exec web python manage.py collectstatic --noinput

superuser: ## Crear superusuario
	docker-compose -f docker-compose.dev.yml exec web python manage.py createsuperuser

clean: ## Limpiar contenedores y volúmenes
	docker-compose -f docker-compose.dev.yml down -v
	docker system prune -f

# Comandos para producción
prod-build: ## Construir para producción
	docker-compose build

prod-up: ## Levantar en producción
	docker-compose up -d

prod-down: ## Detener producción
	docker-compose down

prod-logs: ## Ver logs de producción
	docker-compose logs -f