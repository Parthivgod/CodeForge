# Frontend-Only Deployment Guide (Using Render Backend)

## Overview
This guide shows how to deploy just the frontend since the backend is already running on Render at `https://codeforge-6nhc.onrender.com`.

## Option 1: Deploy Frontend to Render

### 1. Create Render Account
- Go to [render.com](https://render.com)
- Sign up/login with GitHub

### 2. Deploy Frontend
1. Connect your GitHub repository
2. Create a new "Static Site"
3. Configure:
   - **Build Command**: `cd frontend && npm install && npm run build`
   - **Publish Directory**: `frontend/dist`
   - **Environment Variables**:
     - `VITE_API_URL`: `https://codeforge-6nhc.onrender.com`

### 3. Custom Domain (Optional)
- Add your custom domain in Render dashboard
- Update DNS records as instructed

## Option 2: Deploy Frontend to Vercel

### 1. Install Vercel CLI
```bash
npm i -g vercel
```

### 2. Deploy
```bash
cd frontend
vercel --prod
```

### 3. Set Environment Variables
```bash
vercel env add VITE_API_URL
# Enter: https://codeforge-6nhc.onrender.com
```

## Option 3: Deploy Frontend to Netlify

### 1. Build the frontend
```bash
cd frontend
npm install
npm run build
```

### 2. Deploy to Netlify
- Drag and drop the `dist` folder to [netlify.com/drop](https://netlify.com/drop)
- Or use Netlify CLI:
```bash
npm install -g netlify-cli
netlify deploy --prod --dir=dist
```

### 3. Set Environment Variables
In Netlify dashboard:
- Go to Site Settings > Environment Variables
- Add `VITE_API_URL` = `https://codeforge-6nhc.onrender.com`

## Option 4: Local Development with Render Backend

### 1. Update environment
```bash
cd frontend
echo "VITE_API_URL=https://codeforge-6nhc.onrender.com" > .env.local
```

### 2. Start development server
```bash
npm install
npm run dev
```

### 3. Access application
- Frontend: http://localhost:5173
- Backend API: https://codeforge-6nhc.onrender.com

## Option 5: Docker Frontend Only

### 1. Build and run frontend container
```bash
# Development
docker-compose -f docker-compose.frontend.yml up -d

# Production
docker build -f frontend/Dockerfile.prod -t codeforge-frontend frontend/
docker run -p 80:80 -e VITE_API_URL=https://codeforge-6nhc.onrender.com codeforge-frontend
```

## Testing the Setup

### 1. Check backend health
```bash
curl https://codeforge-6nhc.onrender.com/health
# Should return: {"status":"healthy"}
```

### 2. Test API endpoints
```bash
# Check API documentation
curl https://codeforge-6nhc.onrender.com/docs

# Test analyze endpoint (requires file upload)
curl -X POST https://codeforge-6nhc.onrender.com/analyze \
  -F "repo_url=https://github.com/your-repo/example"
```

### 3. Verify frontend connection
- Open browser developer tools
- Check Network tab for API calls to `codeforge-6nhc.onrender.com`
- Ensure no CORS errors

## Environment Variables Reference

### Frontend (.env or deployment config)
```env
VITE_API_URL=https://codeforge-6nhc.onrender.com
```

## Troubleshooting

### CORS Issues
If you encounter CORS errors, the backend needs to be updated to allow your frontend domain. Contact the backend maintainer.

### API Connection Issues
1. Check if backend is healthy: `curl https://codeforge-6nhc.onrender.com/health`
2. Verify the API URL in your frontend environment variables
3. Check browser developer tools for network errors

### Build Issues
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install

# Check for environment variable issues
npm run build -- --debug
```

## Cost Comparison

| Platform | Cost | Features |
|----------|------|----------|
| Render Static Site | Free tier available | Custom domains, auto-deploy |
| Vercel | Free tier available | Edge functions, analytics |
| Netlify | Free tier available | Forms, functions, split testing |
| Docker (Self-hosted) | Server costs only | Full control |

## Production Checklist

- [ ] Environment variables configured
- [ ] Custom domain set up (if needed)
- [ ] HTTPS enabled
- [ ] Error monitoring configured
- [ ] Analytics set up (optional)
- [ ] Performance monitoring
- [ ] Backup strategy for static assets

## Next Steps

1. Set up monitoring for the frontend
2. Configure error tracking (Sentry, LogRocket)
3. Set up analytics (Google Analytics, Plausible)
4. Optimize build performance
5. Set up CI/CD pipeline for automatic deployments