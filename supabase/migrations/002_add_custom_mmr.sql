-- Add custom_mmr column to users table
-- Default MMR is 1000 (standard ELO starting point)
ALTER TABLE users
ADD COLUMN custom_mmr INTEGER NOT NULL DEFAULT 1000;

-- Update existing users with MMR based on their current tier
-- Each tier = 100 points, each division = 25 points (matching ~100 LP per division in League)
UPDATE users u
SET custom_mmr = CASE
    WHEN la.highest_tier IS NULL THEN 1000
    WHEN la.highest_tier = 'IRON' THEN 
        CASE 
            WHEN la.highest_rank = 'I' THEN 1 * 100 + 75
            WHEN la.highest_rank = 'II' THEN 1 * 100 + 50
            WHEN la.highest_rank = 'III' THEN 1 * 100 + 25
            WHEN la.highest_rank = 'IV' THEN 1 * 100 + 0
            ELSE 1 * 100
        END
    WHEN la.highest_tier = 'BRONZE' THEN 
        CASE 
            WHEN la.highest_rank = 'I' THEN 2 * 100 + 75
            WHEN la.highest_rank = 'II' THEN 2 * 100 + 50
            WHEN la.highest_rank = 'III' THEN 2 * 100 + 25
            WHEN la.highest_rank = 'IV' THEN 2 * 100 + 0
            ELSE 2 * 100
        END
    WHEN la.highest_tier = 'SILVER' THEN 
        CASE 
            WHEN la.highest_rank = 'I' THEN 3 * 100 + 75
            WHEN la.highest_rank = 'II' THEN 3 * 100 + 50
            WHEN la.highest_rank = 'III' THEN 3 * 100 + 25
            WHEN la.highest_rank = 'IV' THEN 3 * 100 + 0
            ELSE 3 * 100
        END
    WHEN la.highest_tier = 'GOLD' THEN 
        CASE 
            WHEN la.highest_rank = 'I' THEN 4 * 100 + 75
            WHEN la.highest_rank = 'II' THEN 4 * 100 + 50
            WHEN la.highest_rank = 'III' THEN 4 * 100 + 25
            WHEN la.highest_rank = 'IV' THEN 4 * 100 + 0
            ELSE 4 * 100
        END
    WHEN la.highest_tier = 'PLATINUM' THEN 
        CASE 
            WHEN la.highest_rank = 'I' THEN 5 * 100 + 75
            WHEN la.highest_rank = 'II' THEN 5 * 100 + 50
            WHEN la.highest_rank = 'III' THEN 5 * 100 + 25
            WHEN la.highest_rank = 'IV' THEN 5 * 100 + 0
            ELSE 5 * 100
        END
    WHEN la.highest_tier = 'EMERALD' THEN 
        CASE 
            WHEN la.highest_rank = 'I' THEN 6 * 100 + 75
            WHEN la.highest_rank = 'II' THEN 6 * 100 + 50
            WHEN la.highest_rank = 'III' THEN 6 * 100 + 25
            WHEN la.highest_rank = 'IV' THEN 6 * 100 + 0
            ELSE 6 * 100
        END
    WHEN la.highest_tier = 'DIAMOND' THEN 
        CASE 
            WHEN la.highest_rank = 'I' THEN 7 * 100 + 75
            WHEN la.highest_rank = 'II' THEN 7 * 100 + 50
            WHEN la.highest_rank = 'III' THEN 7 * 100 + 25
            WHEN la.highest_rank = 'IV' THEN 7 * 100 + 0
            ELSE 7 * 100
        END
    WHEN la.highest_tier = 'MASTER' THEN 8 * 100
    WHEN la.highest_tier = 'GRANDMASTER' THEN 9 * 100
    WHEN la.highest_tier = 'CHALLENGER' THEN 10 * 100
    ELSE 1000
END
FROM league_accounts la
WHERE u.discord_id = la.discord_id;

-- Create index for faster MMR queries
CREATE INDEX idx_users_custom_mmr ON users(custom_mmr DESC);

-- Create matches table to track match history
CREATE TABLE matches (
    id BIGSERIAL PRIMARY KEY,
    match_id TEXT UNIQUE,
    team1_player_ids TEXT[] NOT NULL,
    team2_player_ids TEXT[] NOT NULL,
    winning_team INTEGER NOT NULL CHECK (winning_team IN (1, 2)),
    team1_avg_mmr INTEGER NOT NULL,
    team2_avg_mmr INTEGER NOT NULL,
    mmr_change INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for match history queries
CREATE INDEX idx_matches_created_at ON matches(created_at DESC);
CREATE INDEX idx_matches_match_id ON matches(match_id);
CREATE INDEX idx_matches_players ON matches USING gin(team1_player_ids);
CREATE INDEX idx_matches_players2 ON matches USING gin(team2_player_ids);

-- Add comment
COMMENT ON COLUMN users.custom_mmr IS 'Custom MMR rating for team balancing, updated based on match results';
COMMENT ON TABLE matches IS 'Match history with MMR changes';

