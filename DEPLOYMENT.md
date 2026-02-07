# Deployment Guide

Complete deployment instructions for production environments.

## Prerequisites
- Python 3.8+
- PostgreSQL or MySQL
- Nginx web server
- Domain name (optional)

## Quick Deploy with Docker

1. Install Docker and Docker Compose
2. Run: docker-compose up -d
3. Access at http://localhost

## Manual Deployment

See full documentation in docs/deployment.md

## Security Checklist
- Change SECRET_KEY
- Set DEBUG=False
- Configure ALLOWED_HOSTS
- Enable SSL/HTTPS
- Configure firewall
