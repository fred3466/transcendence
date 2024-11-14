all: build

up:
	docker compose up -d

build:
	docker compose up -d --build

migrate:
	cd django &&	python3 manage.py migrate

down:
	docker compose down

clean: down
	docker rmi -f $$(docker images -q)
	
fclean: down
	docker system prune -a -f

re: fclean all

r: down up

PHONY: all up build migrate down clean fclean re r