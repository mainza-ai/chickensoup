---
title: "Docker"
tags: [docker, container, devops]
created: 2026-06-22
updated: 2026-06-22
sources: [docker-2026]
related: [local-first-llm, ai-alien-connection]
---

# Docker

Docker is used for containerization and orchestration of Project Chicken Soup services. It provides a simple, portable deployment target.

## Key Features

- **Containerization** — Package services in containers
- **Orchestration** — Docker Compose for multi-service
- **Portability** — Run on any platform
- **Reproducibility** — Same environment everywhere
- **Scalability** — Easy to scale services

## Configuration

- **docker-compose.yml** — Multi-service orchestration
- **Dockerfile** — Build instructions
- **Services:** neo4j, redis, chickensoup

## Services

- **neo4j** — Knowledge graph
- **redis** — Caching
- **chickensoup** — Main application

## Integration

- **Docker Compose** — `docker-compose up`
- **Dockerfile** — `docker build -t chickensoup .`
- **Environment** — `.env` file for configuration
- **Volumes** — Persistent storage
- **Networking** — Internal networking between services

## See Also

- [[local-first-llm]]
- [[ai-alien-connection]]
