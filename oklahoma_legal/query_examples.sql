-- SQL Queries to view your stored Oklahoma statute data
-- Run these in your Supabase SQL Editor

-- 1. Overview of all statutes
SELECT
    cite_id,
    title_number,
    title_name,
    chapter_number,
    chapter_name,
    section_number,
    section_name,
    scraped_at,
    LENGTH(main_text) as text_length
FROM statutes
ORDER BY title_number, chapter_number, section_number;

-- 2. View the full statute with metadata (statute 440462)
SELECT
    cite_id,
    url,
    title_number || '.' || chapter_number || '.' || section_number as statute_reference,
    section_name,
    page_title,
    citation_format,
    LEFT(main_text, 200) || '...' as text_preview,
    scraped_at
FROM statutes
WHERE cite_id = '440462';

-- 3. View all definitions for a statute
SELECT
    s.cite_id,
    s.section_name,
    d.definition_number,
    d.term,
    LEFT(d.definition, 100) || '...' as definition_preview
FROM statutes s
JOIN statute_definitions d ON s.id = d.statute_id
WHERE s.cite_id = '440462'
ORDER BY d.definition_number;

-- 4. View paragraphs of a statute
SELECT
    s.cite_id,
    p.paragraph_number,
    p.is_historical,
    LEFT(p.text, 150) || '...' as paragraph_preview
FROM statutes s
JOIN statute_paragraphs p ON s.id = p.statute_id
WHERE s.cite_id = '440462'
ORDER BY p.paragraph_number;

-- 5. View legislative history
SELECT
    s.cite_id,
    lh.year,
    lh.bill_type,
    lh.bill_number,
    lh.details,
    lh.effective_date
FROM statutes s
JOIN legislative_history lh ON s.id = lh.statute_id
WHERE s.cite_id = '440462'
ORDER BY lh.year;

-- 6. View citations and references
SELECT
    s.cite_id as statute,
    c.citation_text,
    c.citation_name,
    c.citation_level,
    c.href
FROM statutes s
JOIN statute_citations c ON s.id = c.statute_id
WHERE s.cite_id = '440462';

-- 7. Full statute view with all related data
SELECT
    'MAIN' as section,
    s.cite_id,
    s.title_number || ' - ' || s.title_name as title,
    s.chapter_number || ' - ' || s.chapter_name as chapter,
    s.section_number || ' - ' || s.section_name as section_info,
    s.main_text as content
FROM statutes s
WHERE s.cite_id = '440462'

UNION ALL

SELECT
    'DEFINITIONS' as section,
    s.cite_id,
    d.definition_number as title,
    d.term as chapter,
    NULL as section_info,
    d.definition as content
FROM statutes s
JOIN statute_definitions d ON s.id = d.statute_id
WHERE s.cite_id = '440462'

UNION ALL

SELECT
    'LEGISLATIVE HISTORY' as section,
    s.cite_id,
    lh.year::text as title,
    lh.bill_type || ' ' || lh.bill_number as chapter,
    lh.effective_date as section_info,
    lh.details as content
FROM statutes s
JOIN legislative_history lh ON s.id = lh.statute_id
WHERE s.cite_id = '440462'

ORDER BY section, title;

-- 8. Database statistics
SELECT 'Total Statutes' as metric, COUNT(*)::text as value FROM statutes
UNION ALL
SELECT 'Total Definitions', COUNT(*)::text FROM statute_definitions
UNION ALL
SELECT 'Total Paragraphs', COUNT(*)::text FROM statute_paragraphs
UNION ALL
SELECT 'Total Legislative History Entries', COUNT(*)::text FROM legislative_history
UNION ALL
SELECT 'Total Citations', COUNT(*)::text FROM statute_citations;

-- 9. Search for statutes containing specific terms
-- Example: Search for statutes mentioning "investment"
SELECT
    cite_id,
    section_name,
    ts_rank(to_tsvector('english', main_text), plainto_tsquery('english', 'investment')) as relevance
FROM statutes
WHERE to_tsvector('english', main_text) @@ plainto_tsquery('english', 'investment')
ORDER BY relevance DESC;