start-neo4j:
	docker compose -f docker-compose.neo4j.yml --env-file .env up -d

stop-neo4j:
	docker compose -f docker-compose.neo4j.yml down

