# Multi-stage Dockerfile for SIH26108 Frontend
# Stage 1: Build static web assets
FROM node:20-alpine AS build

WORKDIR /app

# Install npm dependencies
COPY package.json package-lock.json ./
RUN npm ci

# Copy frontend source code
COPY . .

# Optional build-time environment variable for backend API URL
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

# Build production Vite bundle
RUN npm run build

# Stage 2: Serve compiled static application using Nginx
FROM nginx:alpine

# Copy compiled static assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy Nginx server configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose HTTP port
EXPOSE 80

# Start Nginx web server
CMD ["nginx", "-g", "daemon off;"]
