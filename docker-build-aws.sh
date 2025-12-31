#!/bin/bash

# ========================================
# Docker Build Script for AWS Deployment
# ========================================

set -e  # Exit on error

echo "🚀 Building Dermatology AI Backend for AWS (CPU-only)"
echo "=================================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found! Copying from .env.example..."
    cp .env.example .env
    echo "✅ Please edit .env file with your actual credentials before deploying!"
fi

# Build the Docker image
echo "📦 Building Docker image (this may take 10-15 minutes)..."
docker-compose build --no-cache app

# Tag the image for AWS ECR (optional)
if [ ! -z "$AWS_ECR_REPOSITORY" ]; then
    echo "🏷️  Tagging image for AWS ECR: $AWS_ECR_REPOSITORY"
    docker tag dermatology-api:cpu-latest $AWS_ECR_REPOSITORY:latest
    docker tag dermatology-api:cpu-latest $AWS_ECR_REPOSITORY:$(date +%Y%m%d-%H%M%S)
fi

echo ""
echo "✅ Build completed successfully!"
echo ""
echo "Next steps:"
echo "1. Test locally: docker-compose up"
echo "2. Push to ECR: aws ecr get-login-password | docker login --username AWS --password-stdin \$AWS_ECR_REPOSITORY"
echo "3. Push image: docker push \$AWS_ECR_REPOSITORY:latest"
echo ""
