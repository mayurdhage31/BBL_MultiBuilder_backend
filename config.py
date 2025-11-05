"""
Configuration settings for BBL Multi Builder API
"""
import os
from typing import List

class Settings:
    # API Configuration
    API_TITLE = "BBL Multi Builder API"
    API_VERSION = "1.0.0"
    API_DESCRIPTION = "API for BBL cricket multi-bet builder application"
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # React development server
        "http://localhost:3001",  # Alternative React port
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://localhost:8080",  # Alternative frontend port
        "http://127.0.0.1:8080",
        "*"  # Allow all origins for development
    ]
    
    CORS_ALLOW_CREDENTIALS = True
    CORS_ALLOW_METHODS = ["*"]
    CORS_ALLOW_HEADERS = ["*"]
    
    # Data Configuration
    DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
    BATTERS_CSV = os.path.join(DATA_DIR, "BBL_batters.csv")
    BOWLERS_CSV = os.path.join(DATA_DIR, "BBL_bowlers.csv")
    MATCHUPS_CSV = os.path.join(DATA_DIR, "Matchupsdata.csv")
    
    # BBL Teams
    BBL_TEAMS = [
        "Adelaide Strikers",
        "Brisbane Heat", 
        "Hobart Hurricanes",
        "Melbourne Renegades",
        "Melbourne Stars",
        "Perth Scorchers",
        "Sydney Sixers",
        "Sydney Thunder"
    ]
    
    # Betting Markets Configuration
    BATTING_MARKETS = {
        "runs_10_plus": {
            "name": "10+ Runs",
            "csv_column": "Percentage.of.No.of.times.BatsmanName.scored.more.than.10.runs"
        },
        "runs_20_plus": {
            "name": "20+ Runs", 
            "csv_column": "Percentage.of.No.of.times.BatsmanName.scored.more.than.20.runs"
        },
        "hit_six": {
            "name": "To Hit a Six",
            "csv_column": "Percentage.of.No.of.Times.BatsmanName.Hit.Atleast.One.Six"
        },
        "top_team_scorer": {
            "name": "Top Team Run Scorer (TTRS)",
            "csv_column": "Percentage.of.Top.Team.Runs.Scorer"
        }
    }
    
    BOWLING_MARKETS = {
        "wicket_1_plus": {
            "name": "1+ Wickets",
            "csv_column": "Percentage.of.No.of.times.BowlerName.Took.Atleast.1.Wicket"
        },
        "wicket_2_plus": {
            "name": "2+ Wickets",
            "csv_column": "Percentage.of.No.of.times.BowlerName.Took.Atleast.2.Wicket"
        },
        "top_team_wickets": {
            "name": "Top Team Wicket Taker",
            "csv_column": "Percentage.of.Top.Wicket.Taker.for.Team"
        }
    }

settings = Settings()
