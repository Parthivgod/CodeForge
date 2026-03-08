# EC2 + Docker Compose Deployment Guide

## Overview
This guide walks you through deploying CodeForge on AWS EC2 using Docker Compose. Estimated cost: ~$30/month for a t3.medium instance.

## Prerequisites
- AWS Account
- Domain name (optional, for HTTPS)
- Local machine with AWS CLI installed

## Step 1: Launch EC2 Instance

### 1.1 Create EC2 Instance
```bash
# Recommended instance type: t3.medium (2 vCPU, 4GB RAM)
# OS: Ubuntu 22.04 LTS
# Storage: 30GB gp3
```

### 1.2 Security Group Configuration
Create a security group with these inbound rules:
- SSH (22) - Your IP only
- HTTP (80) - 0.0.0.0/0
- HTTPS (443) - 0.0.0.0/0
- Custom TCP (8000) - 0.0.0.0/0 (Backend API)
- Custom TCP (5173) - 0.0.0.0/0 (Frontend - temporary for testing)

## Step 2: Connect to EC2 and Install Dependencies

### 2.1 SSH into your instance
```bash
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

### 2.2 Update system and install Docker
```bash
# Update package list
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo apt install docker-compose -y

# Verify installation
docker --version
docker-compose --version

# Log out and back in for group changes to take effect
exit
```

### 2.3 SSH back in
```bash
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

## Step 3: Clone and Configure Application

### 3.1 Clone repository
```bash
git clone https://github.com/Parthivgod/CodeForge.git
cd CodeForge
```

### 3.2 Create production .env file
```bash
nano .env
```

Add your environment variables:
```env
# AWS Credentials
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1

# Model Configuration
MODEL_MAPPER=openai.gpt-oss-120b-1:0
MODEL_LINKER=us.amazon.nova-pro-v1:0
MODEL_SENTINEL=us.deepseek.r1-v1:0

# LangSmith (Optional)
LANGSMITH_TRACING=true
LANGCHAIN_TRACING_V2=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_PROJECT=CodeForge

# Database
POSTGRES_USER=codeforge_user
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=codeforge_db

# Backend URL (update with your EC2 public IP or domain)
VITE_API_URL=http://your-ec2-ip:8000
```

## Step 4: Build and Deploy

### 4.1 Start services
```bash
# Build and start all services
docker-compose up -d --build

# Check logs
docker-compose logs -f

# Check running containers
docker ps
```

### 4.2 Verify deployment
```bash
# Test backend
curl http://localhost:8000/health

# Test database connection
docker-compose exec db psql -U codeforge_user -d codeforge_db -c "SELECT version();"
```

## Step 5: Access Your Application

- Frontend: `http://your-ec2-ip:5173`
- Backend API: `http://your-ec2-ip:8000`
- API Docs: `http://your-ec2-ip:8000/docs`

## Step 6: Production Optimizations (Optional)

### 6.1 Set up Nginx reverse proxy
```bash
sudo apt install nginx -y

# Create Nginx config
sudo nano /etc/nginx/sites-available/codeforge
```

Add this configuration:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:5173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/codeforge /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 6.2 Set up SSL with Let's Encrypt (if using domain)
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

### 6.3 Set up auto-restart on reboot
```bash
# Enable Docker to start on boot
sudo systemctl enable docker

# Create systemd service for docker-compose
sudo nano /etc/systemd/system/codeforge.service
```

Add:
```ini
[Unit]
Description=CodeForge Docker Compose
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ubuntu/CodeForge
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

Enable the service:
```bash
sudo systemctl enable codeforge.service
sudo systemctl start codeforge.service
```

## Maintenance Commands

### View logs
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db
```

### Restart services
```bash
docker-compose restart
```

### Update application
```bash
git pull
docker-compose down
docker-compose up -d --build
```

### Backup database
```bash
docker-compose exec db pg_dump -U codeforge_user codeforge_db > backup_$(date +%Y%m%d).sql
```

### Restore database
```bash
cat backup_20240308.sql | docker-compose exec -T db psql -U codeforge_user codeforge_db
```

## Monitoring

### Check resource usage
```bash
# System resources
htop

# Docker stats
docker stats

# Disk usage
df -h
docker system df
```

### Clean up Docker resources
```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Full cleanup
docker system prune -a --volumes
```

## Troubleshooting

### Container won't start
```bash
docker-compose logs backend
docker-compose logs frontend
```

### Database connection issues
```bash
docker-compose exec db psql -U codeforge_user -d codeforge_db
```

### Port already in use
```bash
sudo lsof -i :8000
sudo lsof -i :5173
```

### Reset everything
```bash
docker-compose down -v
docker-compose up -d --build
```

## Cost Optimization

### t3.medium pricing (~$30/month)
- Instance: ~$30/month
- Storage (30GB): ~$3/month
- Data transfer: Variable

### To reduce costs:
1. Use t3.small for testing (~$15/month)
2. Stop instance when not in use
3. Use AWS Free Tier eligible t2.micro for demos (limited performance)

## Security Checklist

- [ ] Change default database password
- [ ] Restrict SSH access to your IP only
- [ ] Set up SSL/HTTPS
- [ ] Keep AWS credentials secure (use IAM roles if possible)
- [ ] Regular security updates: `sudo apt update && sudo apt upgrade`
- [ ] Set up CloudWatch monitoring
- [ ] Enable AWS backup for EC2 instance
- [ ] Use AWS Secrets Manager for sensitive data

## Next Steps

1. Set up monitoring with CloudWatch
2. Configure automated backups
3. Set up CI/CD pipeline
4. Migrate to ECS for better scalability (when needed)
