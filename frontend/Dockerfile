FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy application code
COPY . .

# Expose port
EXPOSE 5173

# Run development server (for production, use npm run build && npm run preview)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
