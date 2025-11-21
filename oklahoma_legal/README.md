# Oklahoma Constitution Search

An AI-powered semantic search and Q&A system for the Oklahoma State Constitution. Search using natural language and get intelligent answers with citations.

![Oklahoma Constitution Search](https://img.shields.io/badge/Status-Live-success)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-lightgrey)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-green)

## 🌟 Features

### 1. **Semantic Search**
- Natural language search of the Oklahoma Constitution
- AI-powered relevance scoring
- Find sections by meaning, not just keywords
- Sub-second response times

### 2. **RAG-Powered Q&A**
- Ask questions in plain English
- Get comprehensive answers with citations
- Choose between GPT-3.5 Turbo or GPT-4
- References specific Articles and Sections

### 3. **User-Friendly Interface**
- Clean, modern design
- Mobile-responsive
- Two modes: Search and Ask
- Example queries to get started

## 🚀 Live Demo

**Coming Soon:** [Your Render URL will go here]

## 🛠️ Technology Stack

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Python, Flask
- **AI/ML**:
  - OpenAI text-embedding-ada-002 (embeddings)
  - OpenAI GPT-3.5 Turbo / GPT-4 (question answering)
- **Vector Database**: Pinecone
- **Data Storage**: Supabase (PostgreSQL)
- **Data Source**: Oklahoma State Courts Network (OSCN)

## 📊 How It Works

### Semantic Search Mode
1. User enters a search query (e.g., "voting rights")
2. Query is converted to a vector embedding using OpenAI
3. Pinecone finds the most semantically similar constitution sections
4. Results are displayed with relevance scores

### RAG Q&A Mode
1. User asks a question (e.g., "What are the voting rights in Oklahoma?")
2. System searches for 3 most relevant constitution sections
3. Relevant sections are sent to GPT-4 as context
4. GPT-4 generates a comprehensive answer with citations
5. Answer and sources are displayed to the user

## 🗂️ Project Structure

```
oklahoma-constitution-search/
├── app.py                      # Main Flask application
├── rag_search.py              # RAG (Retrieval-Augmented Generation) system
├── vector_database_builder.py # Vector database creation
├── supabase_client.py         # Database client
├── templates/
│   ├── index.html             # Main search interface
│   └── about.html             # About page
├── requirements.txt           # Python dependencies
├── Procfile                   # Production server config
├── runtime.txt                # Python version
├── config_production.py       # Production configuration
└── DEPLOYMENT.md              # Deployment instructions
```

## 🏃 Running Locally

### Prerequisites
- Python 3.11+
- Pinecone account & API key
- OpenAI account & API key
- Supabase account & credentials

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/oklahoma-constitution-search.git
cd oklahoma-constitution-search
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure API keys**
Create `pinecone_config.py`:
```python
PINECONE_API_KEY = "your_pinecone_key"
OPENAI_API_KEY = "your_openai_key"
INDEX_NAME = "oklahoma-constitution"
```

4. **Run the application**
```bash
python app.py
```

5. **Open your browser**
Navigate to `http://localhost:5000`

## 🌐 Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions to:
- Render (recommended, free tier)
- Railway
- Heroku

## 💰 Cost Estimates

### Hosting
- **Free Tier** (Render/Railway): $0/month

### API Usage (Pay-as-you-go)
- **Semantic Search**: ~$0.0001 per query
- **RAG with GPT-3.5**: ~$0.002 per question
- **RAG with GPT-4**: ~$0.02 per question

*For 100 questions/day using GPT-3.5: ~$6/month*

## 📈 Data

- **202 sections** of the Oklahoma Constitution indexed
- **1536-dimensional vectors** for each section
- **Data source**: Oklahoma State Courts Network (OSCN)

## 🎯 Use Cases

- **Citizens**: Research constitutional rights and government structure
- **Students**: Study Oklahoma government and civics
- **Legal Professionals**: Quick constitutional research
- **Journalists**: Fact-checking and research
- **Educators**: Teaching resource

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

## ⚠️ Disclaimer

This tool is for educational and informational purposes. For legal advice, consult a qualified attorney. The AI-generated answers should be verified against the official Oklahoma Constitution.

## 🙏 Acknowledgments

- Oklahoma State Courts Network (OSCN) for providing public access to constitution data
- OpenAI for GPT and embedding models
- Pinecone for vector database infrastructure
- Supabase for data storage

## 📧 Contact

For questions or feedback, please open an issue on GitHub.

---

Built with ❤️ for Oklahoma citizens

