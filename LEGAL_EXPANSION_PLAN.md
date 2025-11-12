# Oklahoma Legal AI System - Expansion Plan

## Vision
Build a comprehensive AI system that understands Oklahoma law deeply and can answer complex legal questions with proper citations and reasoning.

## Current State (Phase 0) ✅
- Oklahoma Constitution: 202 sections indexed
- Basic semantic search
- RAG-powered Q&A
- GPT-3.5/GPT-4 integration

## Phase 1: Full Oklahoma Statutes (2-4 weeks)

### Goal
Index all Oklahoma statutes (Titles 1-85) for comprehensive legal coverage.

### Tasks
1. **Data Collection**
   - [ ] Scrape Titles 1-85 from OSCN (~50,000 sections)
   - [ ] Parse and structure statute text
   - [ ] Extract metadata (title, chapter, section, effective dates)
   - [ ] Store in Supabase

2. **Vector Database Expansion**
   - [ ] Generate embeddings for all statutes
   - [ ] Upgrade Pinecone plan (need paid tier for scale)
   - [ ] Implement efficient chunking strategy
   - [ ] Add rich metadata (topics, keywords, cross-references)

3. **Enhanced Search**
   - [ ] Multi-statute search
   - [ ] Topic-based filtering
   - [ ] Title/chapter navigation
   - [ ] Amendment history tracking

### Estimated Costs
- Embeddings: $50-100 one-time (OpenAI)
- Pinecone: ~$70/month (Standard plan for 500K vectors)
- Development time: 2-4 weeks

### Success Metrics
- 50,000+ statutes indexed
- Sub-2-second search response time
- Accurate multi-statute queries

---

## Phase 2: Oklahoma Case Law (4-6 weeks)

### Goal
Add judicial opinions for legal precedent and interpretation.

### Data Sources
- Oklahoma Supreme Court opinions
- Court of Criminal Appeals
- Court of Civil Appeals
- District court published opinions

### Tasks
1. **Case Law Collection**
   - [ ] Scrape court opinions from OSCN
   - [ ] Parse case structure (parties, facts, holdings, reasoning)
   - [ ] Extract legal principles and citations
   - [ ] Link to relevant statutes

2. **Legal Citation System**
   - [ ] Build citation graph (which cases cite which)
   - [ ] Track precedent chains
   - [ ] Identify controlling vs. persuasive authority
   - [ ] Note overruled/superseded cases

3. **Enhanced RAG**
   - [ ] Two-stage retrieval: statutes + case law
   - [ ] Citation verification
   - [ ] Precedent analysis
   - [ ] Legal synthesis

### Estimated Costs
- Embeddings: $100-200 (100K+ cases)
- Pinecone: Include in existing plan
- Development time: 4-6 weeks

### Success Metrics
- 100,000+ opinions indexed
- Accurate precedent identification
- Proper citation formatting

---

## Phase 3: Advanced Legal Reasoning (4-8 weeks)

### Goal
Implement sophisticated legal analysis capabilities.

### Features to Build

#### 1. Multi-Hop Legal Reasoning
```
Question: "Can a landlord evict without 30 days notice?"

Analysis Chain:
1. Find landlord-tenant statutes
2. Identify notice requirements
3. Check for exceptions
4. Review relevant case law
5. Synthesize with citations
```

**Implementation:**
- Chain-of-thought prompting
- Multi-stage retrieval
- Source verification
- Confidence scoring

#### 2. Legal Document Understanding
- Upload and analyze contracts
- Compare to Oklahoma law
- Identify issues and risks
- Suggest modifications

#### 3. Temporal Legal Analysis
- "What was the law in 2010?"
- Track statute amendments
- Historical legal research
- Evolution of case law

#### 4. Conflict Detection
- Identify conflicting statutes
- Note when case law supersedes statute
- Flag ambiguous areas
- Suggest resolution strategies

### Implementation Details

**Improved Prompting Strategy:**
```python
legal_analysis_prompt = """You are an expert Oklahoma legal researcher with deep knowledge of:
- Oklahoma statutes and constitution
- Oklahoma case law and precedent
- Legal reasoning and analysis
- Legal citation standards

When analyzing legal questions:

STEP 1: IDENTIFY THE LEGAL ISSUE
- What is the core legal question?
- What area of law does this involve?
- Are there multiple sub-issues?

STEP 2: FIND RELEVANT LAW
- Which statutes apply?
- What case law is controlling?
- Are there regulations or rules?

STEP 3: ANALYZE AND APPLY
- How do the sources interact?
- What is the legal standard?
- What are the elements or requirements?

STEP 4: PROVIDE ANSWER
- State the conclusion clearly
- Cite specific sources (statute § and case citations)
- Note any caveats or exceptions
- Identify areas of uncertainty

STEP 5: PRACTICAL GUIDANCE
- What should someone know?
- What are the next steps?
- What pitfalls should be avoided?

ALWAYS INCLUDE:
- Proper legal citations
- "This is not legal advice" disclaimer
- Recommendation to consult licensed attorney for specific situations
"""
```

**Enhanced Retrieval:**
```python
def deep_legal_search(question: str) -> Dict:
    """Multi-stage legal research"""

    # Stage 1: Broad topic identification
    topics = identify_legal_topics(question)

    # Stage 2: Parallel search across sources
    statutes = search_statutes(question, topics)
    cases = search_case_law(question, topics)
    regs = search_regulations(question, topics)

    # Stage 3: Cross-reference and rank
    relevant_sources = cross_reference(statutes, cases, regs)
    ranked = rank_by_relevance(relevant_sources, question)

    # Stage 4: Citation verification
    verified = verify_citations(ranked)

    # Stage 5: Construct comprehensive context
    context = build_legal_context(verified)

    return context
```

### Estimated Costs
- Development time: 4-8 weeks
- No additional API costs (uses existing infrastructure)

### Success Metrics
- Accurate multi-step legal reasoning
- Proper citation of sources
- Identifies conflicts and ambiguities
- Helpful practical guidance

---

## Phase 4: Specialized Legal Tools (Ongoing)

### Features to Consider

1. **Legal Domain Specialization**
   - Family Law module
   - Criminal Law module
   - Business/Corporate Law
   - Real Estate Law
   - Employment Law

2. **Document Generation**
   - Legal forms with guidance
   - Contract templates
   - Compliance checklists

3. **Monitoring & Alerts**
   - Track new legislation
   - Monitor relevant cases
   - Alert on legal changes

4. **Collaboration Features**
   - Share research
   - Annotate findings
   - Team workspaces

---

## Alternative: Fine-Tuning Approach

### When to Consider Fine-Tuning

**Pros:**
- Faster inference (no large context needed)
- More natural legal language
- Better domain-specific understanding
- Can work offline

**Cons:**
- Expensive ($10K-50K initial)
- Hard to update (need to retrain)
- Less transparent (harder to verify sources)
- Still need RAG for citations

### Fine-Tuning Process

1. **Prepare Training Data**
   - Create Q&A pairs from legal documents
   - Include reasoning steps
   - Format as conversations
   - Need 10,000-100,000+ examples

2. **Fine-Tune Model**
   - Use OpenAI fine-tuning API
   - Start with GPT-3.5 (cheaper)
   - Test on held-out legal questions
   - Iterate on training data

3. **Deploy Hybrid System**
   - Use fine-tuned model for reasoning
   - Use RAG for citations and current law
   - Best of both worlds

### Estimated Costs
- Training data preparation: 100-200 hours
- Fine-tuning: $500-5,000 (depending on size)
- Inference: ~2x cost of base model
- Ongoing: Need to retrain for updates

**Recommendation:** Start with enhanced RAG. Consider fine-tuning only if:
- You have $20K+ budget
- Usage reaches 10,000+ queries/month
- Response time is critical
- Need offline deployment

---

## Technology Stack Evolution

### Current Stack
- Vector DB: Pinecone (202 vectors)
- Embeddings: OpenAI text-embedding-ada-002
- LLM: GPT-3.5/GPT-4
- Backend: Flask + Supabase

### Phase 1-2 Stack (Recommended)
- Vector DB: Pinecone Standard (~$70/mo for 500K vectors)
- Embeddings: Same (OpenAI ada-002)
- LLM: GPT-4 Turbo (better context window)
- Backend: Same
- Add: Redis for caching popular queries

### Phase 3+ Stack (If Scaling Needed)
- Vector DB: Pinecone or self-hosted Qdrant
- Embeddings: Consider voyage-law-2 (legal-specific)
- LLM: GPT-4 + optional fine-tuned model
- Backend: Add message queue for async processing
- Add: PostgreSQL for citation graph
- Add: Elasticsearch for full-text statute search

---

## Cost Projections

### Monthly Costs by Phase

**Current (Constitution Only):**
- Hosting: $0 (Render free)
- APIs: $2-5/day = $60-150/month
- **Total: ~$100/month**

**Phase 1 (Full Statutes):**
- Hosting: $7/month (Render paid)
- Pinecone: $70/month
- APIs: $5-10/day = $150-300/month
- **Total: ~$230-380/month**

**Phase 2 (+ Case Law):**
- Hosting: $25/month (more resources)
- Pinecone: $70/month
- APIs: $10-20/day = $300-600/month
- **Total: ~$400-700/month**

**Phase 3 (Advanced Features):**
- Same as Phase 2
- Possibly add caching to reduce costs
- **Total: ~$400-700/month**

**With Heavy Usage (1000+ users/day):**
- Hosting: $100/month (scale up)
- Pinecone: $200/month (more replicas)
- APIs: $30-50/day = $900-1500/month
- **Total: ~$1200-1800/month**

---

## Revenue Opportunities

If building a business:

**Freemium Model:**
- Free: 10 searches/day, GPT-3.5 only
- Pro ($20/month): Unlimited, GPT-4, priority
- Legal Pro ($99/month): API access, document analysis

**Enterprise:**
- Law firms: $500-2000/month/firm
- Legal tech companies: API licensing
- Government: Custom deployments

---

## Success Factors

### Technical
- ✅ Comprehensive data coverage
- ✅ Fast, accurate retrieval
- ✅ Proper legal citations
- ✅ Clear reasoning chains
- ✅ Regular updates

### Legal
- ⚠️ Proper disclaimers
- ⚠️ Not practicing law
- ⚠️ Accuracy verification
- ⚠️ User education
- ⚠️ Professional review

### Business
- 📈 User adoption
- 📈 Accuracy metrics
- 📈 User satisfaction
- 📈 Cost management
- 📈 Revenue (if applicable)

---

## Timeline Summary

- **Phase 0** (Current): Constitution only ✅
- **Phase 1** (Weeks 1-4): Full Oklahoma statutes
- **Phase 2** (Weeks 5-10): Case law integration
- **Phase 3** (Weeks 11-18): Advanced reasoning
- **Phase 4** (Ongoing): Specialized features

**Total to comprehensive system: 4-6 months**

---

## Next Immediate Actions

1. **Decide on scope**: Just statutes? Include case law?
2. **Budget confirmation**: Can you afford ~$400/month for Phase 2?
3. **Start Phase 1**: Begin scraping full Oklahoma statutes
4. **Test enhanced prompting**: Improve legal reasoning now
5. **Build citation system**: Track statute relationships

---

## Resources & References

- Oklahoma State Courts Network (OSCN): https://www.oscn.net/
- Oklahoma Legislature: http://www.oklegislature.gov/
- OpenAI Fine-tuning: https://platform.openai.com/docs/guides/fine-tuning
- Legal prompt engineering: Best practices for legal AI
- Pinecone pricing: https://www.pinecone.io/pricing/

---

**Prepared:** 2025-11-12
**Next Review:** After Phase 1 completion
**Owner:** Matthew Harris (mharris26@gmail.com)
