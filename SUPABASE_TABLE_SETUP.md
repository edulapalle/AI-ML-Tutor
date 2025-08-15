# Supabase Learning Path Table Setup

The learning path feature requires a `user_learning_path` table in your Supabase database.

## Quick Setup

Go to your Supabase dashboard → SQL Editor and run this query:

```sql
-- Create user_learning_path table for dynamic learning paths
CREATE TABLE IF NOT EXISTS user_learning_path (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    topic VARCHAR(255) NOT NULL,
    explored_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Unique constraint to prevent duplicate topics per user
    UNIQUE(user_id, topic)
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_user_learning_path_user_id ON user_learning_path(user_id);
CREATE INDEX IF NOT EXISTS idx_user_learning_path_explored_at ON user_learning_path(explored_at DESC);
```

## What this table does:
- Tracks topics users have explored
- Builds personalized learning paths
- Prevents duplicate entries per user
- Orders by most recently explored

## Alternative: Manual table creation via UI:
1. Go to Supabase → Table Editor
2. Click "New table" 
3. Name: `user_learning_path`
4. Add columns:
   - `id` (int8, primary key, auto-increment)
   - `user_id` (uuid, not null)
   - `topic` (varchar, not null)
   - `explored_at` (timestamptz, default: now())
   - `created_at` (timestamptz, default: now())
5. Add unique constraint on (user_id, topic)

Once the table exists, the learning path feature will work automatically!
