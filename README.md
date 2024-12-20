---
title: court_allocation
app_file: app.py
sdk: gradio
sdk_version: 4.44.1
---
# Pickleball Tournament Court Allocation Calculator

This application helps tournament organizers calculate the number of courts needed for a pickleball tournament based on various parameters including participant numbers, categories, and match formats.

## Features

- Calculate courts needed based on total participants
- Automatic distribution of players into:
  - Advanced Men's Doubles
  - Mixed Doubles
  - Amateur Categories
  - Optional 35+ Category
  - Optional Open Category
- Round-robin format calculations
- Group distribution visualization
- Detailed breakdown of participant categories

## Installation

1. Clone this repository
2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:
```bash
python app.py
```

2. Open the provided URL in your web browser
3. Input the following parameters:
   - Total number of participants
   - Whether to include 35+ category
   - Whether to include open category
4. Click submit to see the detailed court allocation and tournament statistics

## Assumptions

- Each match takes approximately 30 minutes
- Tournament duration is 8 hours
- Round-robin groups contain 4 teams each
- Advanced players make up 2/3 of total participants
- Among advanced players, 1/3 are women

## Deployment

This application is deployed using Docker Compose with Traefik as a reverse proxy, operating behind Cloudflare for SSL/TLS termination.

### Prerequisites

1. Server with Docker and Docker Compose installed
2. Domain name pointed to your server through Cloudflare
3. GitHub repository secrets configured:
   - `SERVER_HOST`: Deployment server hostname/IP
   - `SERVER_USERNAME`: Server SSH username
   - `SERVER_SSH_KEY`: Server SSH private key

### Initial Setup

1. Ensure your domains are properly configured in Cloudflare:
   - `courts.saurabhn.com`
   - `traefik.saurabhn.com`
2. Enable Cloudflare proxy (orange cloud) for both domains

### Local Development

For local development and testing:

1. Add the following entries to your `/etc/hosts` file:
```
127.0.0.1    courts.localhost
127.0.0.1    traefik.localhost
```

2. Start the application in development mode:
```bash
# Start with Docker Compose Watch
docker compose -f docker-compose.local.yml watch

# Or start normally without watch mode
docker compose -f docker-compose.local.yml up -d
```

The application will be available at:
- Main application: `http://courts.localhost`
- Traefik dashboard: `http://traefik.localhost`

Development Features:
- Hot reload: Changes to Python files are synced immediately
- Auto rebuild: Changes to `requirements.txt` or `Dockerfile` trigger rebuilds
- Ignored files: Git, cache, and environment files are excluded from syncing
- Container logs are preserved for debugging

### Manual Deployment

```bash
# Clone the repository
git clone <repository-url> /opt/court-allocation
cd /opt/court-allocation

# Start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

The application will be available at:
- Main application: `http://courts.saurabhn.com` (HTTPS provided by Cloudflare)
- Traefik dashboard: `http://traefik.saurabhn.com` (HTTPS provided by Cloudflare)

### Features

- **Traefik Reverse Proxy**:
  - Domain-based routing
  - Docker integration
  - Load balancing
  - Health checks

- **Cloudflare Integration**:
  - SSL/TLS termination
  - DDoS protection
  - Caching
  - Analytics

- **Container Management**:
  - Automatic container restart
  - Health monitoring
  - Log rotation (max 3 files of 10MB each)
  - Easy deployment commands

### Security Notes

1. SSL/TLS is handled by Cloudflare
2. Internal communication uses HTTP
3. Container security options are enabled
4. Network isolation between containers
