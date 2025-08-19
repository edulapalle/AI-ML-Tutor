-- Clean Database Schema for AI/ML Educational Platform
-- This reflects the cleaned-up production schema with only actively used tables

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ===============================================
-- ACTIVE TABLES (USED BY APPLICATION)
-- ===============================================

-- Users table for storing user information and study preferences
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    date_of_birth DATE NOT NULL,
    topics_of_interest JSONB NOT NULL DEFAULT '[]',
    current_stage VARCHAR(50) NOT NULL,
    current_goals JSONB NOT NULL DEFAULT '[]',  -- Used instead of learning_goals table
    study_level VARCHAR(20) NOT NULL,
    preferred_learning_style VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE
);

-- User learning path table for tracking explored topics
CREATE TABLE IF NOT EXISTS user_learning_path (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    topic VARCHAR(100) NOT NULL,
    explored_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Chat history table for storing conversation data (used by agentic system)
CREATE TABLE IF NOT EXISTS chat_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID DEFAULT NULL,  -- Optional field, not used currently
    message_content TEXT NOT NULL,
    message_role VARCHAR(20) NOT NULL, -- 'user' or 'assistant'
    message_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    topics_mentioned JSONB DEFAULT '[]',
    response_quality INTEGER -- 1-5 rating for response quality
);

-- Progress tracking table for monitoring learning progress
CREATE TABLE IF NOT EXISTS progress_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    topic VARCHAR(100) NOT NULL,
    proficiency_level INTEGER DEFAULT 1, -- 1-5 scale
    time_spent_minutes INTEGER DEFAULT 0,
    last_studied TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User stars table for bookmarked content
CREATE TABLE IF NOT EXISTS user_stars (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    doc_id VARCHAR(100) NOT NULL,
    note TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- YouTube processed videos table (used by data ingestion pipeline)
CREATE TABLE IF NOT EXISTS youtube_processed_videos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    video_id VARCHAR(20) UNIQUE NOT NULL,
    title TEXT NOT NULL,
    channel_name VARCHAR(255) NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    embedding_status VARCHAR(20) DEFAULT 'pending',
    knowledge_graph_status VARCHAR(20) DEFAULT 'pending'
);

-- ===============================================
-- INDEXES FOR PERFORMANCE
-- ===============================================

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_user_learning_path_user_id ON user_learning_path(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON chat_history(user_id);
CREATE INDEX IF NOT EXISTS idx_progress_tracking_user_id ON progress_tracking(user_id);
CREATE INDEX IF NOT EXISTS idx_user_stars_user_id ON user_stars(user_id);
CREATE INDEX IF NOT EXISTS idx_youtube_processed_videos_video_id ON youtube_processed_videos(video_id);

-- ===============================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ===============================================

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_learning_path ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE progress_tracking ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_stars ENABLE ROW LEVEL SECURITY;
ALTER TABLE youtube_processed_videos ENABLE ROW LEVEL SECURITY;

-- Users table policies
CREATE POLICY "Users can view own profile" ON users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (auth.uid() = id);

-- User learning path policies
CREATE POLICY "Users can view own learning path" ON user_learning_path
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own learning path" ON user_learning_path
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Chat history policies
CREATE POLICY "Users can view own chat history" ON chat_history
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own chat history" ON chat_history
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Progress tracking policies
CREATE POLICY "Users can view own progress" ON progress_tracking
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own progress" ON progress_tracking
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own progress" ON progress_tracking
    FOR UPDATE USING (auth.uid() = user_id);

-- User stars policies
CREATE POLICY "Users can view own stars" ON user_stars
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own stars" ON user_stars
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own stars" ON user_stars
    FOR DELETE USING (auth.uid() = user_id);

-- YouTube processed videos policies (admin access)
CREATE POLICY "Admin can manage youtube videos" ON youtube_processed_videos
    FOR ALL USING (auth.role() = 'service_role');

-- ===============================================
-- NOTES
-- ===============================================

-- This schema includes only tables actively used by the application:
-- 1. users - Core user management with JSONB goals
-- 2. user_learning_path - Learning topic exploration tracking  
-- 3. chat_history - Conversation data for agentic analysis
-- 4. progress_tracking - Learning proficiency and time tracking
-- 5. user_stars - Bookmark/favorites functionality
-- 6. youtube_processed_videos - Data pipeline tracking

-- Removed unused tables:
-- - learning_goals (replaced by users.current_goals JSONB)
-- - study_materials (not implemented)
-- - study_sessions (not used, session_id in chat_history is NULL)
