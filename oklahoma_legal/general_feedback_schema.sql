-- General Feedback Schema for Feature Requests and User Feedback
-- Run this in Supabase SQL Editor

-- Table to store general user feedback and feature requests
CREATE TABLE IF NOT EXISTS general_feedback (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    feedback_type TEXT NOT NULL CHECK (feedback_type IN ('feature_request', 'bug_report', 'general_feedback', 'improvement')),
    subject TEXT NOT NULL,
    message TEXT NOT NULL,
    email TEXT,  -- Optional: for follow-up
    user_agent TEXT,  -- Browser/device info
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_general_feedback_type ON general_feedback(feedback_type);
CREATE INDEX IF NOT EXISTS idx_general_feedback_created_at ON general_feedback(created_at DESC);

-- Enable Row Level Security
ALTER TABLE general_feedback ENABLE ROW LEVEL SECURITY;

-- Policy: Allow anonymous users to insert feedback
CREATE POLICY "Allow anonymous general feedback insertion" ON general_feedback
    FOR INSERT
    TO anon
    WITH CHECK (true);

-- Policy: Allow service role to read all feedback
CREATE POLICY "Allow service role to read general feedback" ON general_feedback
    FOR SELECT
    TO service_role
    USING (true);

-- Grant permissions
GRANT INSERT ON general_feedback TO anon;
GRANT SELECT ON general_feedback TO service_role;

-- Comments for documentation
COMMENT ON TABLE general_feedback IS 'Stores general user feedback, feature requests, and bug reports';
COMMENT ON COLUMN general_feedback.feedback_type IS 'Type of feedback: feature_request, bug_report, general_feedback, or improvement';
COMMENT ON COLUMN general_feedback.email IS 'Optional email for follow-up communication';

-- Verification query
-- SELECT COUNT(*) FROM general_feedback;
-- SELECT feedback_type, COUNT(*) FROM general_feedback GROUP BY feedback_type;
