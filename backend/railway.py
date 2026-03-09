"""
Railway deployment configuration for CodeForge backend
"""
import os
from main import app

# Railway sets PORT environment variable
port = int(os.environ.get("PORT", 8000))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)