"""Team balancing algorithm for generating even teams."""
from typing import List
from itertools import combinations
import random
from api.models.schemas import PlayerInfo, Team


class TeamBalancer:
    """Algorithm to balance teams based on player custom MMR."""
    
    @staticmethod
    def generate_balanced_teams(players: List[PlayerInfo]) -> tuple[Team, Team]:
        """
        Generate two balanced teams from a list of players.
        
        Algorithm:
        1. Generate all 252 possible combinations of 5 players (C(10,5) = 252)
        2. For each combination, calculate the MMR difference between teams
        3. Find the top 20 most balanced combinations
        4. Randomly select one from the top 20
        
        This ensures balanced teams based on custom MMR while adding variety.
        
        Args:
            players: List of 10 players with custom MMR values
            
        Returns:
            Tuple of (team1, team2)
            
        Raises:
            ValueError: If not exactly 10 players
        """
        if len(players) != 10:
            raise ValueError(f"Expected exactly 10 players, got {len(players)}")
        
        # Generate all possible combinations of 5 players for team1
        all_combinations = []
        
        for team1_indices in combinations(range(10), 5):
            # Team1 players
            team1_players = [players[i] for i in team1_indices]
            team1_total_mmr = sum(p.custom_mmr for p in team1_players)
            
            # Team2 players (remaining players)
            team2_indices = [i for i in range(10) if i not in team1_indices]
            team2_players = [players[i] for i in team2_indices]
            team2_total_mmr = sum(p.custom_mmr for p in team2_players)
            
            # Calculate MMR difference (how balanced the teams are)
            mmr_difference = abs(team1_total_mmr - team2_total_mmr)
            
            all_combinations.append({
                'team1_players': team1_players,
                'team1_total': team1_total_mmr,
                'team2_players': team2_players,
                'team2_total': team2_total_mmr,
                'tier_difference': mmr_difference  # Keep name for compatibility
            })
        
        # Sort by MMR difference (most balanced first)
        all_combinations.sort(key=lambda x: x['tier_difference'])
        
        # Take the top 20 most balanced combinations
        top_20_combinations = all_combinations[:20]
        
        # Randomly select one from the top 20
        selected = random.choice(top_20_combinations)
        
        # Create Team objects (total_tier_value kept for compatibility, but represents total MMR)
        team1 = Team(
            players=selected['team1_players'],
            total_tier_value=selected['team1_total']
        )
        team2 = Team(
            players=selected['team2_players'],
            total_tier_value=selected['team2_total']
        )
        
        return team1, team2
    
    @staticmethod
    def calculate_tier_difference(team1: Team, team2: Team) -> int:
        """Calculate the absolute difference in tier values between teams."""
        return abs(team1.total_tier_value - team2.total_tier_value)

