-- Oklahoma Case Law & AG Opinions Database Schema
-- Run this in Supabase SQL Editor

-- ============================================================================
-- TABLE: oklahoma_cases
-- Stores Oklahoma court cases from Supreme Court, Criminal Appeals,
-- Civil Appeals, and Court on the Judiciary
-- ============================================================================

CREATE TABLE IF NOT EXISTS oklahoma_cases (
    id BIGSERIAL PRIMARY KEY,

    -- Case Identification
    cite_id TEXT UNIQUE NOT NULL,           -- OSCN CiteID (e.g., "547774")
    citation TEXT NOT NULL,                  -- Official citation (e.g., "2025 OK 2, 562 P.3d 1085")
    case_number TEXT,                        -- Docket number (e.g., "121688")

    -- Court Information
    court_type TEXT NOT NULL CHECK (court_type IN ('supreme_court', 'criminal_appeals', 'civil_appeals', 'court_on_judiciary')),
    court_database TEXT NOT NULL,            -- Database code (e.g., "STOKCSSC")

    -- Date Information
    decision_date DATE NOT NULL,
    decision_year INTEGER NOT NULL,

    -- Parties
    case_title TEXT NOT NULL,                -- Full case title (e.g., "In re G.E.M.S.")
    appellant TEXT,                          -- Party appealing
    appellee TEXT,                           -- Opposing party
    other_parties TEXT[],                    -- Additional parties (array)

    -- Judges/Justices
    authoring_judge TEXT,                    -- Judge who wrote opinion
    concurring_judges TEXT[],                -- Judges who concurred (array)
    dissenting_judges TEXT[],                -- Judges who dissented (array)

    -- Opinion Content
    opinion_text TEXT NOT NULL,              -- Full opinion text
    syllabus TEXT,                           -- Headnotes/syllabus
    holdings TEXT[],                         -- Key holdings (array)

    -- Metadata
    opinion_type TEXT DEFAULT 'majority' CHECK (opinion_type IN ('majority', 'concurring', 'dissenting', 'per_curiam')),
    procedural_posture TEXT,                 -- "affirmed", "reversed", "remanded", etc.

    -- References
    statutes_cited TEXT[],                   -- Referenced statutes (array)
    cases_cited TEXT[],                      -- Referenced cases (array)

    -- URL
    oscn_url TEXT NOT NULL,                  -- Direct OSCN link

    -- Timestamps
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- INDEXES for oklahoma_cases
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_cases_citation ON oklahoma_cases(citation);
CREATE INDEX IF NOT EXISTS idx_cases_cite_id ON oklahoma_cases(cite_id);
CREATE INDEX IF NOT EXISTS idx_cases_decision_date ON oklahoma_cases(decision_date DESC);
CREATE INDEX IF NOT EXISTS idx_cases_decision_year ON oklahoma_cases(decision_year DESC);
CREATE INDEX IF NOT EXISTS idx_cases_court_type ON oklahoma_cases(court_type);
CREATE INDEX IF NOT EXISTS idx_cases_case_number ON oklahoma_cases(case_number);

-- Full-text search indexes
CREATE INDEX IF NOT EXISTS idx_cases_opinion_text_search
    ON oklahoma_cases USING gin(to_tsvector('english', opinion_text));
CREATE INDEX IF NOT EXISTS idx_cases_case_title_search
    ON oklahoma_cases USING gin(to_tsvector('english', case_title));

-- ============================================================================
-- TABLE: attorney_general_opinions
-- Stores Oklahoma Attorney General opinions (1977-present)
-- ============================================================================

CREATE TABLE IF NOT EXISTS attorney_general_opinions (
    id BIGSERIAL PRIMARY KEY,

    -- Opinion Identification
    cite_id TEXT UNIQUE NOT NULL,            -- OSCN CiteID
    citation TEXT NOT NULL,                   -- "2025 OK AG 3"
    opinion_number INTEGER NOT NULL,

    -- Date Information
    opinion_date DATE NOT NULL,
    opinion_year INTEGER NOT NULL,

    -- Requestor Information
    requestor_name TEXT NOT NULL,
    requestor_title TEXT,
    requestor_organization TEXT,

    -- Opinion Content
    opinion_text TEXT NOT NULL,
    question_presented TEXT,
    conclusion TEXT,

    -- References
    statutes_cited TEXT[],                   -- Referenced statutes (array)
    cases_cited TEXT[],                      -- Referenced cases (array)

    -- URL
    oscn_url TEXT NOT NULL,                  -- Direct OSCN link

    -- Timestamps
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- INDEXES for attorney_general_opinions
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_ag_citation ON attorney_general_opinions(citation);
CREATE INDEX IF NOT EXISTS idx_ag_cite_id ON attorney_general_opinions(cite_id);
CREATE INDEX IF NOT EXISTS idx_ag_opinion_date ON attorney_general_opinions(opinion_date DESC);
CREATE INDEX IF NOT EXISTS idx_ag_opinion_year ON attorney_general_opinions(opinion_year DESC);
CREATE INDEX IF NOT EXISTS idx_ag_opinion_number ON attorney_general_opinions(opinion_number);

-- Full-text search indexes
CREATE INDEX IF NOT EXISTS idx_ag_opinion_text_search
    ON attorney_general_opinions USING gin(to_tsvector('english', opinion_text));
CREATE INDEX IF NOT EXISTS idx_ag_requestor_search
    ON attorney_general_opinions USING gin(to_tsvector('english', requestor_name || ' ' || COALESCE(requestor_organization, '')));

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS on both tables
ALTER TABLE oklahoma_cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE attorney_general_opinions ENABLE ROW LEVEL SECURITY;

-- Policy: Allow service role full access (for admin operations)
CREATE POLICY "Allow service role full access to cases" ON oklahoma_cases
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Allow service role full access to AG opinions" ON attorney_general_opinions
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Policy: Allow anonymous users to read (for public search)
CREATE POLICY "Allow anonymous read access to cases" ON oklahoma_cases
    FOR SELECT
    TO anon
    USING (true);

CREATE POLICY "Allow anonymous read access to AG opinions" ON attorney_general_opinions
    FOR SELECT
    TO anon
    USING (true);

-- ============================================================================
-- GRANTS
-- ============================================================================

GRANT SELECT ON oklahoma_cases TO anon;
GRANT ALL ON oklahoma_cases TO service_role;

GRANT SELECT ON attorney_general_opinions TO anon;
GRANT ALL ON attorney_general_opinions TO service_role;

-- ============================================================================
-- COMMENTS (for documentation)
-- ============================================================================

COMMENT ON TABLE oklahoma_cases IS 'Oklahoma court cases from Supreme Court, Criminal Appeals, Civil Appeals, and Court on the Judiciary (2020-present for MVP)';
COMMENT ON TABLE attorney_general_opinions IS 'Oklahoma Attorney General opinions (1977-present)';

COMMENT ON COLUMN oklahoma_cases.cite_id IS 'Unique OSCN CiteID for direct document access';
COMMENT ON COLUMN oklahoma_cases.citation IS 'Official legal citation (e.g., "2025 OK 2, 562 P.3d 1085")';
COMMENT ON COLUMN oklahoma_cases.court_type IS 'Type of court: supreme_court, criminal_appeals, civil_appeals, court_on_judiciary';

COMMENT ON COLUMN attorney_general_opinions.cite_id IS 'Unique OSCN CiteID for direct document access';
COMMENT ON COLUMN attorney_general_opinions.citation IS 'Official AG opinion citation (e.g., "2025 OK AG 3")';

-- ============================================================================
-- VERIFICATION QUERIES
-- Run these after schema creation to verify
-- ============================================================================

-- Verify tables exist
-- SELECT table_name, table_type
-- FROM information_schema.tables
-- WHERE table_schema = 'public'
-- AND table_name IN ('oklahoma_cases', 'attorney_general_opinions');

-- Check indexes
-- SELECT indexname, indexdef
-- FROM pg_indexes
-- WHERE tablename IN ('oklahoma_cases', 'attorney_general_opinions');

-- Initial counts (should be 0)
-- SELECT COUNT(*) as cases_count FROM oklahoma_cases;
-- SELECT COUNT(*) as ag_opinions_count FROM attorney_general_opinions;
