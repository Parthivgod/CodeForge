# Frontend Deployment Guide

## Overview
The backend is already deployed on Render at `https://codeforge-6nhc.onrender.com`. This guide shows how to deploy the frontend.

## Quick Start - Local Development

```bash
cd frontend
npm install
npm run dev
```

- Frontend: http://localhost:5173
- Backend: https://codeforge-6nhc.onrender.com

## Deploy to Render (Recommended)

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

## Deploy to Vercel

```bash
cd frontend
npm i -g vercel
vercel --prod
```

Set environment variable:
```bash
vercel env add VITE_API_URL
# Enter: https://codeforge-6nhc.onrender.com
```

## Deploy to Netlify

```bash
cd frontend
npm install
npm run build
```

Drag and drop the `dist` folder to [netlify.com/drop](https://netlify.com/drop)

## Environment Variables

The frontend needs one environment variable:
```env
VITE_API_URL=https://codeforge-6nhc.onrender.com
```

## Testing

Check backend health:
```bash
curl https://codeforge-6nhc.onrender.com/health
```

Should return: `{"status":"healthy"}`