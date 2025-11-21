# OSCN Statute Parser - Schema Analysis Report

## Sample File Analyzed
**File**: `Statewide Centralized Hotline for Reporting Child Abuse or Neglect...html`
**CiteID**: 455989
**Citation**: 21 O.S. § 846by (also referenced as 10A O.S. § 1-2-101)

---

## Database Schema Field Mapping

### STATUTES TABLE (14 fields total)

#### Populated Fields (10 of 14) - 71% Coverage
1. **cite_id**: `"455989"` ✓
2. **url**: `"https://www.oscn.net/applications/oscn/DeliverDocument.asp?CiteID=455989"` ✓
3. **title_number**: `"21"` ✓
4. **chapter_number**: `"2"` ✓
5. **article_number**: `"1"` ✓
6. **section_number**: `"846by"` ✓
7. **section_name**: `"Statewide Centralized Hotline for Reporting Child Abuse or Neglect..."` ✓
8. **page_title**: `"Statewide Centralized Hotline for Reporting Child Abuse or Neglect..."` ✓
9. **citation_format**: `"21 O.S. § 846by"` ✓
10. **main_text**: `Full statute text extracted (11,000+ characters)` ✓

#### NULL Fields (4 of 14) - 29% Missing
1. **title_name**: `NULL` ✗ (e.g., "Crimes and Punishments")
2. **chapter_name**: `NULL` ✗ (e.g., "Reporting and Investigations")
3. **article_name**: `NULL` ✗ (e.g., "Oklahoma Children's Code")
4. **title_bar**: `NULL` ✗ (unclear what this should contain)

---

## Related Tables Analysis

### statute_paragraphs
- **Extracted**: 41 paragraphs
- **Status**: Can be populated ✓
- **Sample**: First paragraph contains main definitions and requirements

### statute_definitions
- **Extracted**: 0 definitions
- **Status**: No formal definitions found in this particular statute
- **Note**: This statute doesn't use "As used in this section" pattern

### legislative_history
- **Extracted**: 0 entries
- **Status**: Historical data available but not parsed yet ✗
- **Note**: HTML contains extensive history section that needs better parsing:
  - Multiple amendments from 1965 to 2025
  - HB/SB numbers, chapter numbers, effective dates
  - Example: "Laws 2025, HB 1565, c. 26, § 1, eff. November 1, 2025"

### statute_citations
- **Extracted**: 163 cross-references
- **Status**: Can be populated ✓
- **Sample**: References to "Title 21 § 20N", "Title 30 § 2-117", etc.

---

## Key Findings

### 1. Missing Data in Previous Imports

The NULL values in your previous imports are likely due to:

**a) Fields That Don't Exist in HTML**
- `title_name` - Not explicitly stated in the HTML
- `chapter_name` - Not explicitly stated in the HTML
- `article_name` - Not explicitly stated in the HTML
- `title_bar` - Unclear what this field represents

**b) Parsing Logic Gaps**
The current parser doesn't extract:
- Legislative history (historical data section exists but needs parsing)
- Title/Chapter/Article names (may need lookup table or separate source)

### 2. Schema Recommendations

**Option A: Keep Schema, Improve Parser**
- Add lookup table for title_number → title_name mapping
  - Title 10A = "Children and Juvenile Code"
  - Title 21 = "Crimes and Punishments"
  - Title 22 = "Criminal Procedure"
  - etc.
- Parse "Historical Data" section for legislative_history table
- Make certain fields NULLABLE in schema since they're not always available

**Option B: Simplify Schema**
Remove fields that are rarely/never populated:
- Remove `title_bar` (unclear purpose)
- Remove `chapter_name` and `article_name` (not in source HTML)
- Keep `chapter_number` and `article_number` (can be extracted)
- Add `title_name` via lookup table

### 3. Data Quality Issues

**Current Parser Limitations:**
1. **Legislative History Not Parsed**
   - HTML contains: "Amended by Laws 2025, HB 1565, c. 26, § 1, eff. November 1, 2025"
   - Parser needs to extract: year, bill_type (HB/SB), bill_number, effective_date

2. **Multiple Versions**
   - This statute has 3 versions (amended 3 times in 2025 session)
   - Need to decide: Store all versions or just current version?

3. **Cross-References**
   - Parser finds 163 citations
   - Need to map these to actual cite_ids in database (requires lookup)

---

## Comparison: Old vs Improved Parser

### What We Were Storing Before
```json
{
  "cite_id": "455989",
  "title_number": "21",
  "section_number": "846by",
  "main_text": "[full text]",
  "title_name": NULL,        // Missing
  "chapter_name": NULL,      // Missing
  "article_name": NULL,      // Missing
  "title_bar": NULL         // Missing
}
```

### What We Can Store Now
```json
{
  "cite_id": "455989",
  "url": "https://www.oscn.net/applications/oscn/DeliverDocument.asp?CiteID=455989",
  "title_number": "21",
  "title_name": "Crimes and Punishments",     // Via lookup table
  "chapter_number": "2",
  "chapter_name": "Reporting and Investigations",  // Via lookup OR leave NULL
  "article_number": "1",
  "article_name": "Oklahoma Children's Code",  // Via lookup OR leave NULL
  "section_number": "846by",
  "section_name": "Statewide Centralized Hotline...",
  "page_title": "Statewide Centralized Hotline...",
  "citation_format": "21 O.S. § 846by",
  "main_text": "[full text]",
  "full_json": { /* complete parsed data */ }
}
```

**Plus Related Tables:**
- 41 paragraph records
- 163 citation records
- ~50 legislative history records (if we improve the parser)

---

## Recommended Actions

### Immediate (Before Scraping)
1. ✓ **Create title_name lookup table**
   ```sql
   CREATE TABLE title_names (
     title_number VARCHAR(10) PRIMARY KEY,
     title_name TEXT NOT NULL
   );
   -- Populate with 85 titles + Constitution
   ```

2. ✓ **Make certain fields NULLABLE**
   ```sql
   ALTER TABLE statutes
     ALTER COLUMN title_bar DROP NOT NULL,
     ALTER COLUMN chapter_name DROP NOT NULL,
     ALTER COLUMN article_name DROP NOT NULL;
   ```

3. ✓ **Improve legislative history parser**
   - Parse "Historical Data" section
   - Extract: year, bill_type, bill_number, effective_date

### Later (Optional Enhancements)
1. Consider storing multiple versions of same statute
2. Build cross-reference resolution (map citations to cite_ids)
3. Extract definitions more intelligently (handle various patterns)

---

## Bottom Line

**Why were there NULL values?**
- 30% of schema fields (`title_name`, `chapter_name`, `article_name`, `title_bar`) are not directly available in the HTML
- Parser was basic and only extracted obvious fields

**Solution:**
1. Use lookup table for `title_name` (easy fix)
2. Leave `chapter_name` and `article_name` as NULL (not critical, not in HTML)
3. Remove or repurpose `title_bar` field (unclear purpose)
4. Improve parser to extract legislative history
5. Use `full_json` JSONB field to store complete parsed data as backup

**Improved Schema Coverage:**
- Before: 71% fields populated (10/14)
- After lookup table: 79% fields populated (11/14)
- If we remove unused `title_bar`: 85% fields populated (11/13)

This is acceptable data quality for a legal database!
