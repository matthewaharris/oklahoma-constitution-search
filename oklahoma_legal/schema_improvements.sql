-- Schema improvements for Oklahoma legal documents
-- This adds support for both Constitution and Statutes in the same schema

-- Add document_type column to distinguish between statutes and constitution
ALTER TABLE statutes ADD COLUMN IF NOT EXISTS document_type VARCHAR(20) DEFAULT 'statute' CHECK (document_type IN ('statute', 'constitution'));

-- Add article fields for constitution documents
ALTER TABLE statutes ADD COLUMN IF NOT EXISTS article_number VARCHAR(10);
ALTER TABLE statutes ADD COLUMN IF NOT EXISTS article_name TEXT;

-- Add index for document type filtering
CREATE INDEX IF NOT EXISTS idx_statutes_document_type ON statutes(document_type);

-- Add index for constitution articles
CREATE INDEX IF NOT EXISTS idx_statutes_article ON statutes(article_number) WHERE document_type = 'constitution';

-- Create a view for constitution documents
CREATE OR REPLACE VIEW constitution_documents AS
SELECT
    cite_id,
    article_number,
    article_name,
    section_number,
    section_name,
    page_title,
    main_text,
    scraped_at
FROM statutes
WHERE document_type = 'constitution';

-- Create a view for statute documents
CREATE OR REPLACE VIEW statute_documents AS
SELECT
    cite_id,
    title_number,
    title_name,
    chapter_number,
    chapter_name,
    section_number,
    section_name,
    page_title,
    main_text,
    scraped_at
FROM statutes
WHERE document_type = 'statute';

-- Update the summary view to include document type
DROP VIEW IF EXISTS statutes_summary;
CREATE VIEW statutes_summary AS
SELECT
    cite_id,
    document_type,
    title_number,
    title_name,
    article_number,
    article_name,
    chapter_number,
    chapter_name,
    section_number,
    section_name,
    scraped_at,
    CASE
        WHEN main_text IS NOT NULL THEN LENGTH(main_text)
        ELSE 0
    END as text_length
FROM statutes;

-- Add comments
COMMENT ON COLUMN statutes.document_type IS 'Type of legal document: statute or constitution';
COMMENT ON COLUMN statutes.article_number IS 'Article number (for constitution documents)';
COMMENT ON COLUMN statutes.article_name IS 'Article name (for constitution documents)';
COMMENT ON VIEW constitution_documents IS 'All Oklahoma Constitution documents';
COMMENT ON VIEW statute_documents IS 'All Oklahoma Statute documents';
