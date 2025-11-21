-- Conversation history schema for maintaining chat context

-- Table to store conversation sessions
CREATE TABLE IF NOT EXISTS conversation_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    user_ip TEXT,
    session_metadata JSONB DEFAULT '{}'::jsonb
);

-- Table to store individual messages in conversations
CREATE TABLE IF NOT EXISTS conversation_messages (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES conversation_sessions(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create index for fast retrieval by session
CREATE INDEX IF NOT EXISTS idx_messages_session_id
ON conversation_messages(session_id, created_at);

-- Add Row Level Security (RLS) policies
ALTER TABLE conversation_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_messages ENABLE ROW LEVEL SECURITY;

-- Allow anonymous access for now (you can tighten this later with auth)
CREATE POLICY "Allow all access to conversation_sessions"
ON conversation_sessions FOR ALL
USING (true);

CREATE POLICY "Allow all access to conversation_messages"
ON conversation_messages FOR ALL
USING (true);

-- Function to clean up old sessions (optional - run periodically)
CREATE OR REPLACE FUNCTION cleanup_old_sessions(days_old INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM conversation_sessions
    WHERE updated_at < NOW() - (days_old || ' days')::INTERVAL;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Example: Call this to clean up sessions older than 30 days
-- SELECT cleanup_old_sessions(30);
