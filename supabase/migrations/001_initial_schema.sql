-- Create users table
CREATE TABLE IF NOT EXISTS users (
    discord_id TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create league_accounts table
CREATE TABLE IF NOT EXISTS league_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    discord_id TEXT NOT NULL REFERENCES users(discord_id) ON DELETE CASCADE,
    game_name TEXT NOT NULL,
    tag_line TEXT NOT NULL,
    puuid TEXT UNIQUE,
    highest_tier TEXT,
    highest_rank TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(discord_id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_league_accounts_discord_id ON league_accounts(discord_id);
CREATE INDEX IF NOT EXISTS idx_league_accounts_puuid ON league_accounts(puuid);

-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE league_accounts ENABLE ROW LEVEL SECURITY;

-- RLS Policies for users table
CREATE POLICY "Users can view their own data" ON users
    FOR SELECT USING (true);

CREATE POLICY "Users can insert their own data" ON users
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Users can update their own data" ON users
    FOR UPDATE USING (true);

-- RLS Policies for league_accounts table
CREATE POLICY "Users can view their own league accounts" ON league_accounts
    FOR SELECT USING (true);

CREATE POLICY "Users can insert their own league accounts" ON league_accounts
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Users can update their own league accounts" ON league_accounts
    FOR UPDATE USING (true);

