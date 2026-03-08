# Render Deployment Guide

## Backend Deployment on Render

### Step 1: Create Web Service

1. **Go to [Render Dashboard](https://dashboard.render.com/)**
2. **Click "New +" → "Web Service"**
3. **Connect your GitHub repository**
4. **Configure the service:**

   - **Name**: `codeforge-backend`
   - **Region**: Choose closest to your users
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Step 2: Environment Variables

Add these environment variables in Render dashboard:

```
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
MODEL_MAPPER=anthropic.claude-3-haiku-20240307-v1:0
MODEL_LINKER=anthropic.claude-3-sonnet-20240229-v1:0
MODEL_SENTINEL=anthropic.claude-3-opus-20240229-v1:0
LANGSMITH_TRACING=false
LANGCHAIN_TRACING_V2=false
```

### Step 3: Advanced Settings

- **Auto-Deploy**: Yes
- **Health Check Path**: `/health`
- **Instance Type**: Starter (512MB RAM) or Standard (2GB RAM recommended)

### Step 4: Deploy

1. **Click "Create Web Service"**
2. **Wait for deployment** (5-10 minutes)
3. **Copy the service URL** (e.g., `https://codeforge-backend.onrender.com`)
4. **Test**: `curl https://your-backend-url/health`

## Frontend Deployment

### Option 1: Render Static Site

1. **Create "Static Site" on Render**
2. **Configure:**
   - **Name**: `codeforge-frontend`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm ci && npm run build`
   - **Publish Directory**: `dist`
   - **Environment Variables**:
     ```
     VITE_API_URL=https://your-backend-url.onrender.com
     ```

### Option 2: Netlify (Recommended for Frontend)

1. **Go to [Netlify](https://netlify.com)**
2. **Connect GitHub repository**
3. **Configure:**
   - **Base directory**: `frontend`
   - **Build command**: `npm ci && npm run build`
   - **Publish directory**: `frontend/dist`
   - **Environment variables**:
     ```
     VITE_API_URL=https://your-backend-url.onrender.com
     ```

### Option 3: Vercel

1. **Go to [Vercel](https://vercel.com)**
2. **Import GitHub repository**
3. **Configure:**
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Environment Variables**:
     ```
     VITE_API_URL=https://your-backend-url.onrender.com
     ```

## Cost Comparison

### Render (Backend)
- **Starter**: Free (512MB RAM, sleeps after 15min inactivity)
- **Standard**: $7/month (2GB RAM, always on)

### Frontend Hosting
- **Netlify**: Free (100GB bandwidth)
- **Vercel**: Free (100GB bandwidth)
- **Render Static**: Free (100GB bandwidth)

**Total Cost**: $0-7/month (much cheaper than AWS!)

## Benefits of Render

✅ **Simple deployment** from GitHub
✅ **Free tier available**
✅ **Automatic HTTPS**
✅ **Built-in monitoring**
✅ **Easy environment variables**
✅ **Auto-deploy on git push**
✅ **Health checks**

## Troubleshooting

### Common Issues:

1. **Build fails**
   - Check that `requirements.txt` includes all dependencies
   - Verify Python version compatibility

2. **App doesn't start**
   - Check logs in Render dashboard
   - Verify start command uses `$PORT` environment variable

3. **Health check fails**
   - Ensure `/health` endpoint returns 200 status
   - Check that app binds to `0.0.0.0:$PORT`

4. **Frontend can't connect to backend**
   - Verify `VITE_API_URL` environment variable
   - Check CORS settings in backend

### Viewing Logs

- **Render Dashboard** → Your Service → "Logs" tab
- Real-time logs during deployment and runtime

## Custom Domain (Optional)

1. **In Render Dashboard** → Service → "Settings"
2. **Add custom domain**
3. **Update DNS records** as instructed
4. **SSL certificate** is automatic

## Scaling

- **Render**: Upgrade to Standard ($7/month) for better performance
- **Add Redis**: For persistent job status (optional)
- **CDN**: Render includes CDN for static assets