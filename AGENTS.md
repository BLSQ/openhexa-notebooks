# AGENTS.md

This file provides guidance to AI agents when working with code in this repository.

## Project Overview

OpenHEXA Notebooks is a custom JupyterHub setup that integrates with the OpenHEXA data platform. It runs on Kubernetes in production and uses Docker Compose for local development. The component authenticates users through the OpenHEXA App component and provides isolated Jupyter notebook environments.

## Architecture

- **JupyterHub**: Customized with `AppAuthenticator` for OpenHEXA integration
- **Authentication**: Cookie-based authentication with the OpenHEXA App at `http://localhost:8000`
- **Spawning**: KubeSpawner in production, DockerSpawner for local development
- **Configuration**: Split between `jupyterhub_config.py` (shared) and `jupyterhub_dev_config.py` (local development)
- **Custom Features**:
  - Workspace-based credentials injection
  - Dynamic Docker image selection
  - Custom pod naming and storage management
  - Automatic server shutdown on logout

## Development Commands

### Local Development Setup
```bash
# Using published Docker images (faster)
docker compose -f docker-compose.yml -f docker-compose-withdockerhub.yml up

# Building images locally (slower, for development)
docker compose build
docker compose up
```

### Prerequisites
- Docker and Docker Compose installed
- OpenHEXA App running at `http://localhost:8000`
- External Docker network `openhexa` must exist

## Key Configuration Files

- `jupyterhub/config/jupyterhub_config.py`: Main configuration with custom authenticator
- `jupyterhub/config/jupyterhub_dev_config.py`: Local development overrides
- `docker-compose.yml`: Base compose configuration
- `docker-compose-withdockerhub.yml`: Override for using published images

## Docker Images

- Production: `blsq/openhexa-jupyterhub:latest`
- Development: Built from `jupyterhub/Dockerfile.dev`
- Base notebook image: `blsq/openhexa-base-environment:latest`

## Custom Authenticator Details

The `AppAuthenticator` class handles:
- Cookie-based authentication with OpenHEXA App
- Credential injection from workspace or default endpoints
- Dynamic Docker image selection for workspaces
- Storage configuration (persistent vs ephemeral)
- Environment variable management for spawned containers

## Environment Variables

Key variables for local development:
- `AUTHENTICATION_URL`: App authentication endpoint
- `DEFAULT_CREDENTIALS_URL`: Default credentials endpoint
- `WORKSPACE_CREDENTIALS_URL`: Workspace credentials endpoint
- `HEXA_SERVER_URL`: OpenHEXA server URL
- `HUB_DB_URL`: PostgreSQL connection string
- `JUPYTER_IMAGE`: Default notebook image

## Kubernetes Resource Management

### Resource Configuration Strategy
Production typically uses low guarantees with high limits to maximize cluster density:
- **CPU Guarantee**: 0.05 cores (allows high pod density)
- **Memory Guarantee**: 64MB (minimal reservation)
- **CPU Limit**: 4 cores (burst capacity for active work)
- **Memory Limit**: 32GB (handles large datasets/ML workloads)

### Potential Issues with Low Guarantees

**Issue 1: Startup Delays**
- Kubernetes scheduler sees "available" resources based on guarantees, not actual usage
- If running pods exceed their guarantees, new notebooks may experience slow startup
- Symptoms: 2-5+ minute startup times, "Pod pending" states, startup timeouts
- Mitigation: Increase `c.KubeSpawner.start_timeout = 600` and monitor cluster utilization

**Issue 3: OOM (Out of Memory) Risk**
- Linux kernel prioritizes killing processes that exceed their memory guarantee
- Jupyter needs 200-400MB minimum but only has 64MB guarantee
- Under memory pressure, Jupyter processes may be killed by OOM killer
- Symptoms: "Kernel died" messages, lost work, inconsistent behavior
- Mitigation: Consider higher memory guarantee (e.g., 256MB) or robust monitoring

Both issues are more likely when cluster utilization exceeds 70-80% or during simultaneous user activity spikes.

## Deployment

Production deployment uses Helm charts with Zero to JupyterHub (z2jh). Docker images are built and published via GitHub Actions on releases.
