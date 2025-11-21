-- Oklahoma Statutes Database Schema for Supabase
-- This schema is designed to store scraped Oklahoma statute data

-- Enable UUID extension for better primary keys
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Main statutes table
CREATE TABLE statutes (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    cite_id VARCHAR(20) NOT NULL UNIQUE, -- OSCN cite ID (e.g., '440462')
    url TEXT NOT NULL,

    -- Metadata fields
    title_number VARCHAR(10),
    title_name TEXT,
    chapter_number VARCHAR(10),
    chapter_name TEXT,
    article_number VARCHAR(10),
    article_name TEXT,
    section_number VARCHAR(20),
    section_name TEXT,
    page_title TEXT,
    title_bar TEXT,
    citation_format TEXT,

    -- Content fields
    main_text TEXT, -- Full statute text
    full_json JSONB, -- Complete scraped data as JSON for flexibility

    -- Tracking fields
    scraped_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    scraper_version VARCHAR(20),

    -- Indexing
    CONSTRAINT valid_cite_id CHECK (cite_id ~ '^[0-9]+$')
);

-- Statute paragraphs table (for structured text access)
CREATE TABLE statute_paragraphs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    statute_id UUID NOT NULL REFERENCES statutes(id) ON DELETE CASCADE,
    paragraph_number INTEGER NOT NULL,
    text TEXT NOT NULL,
    is_historical BOOLEAN DEFAULT FALSE,

    -- Ensure unique paragraph numbers per statute
    CONSTRAINT unique_paragraph_per_statute UNIQUE (statute_id, paragraph_number)
);

-- Definitions table (for statutes that define terms)
CREATE TABLE statute_definitions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    statute_id UUID NOT NULL REFERENCES statutes(id) ON DELETE CASCADE,
    definition_number VARCHAR(10) NOT NULL, -- Could be "1", "a", "i", etc.
    term TEXT NOT NULL,
    definition TEXT NOT NULL,

    -- Ensure unique definition numbers per statute
    CONSTRAINT unique_definition_per_statute UNIQUE (statute_id, definition_number)
);

-- Legislative history table
CREATE TABLE legislative_history (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    statute_id UUID NOT NULL REFERENCES statutes(id) ON DELETE CASCADE,
    year INTEGER NOT NULL,
    bill_type VARCHAR(10), -- 'HB', 'SB', etc.
    bill_number VARCHAR(20),
    details TEXT,
    effective_date TEXT -- Store as text since dates can be complex ("July 1, 2004", "emergency effective", etc.)
);

-- Citations and cross-references table
CREATE TABLE statute_citations (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    statute_id UUID NOT NULL REFERENCES statutes(id) ON DELETE CASCADE,
    cited_statute_cite_id VARCHAR(20), -- Reference to another statute's cite_id
    citation_text TEXT NOT NULL,
    citation_name TEXT,
    citation_level TEXT, -- 'Cited', 'Referenced', etc.
    href TEXT -- Original link from OSCN
);

-- Superseded documents table
CREATE TABLE superseded_documents (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    statute_id UUID NOT NULL REFERENCES statutes(id) ON DELETE CASCADE,
    superseded_cite_id VARCHAR(20),
    text TEXT,
    href TEXT
);

-- Create indexes for better query performance
CREATE INDEX idx_statutes_cite_id ON statutes(cite_id);
CREATE INDEX idx_statutes_title_chapter_section ON statutes(title_number, chapter_number, section_number);
CREATE INDEX idx_statutes_title_name ON statutes(title_name);
CREATE INDEX idx_statutes_scraped_at ON statutes(scraped_at);

-- Full-text search index on statute content
CREATE INDEX idx_statutes_main_text_fts ON statutes USING gin(to_tsvector('english', main_text));
CREATE INDEX idx_statute_paragraphs_text_fts ON statute_paragraphs USING gin(to_tsvector('english', text));
CREATE INDEX idx_definitions_term_fts ON statute_definitions USING gin(to_tsvector('english', term || ' ' || definition));

-- Indexes for foreign key relationships
CREATE INDEX idx_paragraphs_statute_id ON statute_paragraphs(statute_id);
CREATE INDEX idx_definitions_statute_id ON statute_definitions(statute_id);
CREATE INDEX idx_legislative_history_statute_id ON legislative_history(statute_id);
CREATE INDEX idx_citations_statute_id ON statute_citations(statute_id);
CREATE INDEX idx_citations_cited_statute ON statute_citations(cited_statute_cite_id);

-- Update trigger for updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_statutes_updated_at
    BEFORE UPDATE ON statutes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Views for common queries
CREATE VIEW statutes_summary AS
SELECT
    cite_id,
    title_number,
    title_name,
    chapter_number,
    chapter_name,
    article_number,
    article_name,
    section_number,
    section_name,
    scraped_at,
    CASE
        WHEN main_text IS NOT NULL THEN LENGTH(main_text)
        ELSE 0
    END as text_length
FROM statutes;

-- View for statutes with definitions
CREATE VIEW statutes_with_definitions AS
SELECT
    s.cite_id,
    s.title_number,
    s.chapter_number,
    s.section_number,
    s.section_name,
    COUNT(d.id) as definition_count,
    string_agg(d.term, '; ' ORDER BY d.definition_number) as defined_terms
FROM statutes s
JOIN statute_definitions d ON s.id = d.statute_id
GROUP BY s.id, s.cite_id, s.title_number, s.chapter_number, s.section_number, s.section_name;

-- Row Level Security (RLS) policies
ALTER TABLE statutes ENABLE ROW LEVEL SECURITY;
ALTER TABLE statute_paragraphs ENABLE ROW LEVEL SECURITY;
ALTER TABLE statute_definitions ENABLE ROW LEVEL SECURITY;
ALTER TABLE legislative_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE statute_citations ENABLE ROW LEVEL SECURITY;
ALTER TABLE superseded_documents ENABLE ROW LEVEL SECURITY;

-- Basic read policy (adjust based on your security requirements)
CREATE POLICY "Enable read access for all users" ON statutes FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON statute_paragraphs FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON statute_definitions FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON legislative_history FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON statute_citations FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON superseded_documents FOR SELECT USING (true);

-- Insert/Update policies (adjust based on your security requirements)
-- These allow authenticated users to insert/update data
CREATE POLICY "Enable insert for authenticated users" ON statutes FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "Enable update for authenticated users" ON statutes FOR UPDATE TO authenticated USING (true);

CREATE POLICY "Enable insert for authenticated users" ON statute_paragraphs FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "Enable insert for authenticated users" ON statute_definitions FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "Enable insert for authenticated users" ON legislative_history FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "Enable insert for authenticated users" ON statute_citations FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "Enable insert for authenticated users" ON superseded_documents FOR INSERT TO authenticated WITH CHECK (true);

-- Comments for documentation
COMMENT ON TABLE statutes IS 'Main table storing Oklahoma statute information';
COMMENT ON COLUMN statutes.cite_id IS 'OSCN unique identifier for the statute';
COMMENT ON COLUMN statutes.full_json IS 'Complete scraped data in JSON format for flexibility';
COMMENT ON TABLE statute_definitions IS 'Definitions found within statutes (common in legal documents)';
COMMENT ON TABLE legislative_history IS 'Legislative history and amendments for each statute';
COMMENT ON VIEW statutes_summary IS 'Quick overview of all statutes without full content';