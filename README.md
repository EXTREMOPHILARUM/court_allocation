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

This application can be deployed using Docker. The repository includes GitHub Actions for automatic deployment.

### Prerequisites

1. Server with Docker installed
2. GitHub repository secrets configured:
   - `SERVER_HOST`: Deployment server hostname/IP
   - `SERVER_USERNAME`: Server SSH username (needs sudo privileges for port 80)
   - `SERVER_SSH_KEY`: Server SSH private key

### Manual Deployment

To deploy manually:

```bash
# Clone the repository
git clone <repository-url> /opt/court-allocation
cd /opt/court-allocation

# Build the Docker image
docker build -t court-allocation .

# Run the container (requires sudo for port 80)
sudo docker run -d \
  --name court-allocation \
  --restart unless-stopped \
  -p 80:7860 \
  court-allocation
```

The application will be available at `http://your-server`

### Note on Port 80

Since we're using port 80, which is a privileged port (requires root access):
1. Ensure your deployment user has sudo privileges
2. Alternatively, you can:
   - Use a reverse proxy like Nginx (recommended for production)
   - Or use a higher port number (e.g., 8080) and configure your firewall rules
