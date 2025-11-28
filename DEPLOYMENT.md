# Deployment Guide for task.ziro-one.ir

This guide explains how to deploy the Task Manager API to your production server with Nginx.

## Prerequisites

- Docker and Docker Compose installed on server
- Domain `task.ziro-one.ir` pointing to your server's IP
- SSH access to the server
- `.env` file configured with production credentials

## Deployment Steps

### 1. Clone Repository on Server

```bash
cd /opt  # or your preferred location
git clone <your-repository-url> task-manager
cd task-manager
```

### 2. Create Production Environment File

```bash
cp .env.example .env
nano .env
```

Configure the following variables:

```env
# Liara AI Configuration
LIARA_API_KEY=your_production_api_key
LIARA_BASE_URL=https://api.liara.ir/v1
LIARA_MODEL=gpt-4o-mini

# JWT Configuration (IMPORTANT: Use a strong secret key)
JWT_SECRET_KEY=your-very-secure-production-secret-key-here

# OTP Configuration
OTP_LENGTH=6
OTP_EXPIRY_MINUTES=5

# Faraz SMS Configuration
FARAZ_SMS_USERNAME=your_faraz_username
FARAZ_SMS_PASSWORD=your_faraz_password
FARAZ_SMS_FROM_NUMBER=your_sender_number
FARAZ_SMS_PATTERN_CODE=your_pattern_bodyId

# Database Configuration
DATABASE_URL=sqlite+aiosqlite:///./data/tasks.db
```

### 3. Create Required Directories

```bash
mkdir -p data logs logs/nginx
chmod 755 data logs
```

### 4. Build and Start Services

For development/testing:
```bash
docker-compose up -d --build
```

For production:
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

### 5. Verify Deployment

Check container status:
```bash
docker-compose ps
```

Check logs:
```bash
docker-compose logs -f app
docker-compose logs -f nginx
```

Test the API:
```bash
curl http://task.ziro-one.ir:8080/health
```

### 6. Configure SSL/HTTPS (Optional but Recommended)

#### Using Let's Encrypt with Certbot

Install Certbot:
```bash
sudo apt-get update
sudo apt-get install certbot
```

Stop Nginx temporarily:
```bash
docker-compose stop nginx
```

Obtain SSL certificate:
```bash
sudo certbot certonly --standalone -d task.ziro-one.ir
```

Update `nginx.conf`:
```bash
nano nginx.conf
# Uncomment the HTTPS server block and HTTP redirect section
```

Restart services:
```bash
docker-compose up -d
```

#### SSL Auto-Renewal

Add to crontab:
```bash
sudo crontab -e
```

Add this line:
```
0 0 * * 0 certbot renew --quiet && docker-compose restart nginx
```

## Maintenance Commands

### View Logs

```bash
# Application logs
docker-compose logs -f app

# Nginx logs
docker-compose logs -f nginx

# All logs
docker-compose logs -f
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart app
docker-compose restart nginx
```

### Stop Services

```bash
docker-compose down
```

### Update Application

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

### Backup Database

```bash
# Create backup
cp data/tasks.db data/tasks.db.backup-$(date +%Y%m%d-%H%M%S)

# Or use docker volume backup
docker run --rm -v task-manager_data:/data -v $(pwd)/backups:/backup \
  alpine tar czf /backup/tasks-backup-$(date +%Y%m%d).tar.gz /data
```

### Database Migration

If you need to reset the database:
```bash
docker-compose down
rm data/tasks.db
docker-compose up -d
# Database will be recreated automatically
```

## Monitoring

### Check Service Health

```bash
# Health check endpoint
curl http://task.ziro-one.ir:8080/health

# Check container health
docker inspect --format='{{.State.Health.Status}}' task-manager-api
```

### Monitor Resource Usage

```bash
docker stats task-manager-api task-manager-nginx
```

## Troubleshooting

### Container won't start

Check logs:
```bash
docker-compose logs app
```

Check environment variables:
```bash
docker-compose config
```

### Nginx configuration errors

Test Nginx config:
```bash
docker exec task-manager-nginx nginx -t
```

Reload Nginx:
```bash
docker exec task-manager-nginx nginx -s reload
```

### Database locked errors

Stop all containers:
```bash
docker-compose down
```

Check for stale lock files:
```bash
rm data/tasks.db-journal 2>/dev/null || true
```

Restart:
```bash
docker-compose up -d
```

### Permission issues

Fix ownership:
```bash
sudo chown -R $USER:$USER data logs
chmod -R 755 data logs
```

## Security Recommendations

1. **Use Strong JWT Secret**: Generate with `openssl rand -hex 32`
2. **Enable HTTPS**: Use Let's Encrypt SSL certificates
3. **Firewall Rules**:
   ```bash
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```
4. **Regular Backups**: Automate database backups
5. **Keep Updated**: Regularly update Docker images and dependencies
6. **Monitor Logs**: Set up log monitoring and alerts
7. **Rate Limiting**: Consider adding rate limiting to Nginx

## API Endpoints

After deployment, your API will be available at:

- **Base URL**: `http://task.ziro-one.ir:8080` or `https://task.ziro-one.ir:8443`
- **API Documentation**: `http://task.ziro-one.ir:8080/docs`
- **Health Check**: `http://task.ziro-one.ir:8080/health`

**Note**: Using ports 8080 (HTTP) and 8443 (HTTPS) to avoid conflicts with existing nginx on your server.

## Support

For issues or questions:
- Check logs: `docker-compose logs -f`
- Review configuration: `docker-compose config`
- Verify environment: `docker exec task-manager-api env | grep LIARA`
