---
title: "GitHub Actions"
tags: [ci-cd, github, automation]
created: 2026-06-22
updated: 2026-06-22
sources: [PROJECT_SPEC-2026]
related: [docker, fastapi]
---

# GitHub Actions

GitHub Actions is the chosen CI/CD platform for Project Chicken Soup, providing automated testing, building, and deployment.

## Overview

GitHub Actions is simple, integrated with GitHub, and free for open source projects. It provides a YAML-based configuration format for defining workflows.

## Role in Project Chicken Soup

GitHub Actions handles:
- **Automated testing** — Runs pytest tests on every push and pull request
- **Building** — Builds the Docker image on release
- **Deployment** — Deploys to production on merge to main
- **Linting** — Runs lint checks on every commit

## Configuration

The GitHub Actions configuration is stored in `.github/workflows/` and defines the following workflows:
- **tests.yml** — Runs tests on every push
- **build.yml** — Builds the Docker image on release
- **deploy.yml** — Deploys to production on merge to main
- **lint.yml** — Runs lint checks on every commit

## See Also

- [[docker]]
- [[fastapi]]
- [[key-decisions]]
