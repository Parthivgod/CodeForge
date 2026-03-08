# AWS App Runner Deployment Guide

## Prerequisites

1. AWS CLI configured with appropriate permissions
2. GitHub repository with your code
3. AWS App Runner service permissions

## Deployment Steps

### Step 1: Deploy Backend

1. **Go to AWS App Runner Console**
2. **Click "Create service"**
3. **Source and deployment:**
   - Repository type: "Source code repository"
   - Connect to GitHub and select your repository
   - Branch: `main`
   - Deployment trigger: "Automatic"

4. **Build settings:**
   - Configuration source: "Use a configuration file"
   - Or manually configure:
     - Runtime: Docker
     - Build command: `docker build -f backend/Dockerfile.apprunner .`
     - Start command: `uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1`

5. **Service settings:**
   - Service name: `codeforge-backend`
   - Port: `8000`
   - Environment variables:
     ```
     AWS_ACCESS_KEY_ID=your-access-key
     AWS_SECRET_ACCESS_KEY=your-secret-key
     AWS_REGION=us-east-1
     MODEL_MAPPER=anthropic.claude-3-haiku-20240307-v1:0
     MODEL_LINKER=anthropic.claude-3-sonnet-20240229-v1:0
     MODEL_SENTINEL=anthropic.claude-3-opus-20240229-v1:0
     ```

6. **Instance configuration:**
   - CPU: 1 vCPU
   - Memory: 2 GB

7. **Health check:**
   - Path: `/health`
   - Interval: 20 seconds
   - Timeout: 10 seconds
   - Healthy threshold: 1
   - Unhealthy threshold: 5

8. **Click "Create & deploy"**

### Step 2: Get Backend URL

After backend deployment completes:
1. Copy the App Runner service URL (e.g., `https://abc123.us-east-1.awsapprunner.com`)
2. Test it: `curl https://your-backend-url/health`

### Step 3: Deploy Frontend

1. **Create another App Runner service**
2. **Source and deployment:**
   - Same repository, `main` branch

3. **Build settings:**
   - Runtime: Docker
   - Build command: `docker build -f frontend/Dockerfile.apprunner .`
   - Start command: `/start.sh`

4. **Service settings:**
   - Service name: `codeforge-frontend`
   - Port: `8080`
   - Environment variables:
     ```
     VITE_API_URL=https://your-backend-url-from-step2
     ```

5. **Instance configuration:**
   - CPU: 0.25 vCPU
   - Memory: 0.5 GB

6. **Health check:**
   - Path: `/health`

7. **Click "Create & deploy"**

## Alternative: CLI Deployment

### Backend CLI Command

```bash
aws apprunner create-service \
  --service-name "codeforge-backend" \
  --source-configuration '{
    "CodeRepository": {
      "RepositoryUrl": "https://github.com/YOUR_USERNAME/CodeForge",
      "SourceCodeVersion": {
        "Type": "BRANCH",
        "Value": "main"
      },
      "CodeConfiguration": {
        "ConfigurationSource": "API",
        "CodeConfigurationValues": {
          "Runtime": "DOCKER",
          "BuildCommand": "docker build -f backend/Dockerfile.apprunner .",
          "StartCommand": "uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1",
          "Port": "8000",
          "RuntimeEnvironmentVariables": {
            "AWS_ACCESS_KEY_ID": "your-access-key",
            "AWS_SECRET_ACCESS_KEY": "your-secret-key",
            "AWS_REGION": "us-east-1"
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
    "Interval": 20,
    "Timeout": 10,
    "HealthyThreshold": 1,
    "UnhealthyThreshold": 5
  }'
```

## Troubleshooting

### Common Issues:

1. **"Runtime version not supported"**
   - Use Docker runtime instead of Python runtime
   - Ensure Dockerfile.apprunner is in the correct directory

2. **Build fails**
   - Check that all dependencies are in requirements.txt
   - Verify Dockerfile syntax

3. **Health check fails**
   - Ensure `/health` endpoint returns 200 status
   - Check that the app starts on the correct port

4. **Frontend can't connect to backend**
   - Verify VITE_API_URL environment variable
   - Check CORS settings in backend

### Viewing Logs

```bash
# Get service ARN first
aws apprunner list-services

# View logs
aws logs describe-log-groups --log-group-name-prefix "/aws/apprunner"
```

## Cost Estimation

- **Backend**: ~$25-40/month (1 vCPU, 2GB RAM)
- **Frontend**: ~$10-15/month (0.25 vCPU, 0.5GB RAM)
- **Total**: ~$35-55/month

## Benefits

✅ **Zero infrastructure management**
✅ **Auto-scaling** (scales to zero when not used)
✅ **Built-in load balancing**
✅ **HTTPS by default**
✅ **Automatic deployments** from GitHub
✅ **Health checks and monitoring**