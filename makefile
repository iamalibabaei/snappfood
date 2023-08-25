run:
	sudo docker-compose down
	sudo docker-compose up -d --build
test-unit: run
	sudo docker exec -it web python manage.py test store.tests.unit
test-integration: run
	sudo docker exec -it web python manage.py test store.tests.integration
