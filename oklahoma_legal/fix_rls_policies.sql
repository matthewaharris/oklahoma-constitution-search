-- Fix Row Level Security policies for anon access
-- Run this in your Supabase SQL Editor to allow the scraper to insert data

-- Drop existing restrictive policies
DROP POLICY IF EXISTS "Enable insert for authenticated users" ON statutes;
DROP POLICY IF EXISTS "Enable update for authenticated users" ON statutes;
DROP POLICY IF EXISTS "Enable insert for authenticated users" ON statute_paragraphs;
DROP POLICY IF EXISTS "Enable insert for authenticated users" ON statute_definitions;
DROP POLICY IF EXISTS "Enable insert for authenticated users" ON legislative_history;
DROP POLICY IF EXISTS "Enable insert for authenticated users" ON statute_citations;
DROP POLICY IF EXISTS "Enable insert for authenticated users" ON superseded_documents;

-- Create permissive policies for anon role (for scraping)
-- You can make these more restrictive later if needed

-- Statutes table
CREATE POLICY "Enable all operations for anon" ON statutes FOR ALL TO anon USING (true) WITH CHECK (true);

-- Related tables
CREATE POLICY "Enable all operations for anon" ON statute_paragraphs FOR ALL TO anon USING (true) WITH CHECK (true);
CREATE POLICY "Enable all operations for anon" ON statute_definitions FOR ALL TO anon USING (true) WITH CHECK (true);
CREATE POLICY "Enable all operations for anon" ON legislative_history FOR ALL TO anon USING (true) WITH CHECK (true);
CREATE POLICY "Enable all operations for anon" ON statute_citations FOR ALL TO anon USING (true) WITH CHECK (true);
CREATE POLICY "Enable all operations for anon" ON superseded_documents FOR ALL TO anon USING (true) WITH CHECK (true);