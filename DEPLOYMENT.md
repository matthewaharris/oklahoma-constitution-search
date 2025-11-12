# Oklahoma Constitution Search - Deployment Guide

## Quick Deploy to Render (Recommended - Free Tier)

### Prerequisites
- GitHub account
- Render account (sign up at render.com - it's free!)
- Your API keys ready:
  - Pinecone API key
  - OpenAI API key
  - Supabase URL & Key

### Step 1: Push Code to GitHub

```bash
# Initialize git repository (if not already done)
git init

# Add all files
git add .

# Create first commit
git commit -m "Initial commit - Oklahoma Constitution Search"

# Create GitHub repository and push
# (Follow GitHub's instructions to create a new repo)
git remote add origin https://github.com/YOUR_USERNAME/oklahoma-constitution-search.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy on Render

1. **Go to [Render Dashboard](https://dashboard.render.com/)**

2. **Click "New +" → "Web Service"**

3. **Connect your GitHub repository**
   - Select "oklahoma-constitution-search" repo

4. **Configure the service:**
   - **Name**: `oklahoma-constitution-search` (or your choice)
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --timeout 120 --workers 2`
   - **Plan**: Free

5. **Add Environment Variables:**
   Click "Advanced" → "Add Environment Variable"

   Add these variables:
   ```
   PRODUCTION=true
   PINECONE_API_KEY=your_pinecone_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   SUPABASE_URL=your_supabase_url_here
   SUPABASE_KEY=your_supabase_key_here
   PINECONE_INDEX_NAME=oklahoma-constitution
   ```

6. **Click "Create Web Service"**

7. **Wait for deployment** (usually 5-10 minutes)

8. **Your app will be live at:**
   ```
   https://oklahoma-constitution-search.onrender.com
   ```

### Step 3: Share Your App!

Your app is now live and accessible to anyone at your Render URL.

---

## Alternative: Deploy to Railway

### Step 1: Push to GitHub (same as above)

### Step 2: Deploy on Railway

1. Go to [Railway.app](https://railway.app/)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Add environment variables (same as Render)
5. Deploy!

---

## Alternative: Deploy to Heroku

### Prerequisites
- Heroku CLI installed
- Heroku account

### Steps

```bash
# Login to Heroku
heroku login

# Create app
heroku create oklahoma-constitution-search

# Set environment variables
heroku config:set PRODUCTION=true
heroku config:set PINECONE_API_KEY=your_key
heroku config:set OPENAI_API_KEY=your_key
heroku config:set SUPABASE_URL=your_url
heroku config:set SUPABASE_KEY=your_key

# Deploy
git push heroku main

# Open app
heroku open
```

---

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `PRODUCTION` | Enables production mode | `true` |
| `PINECONE_API_KEY` | Your Pinecone API key | `pcsk_...` |
| `OPENAI_API_KEY` | Your OpenAI API key | `sk-proj-...` |
| `SUPABASE_URL` | Your Supabase project URL | `https://xxx.supabase.co` |
| `SUPABASE_KEY` | Your Supabase anon/service key | `eyJ...` |
| `PINECONE_INDEX_NAME` | Name of your Pinecone index | `oklahoma-constitution` |

---

## Troubleshooting

### Build fails with "Module not found"
- Check that requirements.txt is properly formatted
- Ensure all dependencies are listed

### App crashes on startup
- Verify all environment variables are set correctly
- Check logs: `heroku logs --tail` or Render dashboard logs

### Search not working
- Verify Pinecone index has data (202 vectors)
- Check API keys are correct
- Ensure vector database was built before deployment

---

## Cost Estimates

### Free Tier Usage:
- **Render Free**: Good for low-medium traffic, sleeps after inactivity
- **Railway Free**: $5 credit/month, good for testing
- **Heroku**: Limited free tier

### API Costs (Pay-as-you-go):
- **Vector Search (embeddings)**: ~$0.0001 per query
- **RAG Questions (embeddings + GPT-3.5)**: ~$0.001-0.003 per question
- **RAG Questions (embeddings + GPT-4)**: ~$0.01-0.03 per question

---

## Custom Domain (Optional)

### On Render:
1. Go to your service settings
2. Click "Custom Domain"
3. Add your domain
4. Follow DNS configuration instructions

### On Railway:
1. Go to service settings
2. Click "Settings" → "Domains"
3. Add custom domain
4. Update DNS records

---

## Monitoring

### Render:
- View logs in dashboard
- Monitor resource usage
- Set up health checks

### Railway:
- Built-in metrics dashboard
- Log streaming
- Resource monitoring

---

## Support

For issues or questions:
- Check application logs first
- Verify environment variables
- Test API keys separately
- Review Render/Railway documentation

---

## Security Notes

⚠️ **Never commit API keys to Git!**
- Always use environment variables
- Keep `.gitignore` updated
- Rotate keys if accidentally exposed
- Use separate keys for production/development

---

Your Oklahoma Constitution Search app is now live and ready to share! 🎉
