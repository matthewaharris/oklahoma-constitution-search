-- Add user_id column to conversation_sessions table to support authenticated users

-- Add user_id column (nullable to support anonymous users)
ALTER TABLE conversation_sessions
ADD COLUMN IF NOT EXISTS user_id TEXT DEFAULT NULL;

-- Add index for fast user lookups
CREATE INDEX IF NOT EXISTS idx_conversation_sessions_user_id
ON conversation_sessions(user_id);

-- Add comment
COMMENT ON COLUMN conversation_sessions.user_id IS 'Clerk user ID for authenticated users, NULL for anonymous users';

-- Verify the column was added
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'conversation_sessions'
ORDER BY ordinal_position;
