# AWS App Runner Deployment Guide

## Prerequisites

1. AWS CLI configured with appropriate permissions
2. GitHub repository with your code
3. AWS App Runner service permissions

## Backend Deployment

### 1. Create App Runner Service for Backend

```bash
aws apprunner create-service \
  --service-name "codeforge-backend" \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "public.ecr.aws/docker/library/python:3.11-slim",
      "ImageConfiguration": {
        "Port": "8000"
      },
      "ImageRepositoryType": "ECR_PUBLIC"
    },
    "CodeRepository": {
      "RepositoryUrl": "https://github.com/YOUR_USERNAME/CodeForge",
      "SourceCodeVersion": {
        "Type": "BRANCH",
        "Value": "main"
      },
      "CodeConfiguration": {
        "ConfigurationSource": "REPOSITORY",
        "CodeConfigurationValues": {
          "Runtime": "DOCKER",
          "BuildCommand": "docker build -f backend/Dockerfile.apprunner -t backend .",
          "StartCommand": "uvicorn main:app --host 0.0.0.0 --port 8000",
          "Port": "8000",
          "RuntimeEnvironmentVariables": {
            "AWS_ACCESS_KEY_ID": "your-access-key",
            "AWS_SECRET_ACCESS_KEY": "your-secret-key",
            "AWS_REGION": "us-east-1",
            "MODEL_MAPPER": "anthropic.claude-3-haiku-20240307-v1:0",
            "MODEL_LINKER": "anthropic.claude-3-sonnet-20240229-v1:0",
            "MODEL_SENTINEL": "anthropic.claude-3-opus-20240229-v1:0"
          }
        }
      }
    }
  }' \
  --instance-configuration '{
    "Cpu": "1 vCPU",
    "Memory": "2 GB"
  }' \
  --health-check-configuration '{
    "Protocol": "HTTP",
    "Path": "/health",
    "Interval": 10,
    "Timeout": 5,
    "HealthyThreshold": 1,
    "UnhealthyThreshold": 5
  }'
```

### 2. Alternative: Use AWS Console

1. Go to AWS App Runner console
2. Click "Create service"
3. Choose "Source code repository"
4. Connect your GitHub repository
5. Select branch: `main`
6. Build settings:
   - Runtime: Docker
   - Build command: `docker build -f backend/Dockerfile.apprunner -t backend .`
   - Start command: `uvicorn main:app --host 0.0.0.0 --port 8000`
7. Configure environment variables (see above)
8. Set instance configuration: 1 vCPU, 2 GB RAM
9. Configure health check: `/health` endpoint

## Frontend Deployment

### 1. Create App Runner Service for Frontend

```bash
aws apprunner create-service \
  --service-name "codeforge-frontend" \
  --source-configuration '{
    "CodeRepository": {
      "RepositoryUrl": "https://github.com/YOUR_USERNAME/CodeForge",
      "SourceCodeVersion": {
        "Type": "BRANCH",
        "Value": "main"
      },
      "CodeConfiguration": {
        "ConfigurationSource": "REPOSITORY",
        "CodeConfigurationValues": {
          "Runtime": "DOCKER",
          "BuildCommand": "docker build -f frontend/Dockerfile.apprunner -t frontend .",
          "StartCommand": "nginx -g \"daemon off;\"",
          "Port": "8080",
          "RuntimeEnvironmentVariables": {
            "VITE_API_URL": "https://your-backend-apprunner-url.us-east-1.awsapprunner.com"
          }
        }
      }
    }
  }' \
  --instance-configuration '{
    "Cpu": "0.25 vCPU",
    "Memory": "0.5 GB"
  }' \
  --health-check-configuration '{
    "Protocol": "HTTP",
    "Path": "/health",
    "Interval": 10,
    "Timeout": 5,
    "HealthyThreshold": 1,
    "UnhealthyThreshold": 5
  }'
```

### 2. Update Frontend API URL

After backend is deployed, update the frontend environment variable:

```bash
aws apprunner update-service \
  --service-arn "arn:aws:apprunner:region:account:service/codeforge-frontend/xxx" \
  --source-configuration '{
    "CodeRepository": {
      "CodeConfiguration": {
        "CodeConfigurationValues": {
          "RuntimeEnvironmentVariables": {
            "VITE_API_URL": "https://your-actual-backend-url.us-east-1.awsapprunner.com"
          }
        }
      }
    }
  }'
```

## Cost Estimation

- **Backend**: ~$25-40/month (1 vCPU, 2GB RAM)
- **Frontend**: ~$10-15/month (0.25 vCPU, 0.5GB RAM)
- **Total**: ~$35-55/month

## Benefits of App Runner

✅ **Zero infrastructure management**
✅ **Auto-scaling** (scales to zero when not used)
✅ **Built-in load balancing**
✅ **HTTPS by default**
✅ **Automatic deployments** from GitHub
✅ **Health checks and monitoring**
✅ **Pay only for what you use**

## Monitoring

- View logs in AWS CloudWatch
- Monitor metrics in App Runner console
- Set up CloudWatch alarms for errors

## Custom Domain (Optional)

1. Add custom domain in App Runner console
2. Create CNAME record in your DNS
3. App Runner handles SSL certificate automatically

## Troubleshooting

- Check CloudWatch logs for errors
- Verify environment variables are set correctly
- Ensure health check endpoints return 200 status
- Check that ports match (8000 for backend, 8080 for frontend)