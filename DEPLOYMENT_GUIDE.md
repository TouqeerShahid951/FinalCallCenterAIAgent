# Deployment & Operations Guide - AI Voice Assistant

## Quick Start

### 1. Docker Deployment
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 2. Production Setup
```bash
# Build production images
docker-compose -f docker-compose.prod.yml up -d --build

# Scale backend instances
docker-compose up -d --scale backend=3
```

## Environment Configuration

### Required Variables
```bash
# .env
OPENROUTER_API_KEY=your_key_here
ENVIRONMENT=production
LOG_LEVEL=WARNING
```

### Nginx Configuration
```nginx
upstream backend_servers {
    server backend:8000;
    server backend:8001;
    server backend:8002;
}

location /ws/ {
    proxy_pass http://backend_servers;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

## Monitoring

### Health Checks
```bash
# Service health
curl http://localhost:8000/health

# Pipeline status
curl http://localhost:8000/pipeline/status
```

### Log Management
```bash
# View logs
docker-compose logs -f backend

# Check errors
docker-compose logs backend | grep ERROR
```

## Performance Optimization

### Pipeline Settings
```python
ULTRA_FAST_CONFIG = {
    "max_buffer_duration": 1.5,
    "min_processing_interval": 0.1,
    "enable_parallel_processing": True
}
```

### Resource Limits
```yaml
# docker-compose.prod.yml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 4G
```

## Security

### SSL Setup
```bash
# Generate certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Firewall
```bash
# Allow necessary ports
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 8000
```

## Backup & Recovery

### Database Backup
```bash
#!/bin/bash
# Backup ChromaDB
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf "chroma_backup_$DATE.tar.gz" -C ./chroma .
```

### Configuration Backup
```bash
# Backup config files
tar -czf config_backup.tar.gz \
    docker-compose.yml \
    nginx/ \
    .env
```

## Troubleshooting

### Common Issues
1. **WebSocket Connection Failed**
   - Check backend status: `docker-compose ps`
   - Verify ports: `netstat -tlnp | grep 8000`

2. **Audio Not Working**
   - Check microphone permissions
   - Verify WebSocket connection
   - Check browser console for errors

3. **Slow Response Times**
   - Enable ultra-fast mode
   - Check system resources: `docker stats`
   - Optimize pipeline configuration

### Debug Mode
```python
# Enable debug logging
logging.getLogger().setLevel(logging.DEBUG)

# Enable pipeline debugging
pipeline.enable_debug_mode(True)
```

## Maintenance

### Regular Tasks
- **Daily**: Check service health, monitor logs
- **Weekly**: Update packages, rotate logs
- **Monthly**: Security updates, SSL renewal

### Update Procedure
```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

*For detailed implementation, refer to the technical architecture and API reference documentation.*
