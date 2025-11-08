"""MMR calculation service using ELO-style rating system."""
from typing import Tuple


class MMRCalculator:
    """Calculate MMR changes based on match results using ELO algorithm."""
    
    # K-factor: determines how much MMR changes per game
    # Higher K = bigger swings, lower K = more stable
    K_FACTOR = 32
    
    @staticmethod
    def calculate_expected_score(team_avg_mmr: float, opponent_avg_mmr: float) -> float:
        """
        Calculate expected score (win probability) for a team.
        
        Uses the ELO formula: E = 1 / (1 + 10^((opponent_rating - team_rating) / 400))
        
        Args:
            team_avg_mmr: Average MMR of the team
            opponent_avg_mmr: Average MMR of the opponent team
            
        Returns:
            Expected score between 0 and 1 (probability of winning)
        """
        return 1 / (1 + 10 ** ((opponent_avg_mmr - team_avg_mmr) / 400))
    
    @staticmethod
    def calculate_mmr_change(
        team_avg_mmr: float,
        opponent_avg_mmr: float,
        actual_score: float
    ) -> int:
        """
        Calculate MMR change for a team based on match result.
        
        Args:
            team_avg_mmr: Average MMR of the team
            opponent_avg_mmr: Average MMR of the opponent team
            actual_score: Actual score (1 for win, 0 for loss)
            
        Returns:
            MMR change as integer (positive for gain, negative for loss)
        """
        expected_score = MMRCalculator.calculate_expected_score(
            team_avg_mmr,
            opponent_avg_mmr
        )
        
        # ELO formula: New Rating = Old Rating + K * (Actual - Expected)
        mmr_change = MMRCalculator.K_FACTOR * (actual_score - expected_score)
        
        return round(mmr_change)
    
    @staticmethod
    def calculate_team_mmr_changes(
        team1_mmrs: list[int],
        team2_mmrs: list[int],
        winning_team: int
    ) -> Tuple[dict[str, int], int]:
        """
        Calculate MMR changes for all players in a match.
        
        Args:
            team1_mmrs: List of MMRs for team 1 players
            team2_mmrs: List of MMRs for team 2 players
            winning_team: 1 if team 1 won, 2 if team 2 won
            
        Returns:
            Tuple of (mmr_changes_dict, mmr_change_amount)
            - mmr_changes_dict: Maps player index to MMR change
            - mmr_change_amount: Absolute MMR change value
        """
        team1_avg = sum(team1_mmrs) / len(team1_mmrs)
        team2_avg = sum(team2_mmrs) / len(team2_mmrs)
        
        # Calculate MMR change for team 1
        team1_actual_score = 1.0 if winning_team == 1 else 0.0
        team1_mmr_change = MMRCalculator.calculate_mmr_change(
            team1_avg,
            team2_avg,
            team1_actual_score
        )
        
        # Team 2's change is opposite of team 1
        team2_mmr_change = -team1_mmr_change
        
        # Build result dictionary
        mmr_changes = {}
        for i in range(len(team1_mmrs)):
            mmr_changes[f"team1_{i}"] = team1_mmr_change
        for i in range(len(team2_mmrs)):
            mmr_changes[f"team2_{i}"] = team2_mmr_change
        
        return mmr_changes, abs(team1_mmr_change)

