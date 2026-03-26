FROM node:20-slim

# Install git (required by baileys) and other build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    git \
    python3 \
    make \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy package files and install
COPY package.json ./
RUN npm install --production

# Copy source
COPY src/ ./src/

# Create auth directory
RUN mkdir -p /app/auth

# Default env
ENV PORT=3000
ENV WEBHOOK_URL=http://host.docker.internal:8000/webhook
ENV SESSION_NAME=default
ENV AUTH_DIR=/app/auth

EXPOSE 3000

CMD ["node", "src/index.js"]
