# Oklahoma Case Law & AG Opinions Integration Plan

## Overview

This plan outlines how to scrape, store, and integrate Oklahoma case law and Attorney General opinions into the legal research application, enabling cross-referencing with existing statutes and constitution data.

---

## Data Sources

### 1. Case Law (4 Court Systems)
- **Oklahoma Supreme Court** (1890-present) - `STOKCSSC`
- **Court of Criminal Appeals** (1908-present) - `STOKCSCR`
- **Court of Civil Appeals** (1968-present) - `STOKCSCV`
- **Court on the Judiciary** - `STOKCSJU`

**Base URL**: `https://www.oscn.net/applications/oscn/index.asp?ftdb=STOKCS&level=1`

### 2. Attorney General Opinions
- **Date Range**: 1977-present
- **Database Code**: `STOKAG`

**Base URL**: `https://www.oscn.net/applications/oscn/index.asp?ftdb=STOKAG&level=1`

---

## Database Schema Design

### New Table: `oklahoma_cases`

```sql
CREATE TABLE IF NOT EXISTS oklahoma_cases (
    id BIGSERIAL PRIMARY KEY,

    -- Case Identification
    cite_id TEXT UNIQUE NOT NULL,  -- OSCN CiteID (e.g., "547774")
    citation TEXT NOT NULL,         -- Official citation (e.g., "2025 OK 2, 562 P.3d 1085")
    case_number TEXT,               -- Docket number (e.g., "121688")

    -- Court Information
    court_type TEXT NOT NULL,       -- "supreme_court", "criminal_appeals", "civil_appeals", "judiciary"
    court_database TEXT NOT NULL,   -- Database code (e.g., "STOKCSSC")

    -- Date Information
    decision_date DATE NOT NULL,
    decision_year INTEGER NOT NULL,

    -- Parties
    case_title TEXT NOT NULL,       -- Full case title
    appellant TEXT,                 -- Party appealing
    appellee TEXT,                  -- Opposing party
    other_parties TEXT[],           -- Additional parties

    -- Judges/Justices
    authoring_judge TEXT,           -- Judge who wrote opinion
    concurring_judges TEXT[],       -- Judges who concurred
    dissenting_judges TEXT[],       -- Judges who dissented

    -- Opinion Content
    opinion_text TEXT NOT NULL,     -- Full opinion text
    syllabus TEXT,                  -- Headnotes/syllabus
    holdings TEXT[],                -- Key holdings

    -- Metadata
    opinion_type TEXT,              -- "majority", "concurring", "dissenting", "per_curiam"
    procedural_posture TEXT,        -- "affirmed", "reversed", "remanded", etc.

    -- References
    statutes_cited TEXT[],          -- Referenced statutes
    cases_cited TEXT[],             -- Referenced cases

    -- URL
    oscn_url TEXT NOT NULL,         -- Direct OSCN link

    -- Timestamps
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for efficient querying
CREATE INDEX idx_cases_citation ON oklahoma_cases(citation);
CREATE INDEX idx_cases_cite_id ON oklahoma_cases(cite_id);
CREATE INDEX idx_cases_decision_date ON oklahoma_cases(decision_date DESC);
CREATE INDEX idx_cases_decision_year ON oklahoma_cases(decision_year DESC);
CREATE INDEX idx_cases_court_type ON oklahoma_cases(court_type);
CREATE INDEX idx_cases_case_number ON oklahoma_cases(case_number);

-- Full-text search
CREATE INDEX idx_cases_opinion_text_search ON oklahoma_cases USING gin(to_tsvector('english', opinion_text));
CREATE INDEX idx_cases_case_title_search ON oklahoma_cases USING gin(to_tsvector('english', case_title));
```

### New Table: `attorney_general_opinions`

```sql
CREATE TABLE IF NOT EXISTS attorney_general_opinions (
    id BIGSERIAL PRIMARY KEY,

    -- Opinion Identification
    cite_id TEXT UNIQUE NOT NULL,   -- OSCN CiteID
    citation TEXT NOT NULL,          -- "2025 OK AG 3"
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
    statutes_cited TEXT[],
    cases_cited TEXT[],

    -- URL
    oscn_url TEXT NOT NULL,

    -- Timestamps
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_ag_citation ON attorney_general_opinions(citation);
CREATE INDEX idx_ag_cite_id ON attorney_general_opinions(cite_id);
CREATE INDEX idx_ag_opinion_date ON attorney_general_opinions(opinion_date DESC);
CREATE INDEX idx_ag_opinion_year ON attorney_general_opinions(opinion_year DESC);
CREATE INDEX idx_ag_opinion_number ON attorney_general_opinions(opinion_number);

-- Full-text search
CREATE INDEX idx_ag_opinion_text_search ON attorney_general_opinions USING gin(to_tsvector('english', opinion_text));
CREATE INDEX idx_ag_requestor_search ON attorney_general_opinions USING gin(to_tsvector('english', requestor_name || ' ' || requestor_organization));
```

---

## Pinecone Vector Index Strategy

### Option 1: Separate Indexes (Recommended for MVP)

**Advantages:**
- Easier to manage and query
- Can use different embedding strategies
- Better performance isolation

**Structure:**
```
oklahoma-cases          (new index for case law)
oklahoma-ag-opinions    (new index for AG opinions)
oklahoma-statutes       (existing)
oklahoma-constitution   (existing)
```

### Option 2: Unified Index with Metadata Filtering

**Advantages:**
- Single query can search all legal documents
- Easier cross-referencing
- Lower index management overhead

**Structure:**
```
oklahoma-legal-documents
  └── metadata filters:
      - document_type: "statute", "constitution", "case", "ag_opinion"
      - source_database: "STOKST", "STOKCS", "STOKAG"
      - court_type: for cases
      - year: for all documents
```

**Recommendation**: Start with **Option 1** (separate indexes), then consolidate later if needed.

---

## Scraping Strategy

### Phase 1: Case Law Scraping

#### Step 1: Discover All Cases
1. Start at top-level index for each court
2. Expand year-by-year navigation
3. Extract all CiteID values
4. Store in discovery queue

**Estimated Volume:**
- Supreme Court (1890-2025): ~50,000-100,000 cases
- Criminal Appeals (1908-2025): ~40,000-80,000 cases
- Civil Appeals (1968-2025): ~20,000-40,000 cases
- **Total**: ~110,000-220,000 cases

#### Step 2: Scrape Individual Cases
For each CiteID:
```python
url = f"https://www.oscn.net/applications/oscn/DeliverDocument.asp?CiteID={cite_id}"
```

**Extract:**
- Citation (from header)
- Case number
- Decision date
- Court information
- Parties (plaintiff, defendant, appellant, appellee)
- Judges/Justices
- Opinion text (structured by paragraphs)
- Syllabus/headnotes
- Holdings
- Citations to statutes and other cases

**Rate Limiting:**
- 1-2 requests per second (respectful scraping)
- Handle rate limit responses (429)
- Retry with exponential backoff

#### Step 3: Store in Supabase
- Batch insert to `oklahoma_cases` table
- Deduplicate by `cite_id`
- Track scraping progress

### Phase 2: AG Opinions Scraping

#### Step 1: Discover All Opinions
1. Expand each year (1977-2025)
2. Extract CiteID for each opinion
3. Store in discovery queue

**Estimated Volume:**
- ~48 years × 50-100 opinions/year = ~2,400-4,800 opinions

#### Step 2: Scrape Individual Opinions
Similar to case law, but extract:
- Citation
- Opinion number
- Date
- Requestor name, title, organization
- Question presented
- Opinion text
- Conclusion
- Citations

#### Step 3: Store in Supabase
- Batch insert to `attorney_general_opinions`
- Deduplicate by `cite_id`

---

## Embedding Strategy

### Chunking Strategy for Cases

**Challenge**: Cases can be 10,000-50,000+ words

**Solution**: Intelligent chunking
1. **By Section**: Split by opinion structure
   - Syllabus (separate chunk)
   - Facts (separate chunk)
   - Discussion (may need multiple chunks)
   - Holding/Conclusion (separate chunk)

2. **Chunk Size**: 1,000-2,000 tokens per chunk
   - Overlap: 200 tokens
   - Preserve paragraph boundaries

3. **Metadata for Each Chunk**:
```python
{
    "cite_id": "547774",
    "citation": "2025 OK 2",
    "chunk_type": "discussion",  # syllabus, facts, discussion, holding
    "chunk_index": 0,
    "total_chunks": 5,
    "case_title": "In re G.E.M.S.",
    "decision_date": "2025-01-14",
    "court_type": "supreme_court"
}
```

### Chunking Strategy for AG Opinions

**Simpler structure** (typically shorter):
1. Question Presented (chunk 1)
2. Opinion Body (chunk 2-N, if long)
3. Conclusion (final chunk)

---

## Implementation Plan

### Phase 1: Infrastructure Setup (Week 1)

**Tasks:**
1. Create database schema in Supabase
2. Create Pinecone indexes
3. Build scraper framework
   - URL discovery crawler
   - Document parser
   - Rate limiter
   - Progress tracker
   - Error handler

**Deliverables:**
- `case_law_schema.sql`
- `case_law_scraper.py`
- `ag_opinion_scraper.py`

### Phase 2: Discovery & Scraping (Weeks 2-4)

**Tasks:**
1. Run discovery crawler for all courts
2. Scrape cases (prioritize recent first)
   - Start with 2020-2025 (most relevant)
   - Then backfill historical cases
3. Scrape AG opinions (all years)
4. Monitor progress and error rates

**Estimated Time:**
- Cases: 110K-220K × 2 seconds = 60-120 hours
- AG Opinions: 2.4K-4.8K × 2 seconds = 1.3-2.6 hours
- **Total scraping time**: ~3-5 days (with proper rate limiting)

**Strategy:**
- Run in parallel: 2-3 workers
- Start with most recent data
- Incremental uploads to Supabase

### Phase 3: Embedding Generation (Weeks 5-6)

**Tasks:**
1. Chunk all cases and opinions
2. Generate embeddings (OpenAI text-embedding-3-small)
3. Upload to Pinecone in batches
4. Verify embeddings quality

**Cost Estimation:**
- Cases: ~110K-220K cases × avg 5 chunks × 1,500 tokens/chunk
  - Total tokens: ~825M-1.65B tokens
  - Cost: $16.50-$33.00 (at $0.00002/1K tokens)
- AG Opinions: ~2.4K-4.8K × avg 2 chunks × 1,000 tokens
  - Total tokens: ~4.8M-9.6M tokens
  - Cost: $0.10-$0.20
- **Total embedding cost**: ~$17-$33

### Phase 4: Integration (Week 7)

**Tasks:**
1. Update search endpoints to query new indexes
2. Add filters for document type
3. Update UI to show case law and AG opinions
4. Cross-reference citations
5. Update RAG prompts to handle legal citations

**UI Changes:**
- Add "Search In" filter: Constitution, Statutes, Case Law, AG Opinions, All
- Display case metadata (citation, date, court)
- Show AG opinion requestor info
- Link to OSCN source

### Phase 5: Testing & Optimization (Week 8)

**Tasks:**
1. Test search quality
2. Verify citation accuracy
3. Optimize query performance
4. A/B test with users
5. Monitor feedback

---

## Scraper Architecture

### File Structure
```
scrapers/
├── case_law/
│   ├── discoverer.py          # Find all CiteIDs
│   ├── scraper.py             # Scrape individual cases
│   ├── parser.py              # Parse HTML into structured data
│   └── chunker.py             # Split cases into chunks
├── ag_opinions/
│   ├── discoverer.py
│   ├── scraper.py
│   ├── parser.py
│   └── chunker.py
├── common/
│   ├── rate_limiter.py        # Respectful rate limiting
│   ├── retry_handler.py       # Exponential backoff
│   ├── progress_tracker.py    # Track scraping progress
│   └── supabase_uploader.py   # Batch upload to Supabase
└── embeddings/
    ├── embedder.py            # Generate embeddings
    └── pinecone_uploader.py   # Upload to Pinecone
```

### Key Components

#### 1. Discovery Crawler
```python
class CaseDiscoverer:
    def discover_all_cite_ids(self, court_db: str) -> List[str]:
        """
        Navigate hierarchical index and extract all CiteIDs
        """
        # Start at top level
        # Expand each year
        # Extract CiteIDs from links
        # Return full list
```

#### 2. Document Parser
```python
class CaseParser:
    def parse_case(self, html: str, cite_id: str) -> Dict:
        """
        Extract structured data from case HTML
        """
        return {
            'cite_id': cite_id,
            'citation': self.extract_citation(html),
            'case_title': self.extract_title(html),
            'decision_date': self.extract_date(html),
            'opinion_text': self.extract_opinion(html),
            # ... more fields
        }
```

#### 3. Intelligent Chunker
```python
class CaseChunker:
    def chunk_case(self, case: Dict) -> List[Dict]:
        """
        Split case into semantic chunks
        """
        chunks = []

        # Syllabus chunk
        if case['syllabus']:
            chunks.append({
                'text': case['syllabus'],
                'chunk_type': 'syllabus',
                'metadata': {...}
            })

        # Opinion chunks (split intelligently)
        opinion_chunks = self.split_long_text(
            case['opinion_text'],
            max_tokens=1500,
            overlap=200
        )
        # ... more chunking

        return chunks
```

---

## Search Integration

### Updated Search Flow

```python
def search_legal_documents(query: str, sources: List[str]) -> List[Dict]:
    """
    sources: ["constitution", "statutes", "cases", "ag_opinions"]
    """
    results = []

    if "constitution" in sources:
        results.extend(search_index("oklahoma-constitution", query))

    if "statutes" in sources:
        results.extend(search_index("oklahoma-statutes", query))

    if "cases" in sources:
        results.extend(search_index("oklahoma-cases", query))

    if "ag_opinions" in sources:
        results.extend(search_index("oklahoma-ag-opinions", query))

    # Combine and re-rank
    return rerank_results(results, query)
```

### Citation Cross-Referencing

When a case cites a statute:
1. Extract statute citation (e.g., "43 O.S. § 109")
2. Link to actual statute in database
3. Show bidirectional references in UI

---

## Risk Assessment & Mitigation

### Risk 1: IP Blocking
**Mitigation:**
- Respectful rate limiting (1-2 req/sec)
- User-Agent identification
- Monitor for 429/403 responses
- Pause and resume capability

### Risk 2: HTML Structure Changes
**Mitigation:**
- Robust parsing with fallbacks
- Error logging for failed parses
- Manual review of failed cases

### Risk 3: Large Data Volume
**Mitigation:**
- Incremental scraping (recent first)
- Progress tracking and resume
- Batch processing
- Cloud storage for raw HTML

### Risk 4: Embedding Costs
**Mitigation:**
- Start with recent cases (2020+)
- Monitor costs closely
- Consider chunking optimization

---

## Success Metrics

### Scraping Quality
- **Completeness**: >98% of discovered cases successfully scraped
- **Accuracy**: >95% correct metadata extraction
- **Error rate**: <2% parsing failures

### Search Quality
- **Relevance**: Users find cases related to their queries
- **Coverage**: Cross-referencing between statutes and cases works
- **Performance**: Search latency <2 seconds

### User Engagement
- **Adoption**: Users search case law and AG opinions
- **Feedback**: Positive feedback on results quality

---

## Next Steps (Immediate Actions)

1. **Review & Approve Plan** - Get your feedback on scope and approach
2. **Create Database Schema** - Run SQL to create tables in Supabase
3. **Build Discovery Crawler** - Start finding all CiteIDs
4. **Test Parser** - Validate parsing on 10-20 sample cases
5. **Estimate Timeline** - Based on actual scraping speed

---

## Future Enhancements

### Phase 2 Features (Post-MVP)
1. **Citation Network Analysis** - Show which cases cite each other
2. **Shepardizing** - Mark overruled or modified cases
3. **Topic Classification** - ML-based categorization (family law, criminal, etc.)
4. **Judge Analytics** - Track trends by authoring judge
5. **Temporal Analysis** - How law evolved over time
6. **Headnote Extraction** - Separate key points from full opinion
7. **PDF Export** - Generate research memos with citations

### Advanced Features
1. **Citator Service** - "Is this case still good law?"
2. **Similarity Search** - "Find cases like this one"
3. **Predictive Analytics** - "How might a court rule?"
4. **Jurisdiction Expansion** - Add federal cases, other states

---

## Conclusion

This plan provides a comprehensive roadmap for integrating Oklahoma case law and AG opinions into your legal research platform. The phased approach allows for:

1. **Quick MVP** (8 weeks) with recent, high-value content
2. **Incremental expansion** to historical cases
3. **Cost control** through intelligent chunking
4. **Quality assurance** at each phase

**Estimated Resources:**
- **Time**: 8 weeks (with automation)
- **Cost**: ~$20-$35 (embedding generation)
- **Storage**: ~5-10GB (Supabase + Pinecone)

The result will be a comprehensive Oklahoma legal research tool covering statutes, constitution, case law, and AG opinions—enabling users to find authoritative answers with proper legal citations.
