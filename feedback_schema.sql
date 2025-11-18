-- Feedback System Schema for Oklahoma Legal Search
-- Run this in Supabase SQL Editor

-- Table to store individual feedback events
CREATE TABLE IF NOT EXISTS user_feedback (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    question TEXT NOT NULL,
    answer_type TEXT NOT NULL CHECK (answer_type IN ('ask', 'search')),
    cite_ids TEXT[] NOT NULL,
    rating INTEGER NOT NULL CHECK (rating IN (-1, 1)),
    feedback_comment TEXT,
    model_used TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table to store aggregated document performance
CREATE TABLE IF NOT EXISTS document_performance (
    cite_id TEXT PRIMARY KEY,
    total_shown INTEGER DEFAULT 0,
    positive_feedback INTEGER DEFAULT 0,
    negative_feedback INTEGER DEFAULT 0,
    feedback_score FLOAT DEFAULT 0.0,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_user_feedback_cite_ids ON user_feedback USING GIN(cite_ids);
CREATE INDEX IF NOT EXISTS idx_user_feedback_created_at ON user_feedback(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_feedback_rating ON user_feedback(rating);
CREATE INDEX IF NOT EXISTS idx_document_performance_score ON document_performance(feedback_score DESC);
CREATE INDEX IF NOT EXISTS idx_document_performance_total ON document_performance(total_shown DESC);

-- Function to update document performance after feedback
CREATE OR REPLACE FUNCTION update_document_performance()
RETURNS TRIGGER AS $$
DECLARE
    cite_id_val TEXT;
BEGIN
    -- Loop through each cite_id in the array
    FOREACH cite_id_val IN ARRAY NEW.cite_ids
    LOOP
        -- Insert or update document performance
        INSERT INTO document_performance (cite_id, total_shown, positive_feedback, negative_feedback, feedback_score)
        VALUES (
            cite_id_val,
            1,
            CASE WHEN NEW.rating = 1 THEN 1 ELSE 0 END,
            CASE WHEN NEW.rating = -1 THEN 1 ELSE 0 END,
            CASE WHEN NEW.rating = 1 THEN 1.0 ELSE -1.0 END
        )
        ON CONFLICT (cite_id) DO UPDATE SET
            total_shown = document_performance.total_shown + 1,
            positive_feedback = document_performance.positive_feedback + CASE WHEN NEW.rating = 1 THEN 1 ELSE 0 END,
            negative_feedback = document_performance.negative_feedback + CASE WHEN NEW.rating = -1 THEN 1 ELSE 0 END,
            feedback_score = (
                (document_performance.positive_feedback + CASE WHEN NEW.rating = 1 THEN 1 ELSE 0 END)::FLOAT -
                (document_performance.negative_feedback + CASE WHEN NEW.rating = -1 THEN 1 ELSE 0 END)::FLOAT
            ) / (document_performance.total_shown + 1)::FLOAT,
            last_updated = NOW();
    END LOOP;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update document performance
DROP TRIGGER IF EXISTS trigger_update_document_performance ON user_feedback;
CREATE TRIGGER trigger_update_document_performance
    AFTER INSERT ON user_feedback
    FOR EACH ROW
    EXECUTE FUNCTION update_document_performance();

-- Enable Row Level Security (RLS)
ALTER TABLE user_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_performance ENABLE ROW LEVEL SECURITY;

-- Policy: Allow anonymous users to insert feedback
CREATE POLICY "Allow anonymous feedback insertion" ON user_feedback
    FOR INSERT
    TO anon
    WITH CHECK (true);

-- Policy: Allow service role to read all feedback
CREATE POLICY "Allow service role to read feedback" ON user_feedback
    FOR SELECT
    TO service_role
    USING (true);

-- Policy: Allow anyone to read document performance
CREATE POLICY "Allow read document performance" ON document_performance
    FOR SELECT
    TO anon, authenticated, service_role
    USING (true);

-- Policy: Allow service role to update document performance
CREATE POLICY "Allow service role to update performance" ON document_performance
    FOR ALL
    TO service_role
    USING (true);

-- Grant permissions
GRANT INSERT ON user_feedback TO anon;
GRANT SELECT ON user_feedback TO service_role;
GRANT SELECT ON document_performance TO anon, authenticated, service_role;
GRANT ALL ON document_performance TO service_role;

-- Comments for documentation
COMMENT ON TABLE user_feedback IS 'Stores individual user feedback events for answers and searches';
COMMENT ON TABLE document_performance IS 'Aggregated performance metrics for each document based on user feedback';
COMMENT ON COLUMN user_feedback.rating IS 'User rating: -1 for thumbs down, 1 for thumbs up';
COMMENT ON COLUMN document_performance.feedback_score IS 'Calculated as (positive - negative) / total_shown, ranges from -1 to 1';

-- Verification queries
-- SELECT COUNT(*) FROM user_feedback;
-- SELECT * FROM document_performance ORDER BY feedback_score DESC LIMIT 10;
-- SELECT * FROM document_performance ORDER BY total_shown DESC LIMIT 10;
