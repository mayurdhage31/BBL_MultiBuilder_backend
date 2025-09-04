"""
BBL Multi Builder FastAPI Application
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import uvicorn
from typing import List, Dict, Any, Optional
import logging

from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Global data storage
batters_df = None
bowlers_df = None

def load_data():
    """Load CSV data into pandas DataFrames"""
    global batters_df, bowlers_df
    try:
        batters_df = pd.read_csv(settings.BATTERS_CSV)
        bowlers_df = pd.read_csv(settings.BOWLERS_CSV)
        logger.info("Data loaded successfully")
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        raise

@app.on_event("startup")
async def startup_event():
    """Load data on startup"""
    load_data()

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "BBL Multi Builder API", "version": settings.API_VERSION}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "data_loaded": batters_df is not None and bowlers_df is not None}

@app.get("/teams")
async def get_teams():
    """Get list of BBL teams"""
    return {"teams": settings.BBL_TEAMS}

@app.get("/matches")
async def get_available_matches():
    """Get available match combinations"""
    matches = []
    teams = settings.BBL_TEAMS
    
    # Generate sample matches (in real app, this would come from fixtures data)
    sample_matches = [
        {"home": "Melbourne Stars", "away": "Brisbane Heat"},
        {"home": "Adelaide Strikers", "away": "Sydney Sixers"},
        {"home": "Perth Scorchers", "away": "Hobart Hurricanes"},
        {"home": "Sydney Thunder", "away": "Melbourne Renegades"},
    ]
    
    for match in sample_matches:
        matches.append({
            "id": f"{match['home']}_vs_{match['away']}",
            "home_team": match["home"],
            "away_team": match["away"],
            "display_name": f"{match['home']} vs {match['away']}"
        })
    
    return {"matches": matches}

@app.get("/players/{team}")
async def get_team_players(team: str):
    """Get players for a specific team"""
    if team not in settings.BBL_TEAMS:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Get batters for the team
    team_batters = batters_df[batters_df['Team'] == team]
    # Get bowlers for the team  
    team_bowlers = bowlers_df[bowlers_df['bowling_team'] == team]
    
    batters = []
    for _, batter in team_batters.iterrows():
        batters.append({
            "name": batter['BatsmanName'],
            "type": "batter",
            "team": batter['Team'],
            "total_innings": int(batter['Total.Innings']),
            "total_runs": int(batter['Total.Runs'])
        })
    
    bowlers = []
    for _, bowler in team_bowlers.iterrows():
        bowlers.append({
            "name": bowler['BowlerName'],
            "type": "bowler", 
            "team": bowler['bowling_team'],
            "total_innings": int(bowler['Innings.by.Bowler']),
            "total_wickets": int(bowler['Total.Wickets'])
        })
    
    return {
        "team": team,
        "batters": batters,
        "bowlers": bowlers,
        "total_players": len(batters) + len(bowlers)
    }

@app.post("/recommendations")
async def get_recommendations(request: Dict[str, Any]):
    """Get player recommendations based on selected winner"""
    winner_team = request.get("winner_team")
    match_id = request.get("match_id")
    
    if not winner_team or winner_team not in settings.BBL_TEAMS:
        raise HTTPException(status_code=400, detail="Invalid winner team")
    
    # Parse match to get both teams
    if match_id:
        teams = match_id.replace("_vs_", " vs ").split(" vs ")
        if len(teams) == 2:
            home_team, away_team = teams[0], teams[1]
            match_teams = [home_team, away_team]
        else:
            match_teams = [winner_team]
    else:
        match_teams = [winner_team]
    
    recommendations = []
    
    # Get recommendations for all players in the match
    for team in match_teams:
        team_batters = batters_df[batters_df['Team'] == team]
        team_bowlers = bowlers_df[bowlers_df['bowling_team'] == team]
        
        # Process batters
        for _, batter in team_batters.iterrows():
            # 10+ runs market
            runs_10_pct = batter['Percentage.of.No.of.times.BatsmanName.scored.more.than.10.runs']
            if pd.notna(runs_10_pct) and runs_10_pct != "0.0%":
                recommendations.append({
                    "player_name": batter['BatsmanName'],
                    "team": batter['Team'],
                    "market": "10+ Runs",
                    "percentage": runs_10_pct,
                    "percentage_value": float(runs_10_pct.replace('%', '')) if isinstance(runs_10_pct, str) else runs_10_pct,
                    "type": "batting"
                })
            
            # 20+ runs market
            runs_20_pct = batter['Percentage.of.No.of.times.BatsmanName.scored.more.than.20.runs']
            if pd.notna(runs_20_pct) and runs_20_pct != "0.0%":
                recommendations.append({
                    "player_name": batter['BatsmanName'],
                    "team": batter['Team'],
                    "market": "20+ Runs",
                    "percentage": runs_20_pct,
                    "percentage_value": float(runs_20_pct.replace('%', '')) if isinstance(runs_20_pct, str) else runs_20_pct,
                    "type": "batting"
                })
            
            # Hit a six market
            six_pct = batter['Percentage.of.No.of.Times.BatsmanName.Hit.Atleast.One.Six']
            if pd.notna(six_pct) and six_pct != "0.0%":
                recommendations.append({
                    "player_name": batter['BatsmanName'],
                    "team": batter['Team'],
                    "market": "To Hit a Six",
                    "percentage": six_pct,
                    "percentage_value": float(six_pct.replace('%', '')) if isinstance(six_pct, str) else six_pct,
                    "type": "batting"
                })
            
            # TTRS market
            ttrs_pct = batter['Percentage.of.Top.Team.Runs.Scorer']
            if pd.notna(ttrs_pct) and ttrs_pct != "0.0%":
                recommendations.append({
                    "player_name": batter['BatsmanName'],
                    "team": batter['Team'],
                    "market": "Top Team Run Scorer (TTRS)",
                    "percentage": ttrs_pct,
                    "percentage_value": float(ttrs_pct.replace('%', '')) if isinstance(ttrs_pct, str) else ttrs_pct,
                    "type": "batting"
                })
        
        # Process bowlers
        for _, bowler in team_bowlers.iterrows():
            # 1+ wickets market
            wicket_1_pct = bowler['Percentage.of.No.of.times.BowlerName.Took.Atleast.1.Wicket']
            if pd.notna(wicket_1_pct) and wicket_1_pct != "0.0%":
                recommendations.append({
                    "player_name": bowler['BowlerName'],
                    "team": bowler['bowling_team'],
                    "market": "1+ Wickets",
                    "percentage": wicket_1_pct,
                    "percentage_value": float(wicket_1_pct.replace('%', '')) if isinstance(wicket_1_pct, str) else wicket_1_pct,
                    "type": "bowling"
                })
            
            # 2+ wickets market
            wicket_2_pct = bowler['Percentage.of.No.of.times.BowlerName.Took.Atleast.2.Wicket']
            if pd.notna(wicket_2_pct) and wicket_2_pct != "0.0%":
                recommendations.append({
                    "player_name": bowler['BowlerName'],
                    "team": bowler['bowling_team'],
                    "market": "2+ Wickets",
                    "percentage": wicket_2_pct,
                    "percentage_value": float(wicket_2_pct.replace('%', '')) if isinstance(wicket_2_pct, str) else wicket_2_pct,
                    "type": "bowling"
                })
    
    # Sort by percentage value (descending) and take top recommendations
    recommendations = sorted(recommendations, key=lambda x: x['percentage_value'], reverse=True)
    
    # Take top 7 recommendations as requested
    top_recommendations = recommendations[:7]
    
    return {
        "winner_team": winner_team,
        "match_teams": match_teams,
        "recommendations": top_recommendations,
        "total_available": len(recommendations)
    }

@app.post("/build-multi")
async def build_multi(request: Dict[str, Any]):
    """Build a multi-bet with selected options"""
    winner_team = request.get("winner_team")
    selected_bets = request.get("selected_bets", [])
    
    if not winner_team:
        raise HTTPException(status_code=400, detail="Winner team is required")
    
    if not selected_bets:
        raise HTTPException(status_code=400, detail="At least one bet must be selected")
    
    # Calculate combined odds (simplified - in real app would use proper odds calculation)
    total_percentage = 1.0
    for bet in selected_bets:
        percentage = bet.get("percentage_value", 0)
        if percentage > 0:
            total_percentage *= (percentage / 100)
    
    combined_percentage = total_percentage * 100
    
    multi_bet = {
        "winner_team": winner_team,
        "selected_bets": selected_bets,
        "total_legs": len(selected_bets) + 1,  # +1 for winner selection
        "combined_percentage": f"{combined_percentage:.2f}%",
        "estimated_odds": f"{100/combined_percentage:.2f}" if combined_percentage > 0 else "N/A"
    }
    
    return {"multi_bet": multi_bet}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
