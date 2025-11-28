# Port Configuration - No Conflicts with Existing Server

## Port Mapping

Your Task Manager API uses **custom ports** to avoid conflicts with existing nginx on your server:

- **HTTP**: Port `8080` (instead of 80)
- **HTTPS**: Port `8443` (instead of 443)

## How It Works

```
Internet Request → Server Ports 8080/8443 → Docker Nginx Container (80/443) → FastAPI App (8000)
```

The nginx container internally listens on ports 80/443, but Docker maps them to 8080/8443 on your host machine.

## Access URLs

After deployment, access your API at:

- **Base URL**: `http://task.ziro-one.ir:8080`
- **API Docs**: `http://task.ziro-one.ir:8080/docs`
- **Health Check**: `http://task.ziro-one.ir:8080/health`

With HTTPS enabled:
- **Base URL**: `https://task.ziro-one.ir:8443`
- **API Docs**: `https://task.ziro-one.ir:8443/docs`

## Deployment Commands

**Deploy to production** (safe, won't affect other projects):
```bash
cd /opt/task-manager
make prod-deploy
```

**Check status**:
```bash
docker ps | grep task-manager
```

**View logs**:
```bash
make prod-logs
```

**Test the deployment**:
```bash
curl http://task.ziro-one.ir:8080/health
```

## What Changed

### Files Updated:
1. ✅ `docker-compose.yml` - Changed ports from 80:80 to 8080:80
2. ✅ `docker-compose.prod.yml` - Changed ports from 80:80 to 8080:80
3. ✅ `DEPLOYMENT.md` - Updated all URL references to include :8080 port

### What Stayed the Same:
- ✅ `nginx.conf` - No changes needed (listens internally on 80/443)
- ✅ Application code - No changes needed
- ✅ Environment variables - No changes needed

## Firewall Configuration

If you need to open these ports on your server:

```bash
# Allow custom HTTP port
sudo ufw allow 8080/tcp

# Allow custom HTTPS port
sudo ufw allow 8443/tcp

# Check firewall status
sudo ufw status
```

## Verifying No Conflicts

Check what's using ports on your server:

```bash
# Check if port 8080 is available
sudo lsof -i :8080

# Check if port 8443 is available
sudo lsof -i :8443

# Check what's using port 80 (your existing nginx)
sudo lsof -i :80
```

If ports 8080/8443 are free, you're good to deploy! ✅

## Reverting to Standard Ports (80/443)

If you later want to use standard ports, simply edit the docker-compose files:

```yaml
# Change from:
ports:
  - "8080:80"
  - "8443:443"

# To:
ports:
  - "80:80"
  - "443:443"
```

Then redeploy with `make prod-deploy`.
