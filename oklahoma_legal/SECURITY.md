# Security Features

This document outlines the security measures implemented in the Oklahoma Constitution Search application.

## 🔒 Security Measures Implemented

### 1. Rate Limiting

**Purpose:** Prevent abuse and protect API costs

**Implementation:**
- **Global limits:** 200 requests per day, 50 per hour per IP address
- **Search endpoint:** 30 requests per minute
- **Ask endpoint (GPT calls):** 10 requests per minute (stricter due to cost)

**Benefits:**
- Prevents DDoS attacks
- Limits API cost exposure
- Ensures fair usage across all users

### 2. Input Validation & Sanitization

**Purpose:** Prevent injection attacks (XSS, SQL injection, etc.)

**Implementation:**
- All user inputs are sanitized before processing
- Removes potentially malicious scripts and code
- Maximum input length of 500 characters
- Whitespace normalization

**Protected against:**
- Cross-site scripting (XSS)
- Script injection
- SQL injection attempts
- Excessive input lengths

### 3. Security Headers

**Purpose:** Protect against common web vulnerabilities

**Headers implemented:**
- `X-Content-Type-Options: nosniff` - Prevents MIME type sniffing
- `X-Frame-Options: DENY` - Prevents clickjacking
- `X-XSS-Protection: 1; mode=block` - Enables browser XSS protection
- `Strict-Transport-Security` - Enforces HTTPS
- `Content-Security-Policy` - Restricts resource loading

### 4. CORS (Cross-Origin Resource Sharing)

**Purpose:** Control which domains can access the API

**Implementation:**
- CORS enabled only for specific API endpoints
- Configured to accept requests from any origin (can be restricted if needed)
- Production deployments can restrict to specific domains

### 5. Error Handling

**Purpose:** Don't expose sensitive information in errors

**Implementation:**
- Generic error messages to users
- Detailed errors logged server-side only
- No stack traces exposed to clients
- HTTP status codes properly configured

### 6. Environment Variable Management

**Purpose:** Protect API keys and secrets

**Implementation:**
- All API keys stored as environment variables
- No hardcoded credentials in code
- `.gitignore` prevents accidental commits
- Separate configs for dev/production

**Protected credentials:**
- Pinecone API key
- OpenAI API key
- Supabase URL and key

### 7. Request Validation

**Purpose:** Ensure requests are valid and safe

**Implementation:**
- JSON request validation
- Parameter type checking
- Whitelist for allowed AI models
- Limits on result counts (max 20 for search, max 5 sources for RAG)

### 8. HTTPS Enforcement

**Purpose:** Encrypt data in transit

**Implementation:**
- Strict-Transport-Security header
- Production deployments force HTTPS
- Render/Railway automatically provide SSL certificates

## 🛡️ Additional Recommendations

### For Production Deployment:

1. **Monitor API Usage:**
   - Set up alerts for unusual activity
   - Monitor OpenAI and Pinecone usage dashboards
   - Track rate limit violations

2. **Rotate API Keys Regularly:**
   - Change API keys every 90 days
   - Use different keys for dev/staging/production
   - Immediately rotate if keys are compromised

3. **Set Budget Limits:**
   - OpenAI: Set usage limits in dashboard
   - Pinecone: Monitor vector operations
   - Render: Set up notifications for resource usage

4. **Restrict CORS (Optional):**
   ```python
   # In app.py, change CORS to restrict domains:
   CORS(app, resources={
       r"/search": {"origins": ["https://yourdomain.com"]},
       r"/ask": {"origins": ["https://yourdomain.com"]}
   })
   ```

5. **Add Authentication (Optional for Private Use):**
   - Implement API keys for access
   - Use OAuth for user authentication
   - Add admin panel for monitoring

6. **Database Security:**
   - Row-Level Security (RLS) in Supabase
   - Read-only API keys for public access
   - Regular backups

## 📊 Rate Limit Details

| Endpoint | Rate Limit | Why |
|----------|------------|-----|
| `/search` | 30/min | Prevents abuse, reasonable for real users |
| `/ask` | 10/min | GPT calls are expensive, stricter limit |
| Global | 200/day, 50/hour | Overall protection per IP |

## 🚨 Security Incident Response

If you suspect a security issue:

1. **Immediately rotate all API keys:**
   - OpenAI dashboard → API keys → Revoke and create new
   - Pinecone dashboard → API keys → Create new key
   - Update environment variables in Render

2. **Check usage logs:**
   - OpenAI usage dashboard
   - Pinecone monitoring
   - Render application logs

3. **Block abusive IPs (if identified):**
   - Can be done at Render/Railway level
   - Or implement IP blacklist in Flask-Limiter

4. **Review and update security measures**

## 📝 Security Checklist for Deployment

- [ ] All API keys set as environment variables
- [ ] No hardcoded credentials in code
- [ ] `.gitignore` includes sensitive files
- [ ] Rate limiting enabled
- [ ] Input sanitization working
- [ ] HTTPS enforced
- [ ] Security headers configured
- [ ] Error messages don't expose internals
- [ ] Monitoring set up for API usage
- [ ] Budget alerts configured (OpenAI)

## 🔍 Testing Security

### Test Rate Limiting:
```bash
# Should get rate limited after 10 requests
for i in {1..15}; do
  curl -X POST http://localhost:5000/ask \
    -H "Content-Type: application/json" \
    -d '{"question":"test"}';
done
```

### Test Input Sanitization:
```bash
# Should remove script tags
curl -X POST http://localhost:5000/search \
  -H "Content-Type: application/json" \
  -d '{"query":"<script>alert('xss')</script> voting rights"}'
```

## 📚 Further Reading

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/latest/security/)
- [OpenAI Best Practices](https://platform.openai.com/docs/guides/safety-best-practices)
- [Render Security Guide](https://render.com/docs/security)

---

**Last Updated:** 2025-11-12
**Security Review:** Pass ✅

This application implements industry-standard security practices suitable for public deployment.
