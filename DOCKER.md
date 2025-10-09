# Docker Setup for NestWatch NeMo Agent

This document provides instructions for running the NestWatch NeMo Agent application using Docker.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 4GB RAM available for containers

## Quick Start

### 1. Build and Run with Docker Compose

```bash
# Build and start all services
docker-compose up --build

# Run in detached mode
docker-compose up -d --build
```

### 2. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Individual Service Commands

### Frontend Only

```bash
# Build frontend image
docker build -f Dockerfile.frontend -t nestwatch-frontend .

# Run frontend container
docker run -p 3000:3000 nestwatch-frontend
```

### Backend Only

```bash
# Build backend image
docker build -f Dockerfile.backend -t nestwatch-backend .

# Run backend container
docker run -p 8000:8000 nestwatch-backend
```

## Environment Configuration

### Required Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Backend Configuration
PYTHONPATH=/app
ENVIRONMENT=production

# AI Provider Configuration (choose one or more)
ANTHROPIC_API_KEY=your_anthropic_key_here
OPENAI_API_KEY=your_openai_key_here
AWS_ACCESS_KEY_ID=your_aws_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_here

# Optional: Model Configuration
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
OPENAI_MODEL=gpt-4
```

### Environment File Mounting

The docker-compose.yml automatically mounts `.env` files if they exist. You can also mount additional environment files:

```yaml
volumes:
  - ./.env:/app/.env:ro
  - ./multi-provider.env:/app/multi-provider.env:ro
```

## Development vs Production

### Development Mode

For development with hot reloading:

```bash
# Frontend development
docker-compose -f docker-compose.dev.yml up frontend

# Backend development  
docker-compose -f docker-compose.dev.yml up backend
```

### Production Mode

For production deployment:

```bash
# Production build
docker-compose -f docker-compose.prod.yml up -d

# With custom environment
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d
```

## Container Management

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Health Checks

```bash
# Check service health
docker-compose ps

# Backend health endpoint
curl http://localhost:8000/api/v1/health
```

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```bash
   # Check if ports are in use
   lsof -i :3000
   lsof -i :8000
   
   # Use different ports
   docker-compose up -p 3001:3000 -p 8001:8000
   ```

2. **Permission Issues**
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER .
   ```

3. **Build Failures**
   ```bash
   # Clean build
   docker-compose down
   docker system prune -f
   docker-compose up --build --no-cache
   ```

### Debugging

```bash
# Enter container for debugging
docker-compose exec backend bash
docker-compose exec frontend sh

# Check container resources
docker stats

# View detailed logs
docker-compose logs --tail=100 backend
```

## Production Deployment

### Security Considerations

1. **Use secrets management** for API keys
2. **Enable HTTPS** with reverse proxy
3. **Configure firewall** rules
4. **Use non-root users** (already configured)

### Scaling

```bash
# Scale backend instances
docker-compose up --scale backend=3

# Use load balancer
docker-compose -f docker-compose.prod.yml up -d
```

### Monitoring

```bash
# Container health monitoring
docker-compose ps
docker stats

# Application health
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/providers/health
```

## File Structure

```
├── Dockerfile.frontend      # Frontend container definition
├── Dockerfile.backend      # Backend container definition  
├── docker-compose.yml      # Service orchestration
├── .dockerignore          # Build optimization
├── DOCKER.md              # This documentation
└── .env                   # Environment configuration
```

## Advanced Configuration

### Custom Docker Compose Files

Create environment-specific compose files:

```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    volumes:
      - .:/app
      - /app/node_modules
    environment:
      - NODE_ENV=development
```

### Multi-stage Builds

Both Dockerfiles use multi-stage builds for:
- Smaller production images
- Better security
- Optimized layer caching

### Resource Limits

Add resource constraints:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'
```

## Support

For issues related to Docker setup:

1. Check container logs: `docker-compose logs`
2. Verify environment variables: `docker-compose config`
3. Test individual services: `docker-compose up <service>`
4. Review this documentation for common solutions
