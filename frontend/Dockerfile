# Multi-stage Dockerfile for MicroCFO Frontend
# Stage 1: Builder - Install dependencies and build React app
FROM node:20-alpine as builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production=false

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Stage 2: Runtime - Nginx to serve static files
FROM nginx:alpine

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Create non-root user
RUN addgroup -g 1000 microcfo && \
    adduser -D -u 1000 -G microcfo microcfo && \
    chown -R microcfo:microcfo /usr/share/nginx/html && \
    chown -R microcfo:microcfo /var/cache/nginx && \
    chown -R microcfo:microcfo /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown -R microcfo:microcfo /var/run/nginx.pid

# Switch to non-root user
USER microcfo

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
