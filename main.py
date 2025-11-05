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
matchups_df = None

def load_data():
    """Load CSV data into pandas DataFrames"""
    global batters_df, bowlers_df, matchups_df
    try:
        batters_df = pd.read_csv(settings.BATTERS_CSV)
        bowlers_df = pd.read_csv(settings.BOWLERS_CSV)
        matchups_df = pd.read_csv(settings.MATCHUPS_CSV)
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
    return {"status": "healthy", "data_loaded": batters_df is not None and bowlers_df is not None and matchups_df is not None}

@app.get("/teams")
async def get_teams():
    """Get list of BBL teams"""
    return {"teams": settings.BBL_TEAMS}

@app.get("/matchups")
async def get_matchups():
    """Get available matchups from the dataset"""
    if matchups_df is None:
        raise HTTPException(status_code=500, detail="Matchup data not loaded")
    
    # Get unique matchups from the dataset
    unique_matchups = matchups_df['Matchup'].unique()
    
    matchups = []
    for matchup in unique_matchups:
        # Extract teams from matchup string (e.g., "Sydney Sixers vs Perth Scorchers")
        teams = matchup.split(' vs ')
        if len(teams) == 2:
            matchups.append({
                "id": matchup.replace(' ', '_').replace('vs', 'vs'),
                "matchup": matchup,
                "team1": teams[0].strip(),
                "team2": teams[1].strip()
            })
    
    return {"matchups": matchups}

@app.get("/matchup-players")
async def get_matchup_players(matchup: str):
    """Get players for a specific matchup"""
    if matchups_df is None:
        raise HTTPException(status_code=500, detail="Matchup data not loaded")
    
    # Filter matchup data for the specific matchup
    matchup_players = matchups_df[matchups_df['Matchup'] == matchup]
    
    if matchup_players.empty:
        raise HTTPException(status_code=404, detail="Matchup not found")
    
    players = []
    for _, player in matchup_players.iterrows():
        players.append({
            "PlayerName": player['PlayerName'],
            "TeamName": player['TeamName'],
            "Matchup": player['Matchup']
        })
    
    return players

@app.get("/player-stats/{player_name}")
async def get_player_stats(player_name: str):
    """Get detailed stats for a specific player"""
    if batters_df is None or bowlers_df is None:
        raise HTTPException(status_code=500, detail="Player data not loaded")
    
    player_stats = {"name": player_name}
    
    # Check if player is a batter
    batter_data = batters_df[batters_df['BatsmanName'] == player_name]
    if not batter_data.empty:
        batter = batter_data.iloc[0]
        player_stats["batting_stats"] = {
            "team": batter['Team'],
            "total_innings": int(batter['Total.Innings']),
            "total_runs": int(batter['Total.Runs']),
            "runs_10_plus_pct": batter['Percentage.of.No.of.times.BatsmanName.scored.more.than.10.runs'],
            "runs_20_plus_pct": batter['Percentage.of.No.of.times.BatsmanName.scored.more.than.20.runs'],
            "top_scorer_pct": batter['Percentage.of.Top.Team.Runs.Scorer'],
            "six_hit_pct": batter['Percentage.of.No.of.Times.BatsmanName.Hit.Atleast.One.Six'],
            "runs_10_plus_count": int(batter['No.of.times.BatsmanName.scored.more.than.10.runs']),
            "runs_20_plus_count": int(batter['No.of.times.BatsmanName.scored.more.than.20.runs']),
            "top_scorer_count": int(batter['Top.Team.Runs.Scorer']),
            "six_hit_count": int(batter['No.of.Times.BatsmanName.Hit.Atleast.One.Six'])
        }
    
    # Check if player is a bowler
    bowler_data = bowlers_df[bowlers_df['BowlerName'] == player_name]
    if not bowler_data.empty:
        bowler = bowler_data.iloc[0]
        player_stats["bowling_stats"] = {
            "team": bowler['bowling_team'],
            "total_innings": int(bowler['Innings.by.Bowler']),
            "total_wickets": int(bowler['Total.Wickets']),
            "wicket_1_plus_pct": bowler['Percentage.of.No.of.times.BowlerName.Took.Atleast.1.Wicket'],
            "wicket_2_plus_pct": bowler['Percentage.of.No.of.times.BowlerName.Took.Atleast.2.Wicket'],
            "top_wicket_taker_pct": bowler['Percentage.of.Top.Wicket.Taker.for.Team'],
            "wicket_1_plus_count": int(bowler['No.of.times.BowlerName.Took.Atleast.1.Wicket']),
            "wicket_2_plus_count": int(bowler['No.of.times.BowlerName.Took.Atleast.2.Wicket']),
            "top_wicket_taker_count": int(bowler['Top.Wicket.Taker.for.Team'])
        }
    
    if "batting_stats" not in player_stats and "bowling_stats" not in player_stats:
        raise HTTPException(status_code=404, detail="Player not found")
    
    return player_stats

@app.get("/team-stats/{team_name}")
async def get_team_stats(team_name: str):
    """Get player stats for a specific team from matchup data"""
    if matchups_df is None or batters_df is None or bowlers_df is None:
        raise HTTPException(status_code=500, detail="Data not loaded")
    
    # Get players for the team from matchups data
    team_players = matchups_df[matchups_df['TeamName'] == team_name]['PlayerName'].tolist()
    
    if not team_players:
        raise HTTPException(status_code=404, detail=f"No players found for team: {team_name}")
    
    player_stats = []
    
    for player_name in team_players:
        player_stat = {"name": player_name, "batting_stats": None, "bowling_stats": None}
        
        # Get batting stats
        batter_data = batters_df[batters_df['BatsmanName'] == player_name]
        if not batter_data.empty:
            batter = batter_data.iloc[0]
            player_stat["batting_stats"] = {
                "total_innings": int(batter['Total.Innings']),
                "total_runs": int(batter['Total.Runs']),
                "runs_10_plus_pct": batter['Percentage.of.No.of.times.BatsmanName.scored.more.than.10.runs'],
                "runs_20_plus_pct": batter['Percentage.of.No.of.times.BatsmanName.scored.more.than.20.runs'],
                "six_hit_pct": batter['Percentage.of.No.of.Times.BatsmanName.Hit.Atleast.One.Six'],
                "top_scorer_pct": batter['Percentage.of.Top.Team.Runs.Scorer']
            }
        
        # Get bowling stats
        bowler_data = bowlers_df[bowlers_df['BowlerName'] == player_name]
        if not bowler_data.empty:
            bowler = bowler_data.iloc[0]
            player_stat["bowling_stats"] = {
                "total_innings": int(bowler['Innings.by.Bowler']),
                "total_wickets": int(bowler['Total.Wickets']),
                "wicket_1_plus_pct": bowler['Percentage.of.No.of.times.BowlerName.Took.Atleast.1.Wicket'],
                "wicket_2_plus_pct": bowler['Percentage.of.No.of.times.BowlerName.Took.Atleast.2.Wicket'],
                "top_wicket_taker_pct": bowler['Percentage.of.Top.Wicket.Taker.for.Team']
            }
        
        player_stats.append(player_stat)
    
    return {"team": team_name, "players": player_stats}

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
