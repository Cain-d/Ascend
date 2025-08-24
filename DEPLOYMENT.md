# Deployment Guide

## Production Deployment Options

### Option 1: Docker Deployment (Recommended)

1. **Build and run with Docker Compose:**
   ```bash
   # Clone the repository
   git clone <your-repo-url>
   cd Ascend
   
   # Create production environment file
   cp .env.example .env
   # Edit .env with production values
   
   # Build and start services
   docker-compose up -d
   ```

2. **Environment Variables for Production:**
   ```bash
   SECRET_KEY=your-very-secure-secret-key-here
   DATABASE_PATH=data/ascend.db
   CORS_ORIGINS=https://yourdomain.com
   ACCESS_TOKEN_EXPIRE_MINUTES=1440
   ```

### Option 2: Manual Deployment

1. **Server Setup:**
   ```bash
   # Install Python 3.8+
   sudo apt update
   sudo apt install python3 python3-pip python3-venv nginx
   
   # Clone repository
   git clone <your-repo-url>
   cd Ascend
   ```

2. **Backend Setup:**
   ```bash
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Setup environment
   cp .env.example .env
   # Edit .env with production settings
   
   # Initialize database
   python init_db.py
   
   # Start with gunicorn (production WSGI server)
   pip install gunicorn
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```

3. **Frontend Setup:**
   ```bash
   cd ascend-frontend
   npm install
   npm run build
   
   # Serve static files with nginx
   sudo cp dist/* /var/www/html/
   ```

4. **Nginx Configuration:**
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;
       
       location / {
           root /var/www/html;
           try_files $uri $uri/ /index.html;
       }
       
       location /api {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

### Option 3: Cloud Deployment

#### Heroku
1. Create `Procfile`:
   ```
   web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

2. Deploy:
   ```bash
   heroku create your-app-name
   heroku config:set SECRET_KEY=your-secret-key
   git push heroku main
   ```

#### AWS/DigitalOcean
- Use the Docker deployment option
- Set up load balancer and SSL certificates
- Configure environment variables in your cloud provider's interface

## Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Use HTTPS in production
- [ ] Configure proper CORS origins
- [ ] Set up database backups
- [ ] Enable logging and monitoring
- [ ] Use environment variables for all secrets
- [ ] Set up firewall rules
- [ ] Regular security updates

## Monitoring

### Health Checks
- API health: `GET /` should return `{"message": "Ascend API is running"}`
- Database: Check if database file exists and is accessible

### Logging
- Application logs: Check uvicorn/gunicorn logs
- Access logs: Monitor nginx access logs
- Error tracking: Consider integrating Sentry or similar

### Performance
- Monitor API response times
- Database query performance
- Memory and CPU usage
- Disk space (especially for SQLite database)

## Backup Strategy

### Database Backup
```bash
# Create backup
cp data/ascend.db data/backup/ascend_$(date +%Y%m%d_%H%M%S).db

# Automated backup script
#!/bin/bash
BACKUP_DIR="data/backup"
mkdir -p $BACKUP_DIR
cp data/ascend.db $BACKUP_DIR/ascend_$(date +%Y%m%d_%H%M%S).db

# Keep only last 30 days of backups
find $BACKUP_DIR -name "ascend_*.db" -mtime +30 -delete
```

### Application Backup
- Code: Use Git for version control
- Configuration: Backup .env and nginx configs
- Static files: Backup uploaded files if any

## Troubleshooting

### Common Issues

1. **Database locked error:**
   - Check if multiple processes are accessing the database
   - Ensure proper database connection handling

2. **CORS errors:**
   - Verify CORS_ORIGINS in .env
   - Check frontend API base URL

3. **Authentication issues:**
   - Verify SECRET_KEY is set
   - Check JWT token expiration

4. **Performance issues:**
   - Monitor database size and queries
   - Consider migrating to PostgreSQL for high load
   - Implement caching strategies

### Log Locations
- Application: Check uvicorn/gunicorn output
- System: `/var/log/nginx/` for nginx logs
- Database: SQLite doesn't have separate logs

## Scaling Considerations

### Database
- SQLite is suitable for small to medium applications
- For high traffic, migrate to PostgreSQL or MySQL
- Implement connection pooling

### Application
- Use multiple worker processes
- Implement caching (Redis)
- Consider microservices architecture for large scale

### Infrastructure
- Load balancing for multiple instances
- CDN for static assets
- Database replication for read scaling