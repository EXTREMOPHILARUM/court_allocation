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
