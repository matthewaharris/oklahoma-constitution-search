-- Add missing columns to statutes table for better document support
-- Run this in Supabase SQL Editor

-- Add document_type if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'statutes' AND column_name = 'document_type'
    ) THEN
        ALTER TABLE statutes ADD COLUMN document_type VARCHAR(20) DEFAULT 'statute' CHECK (document_type IN ('statute', 'constitution'));
        CREATE INDEX idx_statutes_document_type ON statutes(document_type);
    END IF;
END $$;

-- Add article columns for constitution if they don't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'statutes' AND column_name = 'article_number'
    ) THEN
        ALTER TABLE statutes ADD COLUMN article_number VARCHAR(10);
        ALTER TABLE statutes ADD COLUMN article_name TEXT;
        CREATE INDEX idx_statutes_article ON statutes(article_number) WHERE document_type = 'constitution';
    END IF;
END $$;

COMMENT ON COLUMN statutes.document_type IS 'Type: statute or constitution';
COMMENT ON COLUMN statutes.article_number IS 'Article number (for constitution)';
COMMENT ON COLUMN statutes.article_name IS 'Article name (for constitution)';

-- All done!
SELECT 'Schema update complete!' as status;
