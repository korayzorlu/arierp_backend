COMPOSE_EXEC_WEB = docker compose exec web

command:
	$(COMPOSE_EXEC_WEB) python manage.py $(filter-out $@,$(MAKECMDGOALS))

migrate:
	$(COMPOSE_EXEC_WEB) python manage.py migrate $(filter-out $@,$(MAKECMDGOALS))

shell:
	$(COMPOSE_EXEC_WEB) python manage.py shell_plus

bash:
	$(COMPOSE_EXEC_WEB) bash

collectstatic:
	$(COMPOSE_EXEC_WEB) python manage.py collectstatic --noinput

createsuperuser:
	$(COMPOSE_EXEC_WEB) python manage.py createsuperuser

makemigrations:
	$(COMPOSE_EXEC_WEB) python manage.py makemigrations $(filter-out $@,$(MAKECMDGOALS))

logs:
	docker compose logs -f web

restart:
	docker compose restart web

# Genel amaçlı: make run CMD="python manage.py showmigrations"
run:
	$(COMPOSE_EXEC_WEB) $(CMD)