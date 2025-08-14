-- Schema for user_stars table (for RAG Backend star functionality)
-- Run this in your Supabase SQL Editor

CREATE TABLE IF NOT EXISTS user_stars (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    doc_id TEXT NOT NULL,
    note TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(user_id, doc_id)
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_user_stars_user_id ON user_stars(user_id);
CREATE INDEX IF NOT EXISTS idx_user_stars_doc_id ON user_stars(doc_id);

-- Add RLS policy (if Row Level Security is enabled)
-- ALTER TABLE user_stars ENABLE ROW LEVEL SECURITY;

-- CREATE POLICY "Users can manage their own stars" ON user_stars
--     FOR ALL USING (auth.uid() = user_id);

-- Add updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_user_stars_updated_at 
    BEFORE UPDATE ON user_stars 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
