"""Tier and rank utility functions for MMR calculation."""
from typing import Optional


# Tier ranking values (higher is better)
TIER_VALUES = {
    "IRON": 1,
    "BRONZE": 2,
    "SILVER": 3,
    "GOLD": 4,
    "PLATINUM": 5,
    "EMERALD": 6,
    "DIAMOND": 7,
    "MASTER": 8,
    "GRANDMASTER": 9,
    "CHALLENGER": 10,
}

# Rank values within tier (higher = better)
# Each rank = 1 unit, will be multiplied by 25 to get MMR bonus
RANK_VALUES = {
    "I": 3,    # +75 MMR (3 * 25)
    "II": 2,   # +50 MMR (2 * 25)
    "III": 1,  # +25 MMR (1 * 25)
    "IV": 0,   # +0 MMR (0 * 25)
}


def tier_to_value(tier: Optional[str], rank: Optional[str] = None) -> int:
    """
    Convert tier and rank to a numeric value for team balancing.
    
    Each tier = 100 points, each division = 25 points
    This matches League's ~100 LP per division structure.
    
    Master, Grandmaster, and Challenger have fixed values (no ranks).
    
    Args:
        tier: Tier name (e.g., "DIAMOND", "GOLD", "MASTER")
        rank: Rank within tier (e.g., "I", "II", "III", "IV") - ignored for Master+
        
    Returns:
        Numeric value representing skill level
    """
    if not tier:
        return 0
    
    tier_upper = tier.upper()
    
    # Master, Grandmaster, and Challenger have fixed values (no ranks)
    if tier_upper == "MASTER":
        return 800
    elif tier_upper == "GRANDMASTER":
        return 900
    elif tier_upper == "CHALLENGER":
        return 1000
    
    # For other tiers, calculate based on tier and rank
    tier_val = TIER_VALUES.get(tier_upper, 0)
    base_mmr = tier_val * 100  # Each tier = 100 points
    
    if rank:
        # Each division = 25 points (I=75, II=50, III=25, IV=0)
        rank_bonus = RANK_VALUES.get(rank.upper(), 0) * 25
        return base_mmr + rank_bonus
    
    return base_mmr

