# Feedback-Based Learning System

## Overview
Add user feedback to improve search results over time through re-ranking.

## Phase 1: Data Collection (Week 1)

### Database Schema
```sql
-- Store individual feedback events
CREATE TABLE user_feedback (
    id SERIAL PRIMARY KEY,
    session_id TEXT,
    question TEXT NOT NULL,
    question_embedding VECTOR(1536), -- for similarity matching
    answer_type TEXT CHECK (answer_type IN ('ask', 'search')),
    cite_ids TEXT[] NOT NULL, -- documents shown
    rating INTEGER CHECK (rating IN (-1, 0, 1)), -- -1=bad, 0=neutral, 1=good
    feedback_comment TEXT,
    model_used TEXT, -- gpt-4, gpt-3.5-turbo
    created_at TIMESTAMP DEFAULT NOW()
);

-- Aggregated document performance
CREATE TABLE document_performance (
    cite_id TEXT PRIMARY KEY,
    total_shown INTEGER DEFAULT 0,
    positive_feedback INTEGER DEFAULT 0,
    negative_feedback INTEGER DEFAULT 0,
    feedback_score FLOAT, -- (positive - negative) / total_shown
    last_updated TIMESTAMP DEFAULT NOW()
);

-- Create index for fast lookups
CREATE INDEX idx_user_feedback_cite_ids ON user_feedback USING GIN(cite_ids);
CREATE INDEX idx_document_performance_score ON document_performance(feedback_score DESC);
```

### UI Changes
Add feedback buttons after each answer:

```html
<div class="feedback-section">
    <p style="font-size: 14px; color: #666; margin-bottom: 10px;">
        Was this answer helpful?
    </p>
    <div class="feedback-buttons">
        <button class="feedback-btn" onclick="submitFeedback(1)">
            👍 Yes
        </button>
        <button class="feedback-btn" onclick="submitFeedback(-1)">
            👎 No
        </button>
    </div>
    <textarea
        id="feedbackComment"
        placeholder="Optional: Tell us how we can improve..."
        style="display: none; margin-top: 10px; width: 100%;"
    ></textarea>
</div>
```

### Backend Endpoint
```python
@app.route('/feedback', methods=['POST'])
@limiter.limit("20 per minute")
def submit_feedback():
    """Store user feedback"""
    data = request.get_json()

    # Store in database
    supabase.table('user_feedback').insert({
        'session_id': data.get('session_id'),
        'question': data.get('question'),
        'cite_ids': data.get('cite_ids'),
        'rating': data.get('rating'),
        'feedback_comment': data.get('comment'),
        'answer_type': data.get('type'),
        'model_used': data.get('model')
    }).execute()

    # Update aggregated performance
    update_document_performance(data.get('cite_ids'), data.get('rating'))

    return jsonify({'success': True})
```

## Phase 2: Re-ranking (Week 2)

### Smart Re-ranking Algorithm
```python
def rerank_with_feedback(results, question_category=None):
    """
    Re-rank results based on historical performance

    Args:
        results: Initial search results from Pinecone
        question_category: Optional category for context-specific ranking

    Returns:
        Re-ranked results with adjusted scores
    """
    # Get performance data for all cite_ids
    cite_ids = [r['cite_id'] for r in results]

    performance_data = supabase.table('document_performance').select(
        'cite_id', 'feedback_score'
    ).in_('cite_id', cite_ids).execute()

    # Create lookup dict
    performance_map = {
        item['cite_id']: item['feedback_score']
        for item in performance_data.data
    }

    # Adjust scores
    for result in results:
        cite_id = result['cite_id']
        original_score = result['score']
        feedback_score = performance_map.get(cite_id, 0.0)  # default to neutral

        # Blend original semantic similarity with user feedback
        # 80% original score, 20% feedback influence
        result['adjusted_score'] = original_score * 0.8 + feedback_score * 0.2
        result['feedback_boost'] = feedback_score

    # Re-sort by adjusted score
    return sorted(results, key=lambda x: x['adjusted_score'], reverse=True)
```

### Integration
```python
# In search_system.py
def search(self, query, source='both', top_k=5):
    # ... existing search logic ...

    # Get initial results from Pinecone
    results = self._get_pinecone_results(query, source, top_k)

    # Re-rank based on user feedback
    results = rerank_with_feedback(results)

    return results
```

## Phase 3: Analytics Dashboard (Week 3)

Create admin dashboard to view:
- Most/least helpful documents
- Common queries with negative feedback
- Feedback trends over time

```python
@app.route('/admin/feedback-stats')
def feedback_stats():
    """Admin dashboard for feedback analytics"""

    # Top performing documents
    top_docs = supabase.table('document_performance').select(
        'cite_id', 'feedback_score', 'total_shown'
    ).order('feedback_score', desc=True).limit(10).execute()

    # Worst performing documents
    worst_docs = supabase.table('document_performance').select(
        'cite_id', 'feedback_score', 'total_shown'
    ).order('feedback_score', asc=True).limit(10).execute()

    # Recent negative feedback
    recent_negative = supabase.table('user_feedback').select(
        'question', 'cite_ids', 'feedback_comment'
    ).eq('rating', -1).order('created_at', desc=True).limit(20).execute()

    return render_template('admin/feedback_stats.html',
        top_docs=top_docs.data,
        worst_docs=worst_docs.data,
        recent_negative=recent_negative.data
    )
```

## Phase 4: Advanced Features (Optional)

### Query Similarity Matching
When user rates an answer, also improve similar future questions:

```python
def update_similar_questions(question, rating, cite_ids):
    """Update performance for semantically similar questions"""

    # Get embedding for rated question
    question_embedding = create_embedding(question)

    # Find similar questions in feedback history
    similar_feedback = find_similar_questions(question_embedding, threshold=0.85)

    # Adjust their document rankings too
    for similar_q in similar_feedback:
        boost_documents_for_question(similar_q['id'], cite_ids, rating * 0.5)
```

### A/B Testing
Test feedback-enhanced vs. standard ranking:

```python
def search_with_ab_test(query):
    """Randomly assign users to test groups"""

    user_group = random.choice(['control', 'feedback_enhanced'])

    if user_group == 'feedback_enhanced':
        results = search_with_feedback_reranking(query)
    else:
        results = standard_search(query)

    # Track which group performs better
    log_ab_test_assignment(user_group, query)

    return results
```

## Benefits

1. **Self-improving system** - Gets better with usage
2. **No manual curation needed** - Users tell you what works
3. **Personalization potential** - Could adapt per user over time
4. **Identifies content gaps** - See what people need but can't find
5. **Low cost** - Just database storage, no model retraining

## Metrics to Track

- Feedback rate (% of queries that get rated)
- Positive/negative ratio
- Impact of re-ranking on subsequent feedback
- Documents that consistently get negative feedback
- Questions that never get good answers

## Privacy Considerations

- Don't store personally identifiable information
- Use session IDs, not user accounts
- Allow users to opt-out of feedback collection
- Aggregate data before analysis
- Clear privacy policy

## Cost Estimate

- Database storage: ~$0.01/month per 1000 feedback entries
- No additional API costs (just database queries)
- Minimal compute overhead for re-ranking

## Next Steps

1. Add database schema to Supabase
2. Implement UI feedback buttons
3. Create feedback endpoint
4. Build re-ranking logic
5. Test with sample data
6. Deploy and monitor
