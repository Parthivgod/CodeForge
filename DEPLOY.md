# Frontend Deployment Guide

## Overview
This guide shows how to run CodeForge with a local backend and deploy the frontend.

## Quick Start - Full Local Development

### 1. Start Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Start Frontend
```bash
cd frontend
npm install
npm run dev
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Deploy Frontend Only (with Local Backend)

### Deploy to Render
1. Create a new "Static Site" on Render
2. Configure:
   - **Build Command**: `cd frontend && npm install && npm run build`
   - **Publish Directory**: `frontend/dist`
   - **Environment Variables**:
     - `VITE_API_URL`: `http://your-local-ip:8000`

### Deploy to Vercel
```bash
cd frontend
npm i -g vercel
vercel --prod
```

Set environment variable:
```bash
vercel env add VITE_API_URL
# Enter: http://your-local-ip:8000
```

### Deploy to Netlify
```bash
cd frontend
npm install
npm run build
```

Drag and drop the `dist` folder to [netlify.com/drop](https://netlify.com/drop)

## Environment Variables

The frontend needs one environment variable:
```env
VITE_API_URL=http://localhost:8000
```

For production deployments, replace `localhost` with your actual IP address.

## Testing

Check backend health:
```bash
curl http://localhost:8000/health
```

Should return: `{"status":"healthy"}`

## Running Both Services

### Option 1: Separate Terminals
```bash
# Terminal 1 - Backend
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend  
cd frontend
npm run dev
```

### Option 2: Using Docker Compose (if you have docker-compose.yml)
```bash
docker-compose up -d
```

## Troubleshooting

### Backend Not Starting
- Check if port 8000 is available: `lsof -i :8000`
- Verify Python dependencies: `pip install -r requirements.txt`
- Check AWS credentials in `.env` file

### Frontend Can't Connect to Backend
- Ensure backend is running on `http://localhost:8000`
- Check CORS settings in backend
- Verify `VITE_API_URL` environment variable

### CORS Issues
Make sure your backend allows requests from your frontend domain. Check the CORS middleware configuration in `backend/main.py`.