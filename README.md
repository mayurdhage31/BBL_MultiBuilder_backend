# BBL Multi Builder Backend

A FastAPI backend for the BBL (Big Bash League) Multi Builder application that provides cricket betting recommendations based on historical player performance data.

## Features

- **Match Selection**: Get available BBL matches
- **Team Data**: Access player statistics for all BBL teams
- **Smart Recommendations**: AI-powered betting recommendations based on historical data
- **Multi-bet Builder**: Create multi-leg bets with combined odds calculation
- **CORS Support**: Configured for local development with React frontend

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Core Endpoints
- `GET /` - API information
- `GET /health` - Health check
- `GET /teams` - List of BBL teams
- `GET /matches` - Available match fixtures

### Data Endpoints
- `GET /players/{team}` - Get players for a specific team
- `POST /recommendations` - Get betting recommendations for a match
- `POST /build-multi` - Build a multi-bet with selected options

## Data Sources

The application uses two CSV files with historical BBL data:
- `BBL_batters.csv` - Batting statistics and percentages
- `BBL_bowlers.csv` - Bowling statistics and percentages

## Betting Markets

### Batting Markets
- 10+ Runs
- 20+ Runs  
- To Hit a Six
- Top Team Run Scorer (TTRS)

### Bowling Markets
- 1+ Wickets
- 2+ Wickets
- Top Team Wicket Taker

## Configuration

All settings are managed in `config.py`:
- CORS origins for frontend integration
- Data file paths
- BBL team names
- Betting market definitions
