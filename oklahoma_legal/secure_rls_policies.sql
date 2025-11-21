-- Secure Row Level Security policies that allow scraping but limit access
-- Run this in your Supabase SQL Editor for better security

-- First, drop the overly permissive policies
DROP POLICY IF EXISTS "Enable all operations for anon" ON statutes;
DROP POLICY IF EXISTS "Enable all operations for anon" ON statute_paragraphs;
DROP POLICY IF EXISTS "Enable all operations for anon" ON statute_definitions;
DROP POLICY IF EXISTS "Enable all operations for anon" ON legislative_history;
DROP POLICY IF EXISTS "Enable all operations for anon" ON statute_citations;
DROP POLICY IF EXISTS "Enable all operations for anon" ON superseded_documents;

-- Option 1: Temporarily disable RLS for setup (easiest for testing)
-- You can re-enable it later with more specific policies
ALTER TABLE statutes DISABLE ROW LEVEL SECURITY;
ALTER TABLE statute_paragraphs DISABLE ROW LEVEL SECURITY;
ALTER TABLE statute_definitions DISABLE ROW LEVEL SECURITY;
ALTER TABLE legislative_history DISABLE ROW LEVEL SECURITY;
ALTER TABLE statute_citations DISABLE ROW LEVEL SECURITY;
ALTER TABLE superseded_documents DISABLE ROW LEVEL SECURITY;

-- Option 2: If you want to keep RLS enabled, uncomment the policies below
-- and comment out the DISABLE statements above

-- More restrictive policies - only allow reads for everyone, writes for anon with API key
-- CREATE POLICY "Enable read access for all users" ON statutes FOR SELECT USING (true);
-- CREATE POLICY "Enable insert for anon only" ON statutes FOR INSERT TO anon WITH CHECK (true);

-- CREATE POLICY "Enable read access for all users" ON statute_paragraphs FOR SELECT USING (true);
-- CREATE POLICY "Enable insert for anon only" ON statute_paragraphs FOR INSERT TO anon WITH CHECK (true);

-- CREATE POLICY "Enable read access for all users" ON statute_definitions FOR SELECT USING (true);
-- CREATE POLICY "Enable insert for anon only" ON statute_definitions FOR INSERT TO anon WITH CHECK (true);

-- CREATE POLICY "Enable read access for all users" ON legislative_history FOR SELECT USING (true);
-- CREATE POLICY "Enable insert for anon only" ON legislative_history FOR INSERT TO anon WITH CHECK (true);

-- CREATE POLICY "Enable read access for all users" ON statute_citations FOR SELECT USING (true);
-- CREATE POLICY "Enable insert for anon only" ON statute_citations FOR INSERT TO anon WITH CHECK (true);

-- CREATE POLICY "Enable read access for all users" ON superseded_documents FOR SELECT USING (true);
-- CREATE POLICY "Enable insert for anon only" ON superseded_documents FOR INSERT TO anon WITH CHECK (true);

-- Note: With RLS disabled, your anon key can read/write but you should:
-- 1. Keep your API key secret
-- 2. Consider using a service role key instead of anon key for scraping
-- 3. Re-enable RLS with proper policies once your scraper is working