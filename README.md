# AI Bootcamp Capstone Project - AI/ML Educational Platform

**Date**: August 2025  
**Author**: Santosh Edulapalle

## 🎯 Project Overview

An intelligent AI/ML educational platform that combines:
- **Child-friendly UI** with age-appropriate learning
- **RAG System** using Milvus/Zilliz Cloud for ML concept retrieval
- **YouTube Knowledge Graph** using Neo4j for video recommendations
- **Secure Authentication** with Supabase and JWT
- **Personalized Learning** based on user age and study preferences

## ✨ Key Features

### 🧠 **AI/ML Tutoring System**
- **RAG-powered responses** using Milvus vector database with 513 rich educational chunks
- **Child-friendly content** including definitions, analogies, examples, mistakes, quizzes, and related concepts
- **Age-appropriate explanations** for different learning levels
- **Content guardrails** ensuring ML/AI focus only
- **Conversation continuity** with context awareness
- **Production-ready dataset** generated using OpenAI with comprehensive ML/AI coverage

### 🎥 **YouTube Knowledge Graph**
- **Multi-channel scraping** of high-profile AI/ML channels
- **Intelligent keyword extraction** prioritizing ML/AI terms
- **Neo4j storage** with rich metadata and relationships
- **Video recommendations** based on keyword similarity

### 🔐 **Secure User Management**
- **JWT authentication** with Supabase backend
- **User profiles** with ML/AI topics of interest
- **Study method preferences** (Study Only, Study+Test, Study+Demo)
- **Age-based personalization** for learning content

### 🎨 **Child-Friendly Interface**
- **Bright, engaging design** with animations
- **Simplified navigation** and quick actions
- **Personalized dashboard** showing user progress
- **Responsive design** for all devices

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Neo4j Aura Cloud instance
- Milvus/Zilliz Cloud instance
- OpenAI API key
- Supabase project

### Installation

1. **Clone and setup virtual environment**
```bash
git clone <repository-url>
cd rag-vercel-example
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**
Create a `.env` file with:
```env
# OpenAI
OPENAI_API_KEY=your_openai_key

# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
JWT_SECRET_KEY=your_jwt_secret

# Milvus/Zilliz Cloud
MILVUS_URI=your_milvus_uri
MILVUS_TOKEN=your_milvus_token
MILVUS_COLLECTION=ml_concepts

# Neo4j Aura
NEO4J_URI=your_neo4j_uri
NEO4J_USERNAME=your_username
NEO4J_PASSWORD=your_password

# SSL Certificates (for corporate environments)
SSL_CERT_FILE=/path/to/corp_root_ca.pem
REQUESTS_CA_BUNDLE=/path/to/corp_root_ca.pem
```

4. **Setup database**
```bash
# Run Supabase schema
# Copy database_schema.sql content to Supabase SQL Editor

# Populate ML concepts
python populate_ml_concepts.py

# Setup Neo4j schema (automatic with scraper)
```

5. **Run the application**
```bash
python index.py
```

## 📊 Current System Status

### 🧠 **RAG System (Milvus)**
- ✅ **Connected**: Zilliz Cloud integration
- ✅ **Production Dataset**: 513 rich educational chunks in `rich_ml_education` collection
- ✅ **Content Types**: Definitions, analogies, examples, mistakes, quizzes, related concepts
- ✅ **Embeddings**: OpenAI text-embedding-3-small (1536 dimensions)
- ✅ **Coverage**: 42 comprehensive ML/AI concepts
- ✅ **Functional**: Age-appropriate responses
- ✅ **Guardrails**: Content filtering active

### 🎥 **YouTube Knowledge Graph (Neo4j)**
- ✅ **Connected**: Neo4j Aura Cloud
- ✅ **Channels**: 3 working channels
- ✅ **Videos**: 91 educational videos
- ✅ **Keywords**: 640 ML/AI keywords
- ✅ **Relationships**: 1,373 keyword connections

#### **Working Channels:**
1. **3Blue1Brown** (30 videos) - Mathematics & Computer Science
2. **StatQuest** (30 videos) - Statistics & Machine Learning  
3. **Two Minute Papers** (30 videos) - AI Research Papers

### 🔐 **Authentication System**
- ✅ **Supabase**: PostgreSQL backend
- ✅ **JWT**: Secure token management
- ✅ **User Profiles**: ML/AI focused registration
- ✅ **Security**: Password hashing, RLS policies

## 🛠️ Utility Scripts

### **Core Application**
- `index.py` - Main FastAPI application
- `rag_system.py` - RAG system with Milvus
- `auth_service.py` - Authentication logic
- `auth_models.py` - User data models

### **YouTube Scraping**
- `youtube_channel_scraper.py` - Multi-channel video scraper
- `youtube_single_scraper.py` - Single video scraper
- `run_scraper.sh` - Bash wrapper with SSL certificates

### **RAG Management**
- `populate_ml_concepts.py` - Populate Milvus with basic ML concepts (legacy)
- `check_ml_concepts.py` - Check Milvus collection status
- `cleanup_ml_concepts.py` - Clean up Milvus collection

### **Rich Dataset Generation**
- `generate_dataset.py` - Generate rich educational content using OpenAI
- `create_rich_milvus_collection.py` - Create new collection for rich content
- `load_rich_concepts_to_milvus_new.py` - Load rich content to production collection
- `concepts.json` - Curated list of 42 ML concepts
- `ml_analogies.jsonl` - Generated rich educational dataset (513 chunks)

### **Testing & Debugging**
- `test_rag_retrieval.py` - Test RAG system responses
- `test_guardrails.py` - Test content filtering
- `test_conversation_fix.py` - Test conversation flow
- `neo4j_basic_read.py` - Read Neo4j knowledge graph
- `rag_backend.py` - **Main RAG Backend API** (unified query pipeline)
- `run_rag_backend.py` - Start RAG backend server
- `test_rag_backend.py` - Test all RAG backend endpoints
- `user_stars_schema.sql` - Database schema for star functionality

## 🔧 Usage Examples

### **RAG Backend API**
```bash
# Start the RAG backend server (all databases integrated)
python run_rag_backend.py

# Test all endpoints (query, star, next)
python test_rag_backend.py

# Access interactive API documentation
open http://localhost:8000/docs
```

### **Generate Rich Educational Dataset**
```bash
# Generate rich content for all 42 ML concepts (one-time setup)
python generate_dataset.py --concepts concepts.json --out ml_analogies.jsonl --variants 3

# Create new Milvus collection for rich content
python create_rich_milvus_collection.py

# Load rich content to production collection
python load_rich_concepts_to_milvus_new.py
```

### **Scrape YouTube Channels**
```bash
# Scrape all working channels (30 videos each)
python youtube_channel_scraper.py

# Scrape single video
python youtube_single_scraper.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

### **Check System Status**
```bash
# Check Milvus RAG system
python check_ml_concepts.py

# Check Neo4j knowledge graph
python neo4j_basic_read.py

# Test RAG responses
python test_rag_retrieval.py
```

### **Populate ML Concepts**
```bash
# Initial population
python populate_ml_concepts.py

# Force repopulate
python populate_ml_concepts.py --force
```

## 🏗️ Project Structure

```
rag-vercel-example/
├── index.py                 # Main FastAPI application
├── rag_system.py           # RAG system with Milvus
├── youtube_channel_scraper.py  # Multi-channel YouTube scraper
├── youtube_single_scraper.py   # Single video scraper
├── auth_service.py         # Authentication service
├── auth_models.py          # User data models
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not in git)
├── templates/              # HTML templates
├── static/                 # CSS, JS, assets
├── README.md              # This file
└── DEVELOPMENT_NOTES.md   # Development progress log
```

## 🔒 Security Features

- **Environment variables** for all sensitive data
- **JWT tokens** for secure authentication
- **Password hashing** with bcrypt
- **Row-level security** in Supabase
- **SSL certificate** handling for corporate environments

## 🚀 Deployment

### **Vercel Deployment**
- Configured with `vercel.json`
- Environment variables in Vercel dashboard
- Automatic deployments from main branch

### **Local Development**
- FastAPI development server on port 8000
- Hot reload for development
- Virtual environment isolation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📚 Technologies Used

- **Backend**: FastAPI, Python
- **Database**: Supabase (PostgreSQL), Neo4j Aura
- **Vector DB**: Milvus/Zilliz Cloud
- **AI**: OpenAI GPT models
- **Frontend**: HTML, CSS, JavaScript
- **Authentication**: JWT, Supabase Auth
- **YouTube Scraping**: yt-dlp, youtube-transcript-api

## 🆘 Support

- **Documentation**: Check `DEVELOPMENT_NOTES.md` for recent updates
## 🔧 SSL Certificate Configuration

### **Important Discovery: Python SSL Certificate Path Issue**

If you encounter SSL certificate errors with OpenAI API on macOS:

```bash
# Error: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed
# Root cause: Python looking for certificates in wrong location
```

**Solution:**
```bash
export SSL_CERT_FILE=/etc/ssl/cert.pem
export REQUESTS_CA_BUNDLE=/etc/ssl/cert.pem
```

This is automatically configured in our scripts, but may be needed for other Python SSL issues.

## 🚨 Troubleshooting

- **Troubleshooting**: See `TROUBLESHOOTING.md` for common issues
- **Issues**: Create GitHub issues for bugs or feature requests

## 📈 Roadmap

- [ ] **ML Concept Relationships** in Neo4j
- [ ] **Video Recommendation System** using keyword similarity
- [ ] **Learning Paths** and prerequisites
- [ ] **More YouTube Channels** (Lex Fridman, DeepMind, etc.)
- [ ] **Advanced Analytics** and progress tracking
- [ ] **Mobile App** development

---

**Last Updated**: August 13, 2025  
**Status**: ✅ **YouTube Knowledge Graph Active** | ✅ **RAG System Operational** | ✅ **Authentication Working** 