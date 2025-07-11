# Multi-stage Dockerfile for Mobius Frontend Production
# Optimized for production deployment with minimal runtime

# Build stage
FROM node:20-alpine as builder

# Install dependencies for building native modules
# Pinned versions for Alpine 3.22 to ensure reproducible builds
RUN apk add --no-cache python3=3.12.11-r0 make=4.4.1-r3 g++=14.2.0-r6

# Set working directory
WORKDIR /app

# Copy package files
COPY frontend/package*.json ./

# Install dependencies with frozen lockfile
RUN npm ci --no-audit --fund=false

# Copy source files
COPY frontend/ .

# Build the application for production
ENV NODE_ENV=production
RUN npm run build

# Production stage - nginx for serving static files
FROM nginx:1.27-alpine

# Install curl for health checks
# Pinned version for Alpine 3.22 to ensure reproducible builds
RUN apk add --no-cache curl=8.11.1-r0

# Remove default nginx config
RUN rm -rf /etc/nginx/conf.d/*

# Copy custom nginx configuration
COPY docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Copy built application from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Create non-root user for nginx
RUN addgroup -g 1001 -S nginx && \
    adduser -u 1001 -S nginx -G nginx && \
    chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown nginx:nginx /var/run/nginx.pid

# Switch to non-root user
USER nginx

# Expose port 80 (nginx will run on this port)
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

# Start nginx in foreground
CMD ["nginx", "-g", "daemon off;"]
