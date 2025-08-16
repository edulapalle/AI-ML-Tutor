-- Supabase Table Setup for Vercel YouTube Monitoring
-- Run this SQL in your Supabase SQL Editor

-- Create table to track processed YouTube videos (replaces processed_videos.json)
CREATE TABLE IF NOT EXISTS public.youtube_processed_videos (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    video_id text NOT NULL,
    processed_at timestamp with time zone DEFAULT now() NOT NULL,
    status text DEFAULT 'completed' NOT NULL,
    title text,
    channel text DEFAULT 'StatQuest with Josh Starmer',
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT youtube_processed_videos_pkey PRIMARY KEY (id),
    CONSTRAINT youtube_processed_videos_video_id_key UNIQUE (video_id)
);

-- Enable Row Level Security
ALTER TABLE public.youtube_processed_videos ENABLE ROW LEVEL SECURITY;

-- Create policies for authenticated users
CREATE POLICY "Enable read access for authenticated users" ON public.youtube_processed_videos
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "Enable insert for authenticated users" ON public.youtube_processed_videos
    FOR INSERT TO authenticated WITH CHECK (true);

CREATE POLICY "Enable update for authenticated users" ON public.youtube_processed_videos
    FOR UPDATE TO authenticated USING (true) WITH CHECK (true);

-- Create index for performance
CREATE INDEX IF NOT EXISTS youtube_processed_videos_video_id_idx ON public.youtube_processed_videos(video_id);
CREATE INDEX IF NOT EXISTS youtube_processed_videos_processed_at_idx ON public.youtube_processed_videos(processed_at);

-- Insert comment for documentation
COMMENT ON TABLE public.youtube_processed_videos IS 'Tracks YouTube videos that have been processed by the real-time monitoring system';
COMMENT ON COLUMN public.youtube_processed_videos.video_id IS 'YouTube video ID (e.g., qPN_XZcJf_s)';
COMMENT ON COLUMN public.youtube_processed_videos.status IS 'Processing status: completed, failed, processing';
COMMENT ON COLUMN public.youtube_processed_videos.processed_at IS 'When the video was successfully processed';
