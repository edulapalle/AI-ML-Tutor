# Milvus Setup Guide for RAG System

## ☁️ Recommended: Zilliz Cloud (Managed Milvus)

### 1. Create Zilliz Cloud Account
1. Go to [Zilliz Cloud](https://cloud.zilliz.com/)
2. Sign up for a free account
3. Create a new cluster

### 2. Get Connection Details
1. In your Zilliz dashboard, copy:
   - **Public Endpoint** (your MILVUS_URI)
   - **Token** (your MILVUS_TOKEN)

### 3. Configure .env
```env
# Zilliz Cloud Configuration
MILVUS_URI=https://your-cluster-id.zillizcloud.com:port
MILVUS_TOKEN=your_token_here
```

## 🐳 Alternative: Local Docker Setup (Not Recommended)

### 1. Install Docker
Make sure Docker is installed and running on your system.

### 2. Download Milvus Docker Compose
```bash
# Download the docker-compose.yml
curl -O https://github.com/milvus-io/milvus/releases/download/v2.3.3/milvus-standalone-docker-compose.yml

# Rename for convenience
mv milvus-standalone-docker-compose.yml docker-compose.yml
```

### 3. Start Milvus
```bash
# Start Milvus (this will download necessary images first time)
docker-compose up -d

# Check if containers are running
docker-compose ps
```

### 4. Verify Installation
```bash
# Check Milvus logs
docker-compose logs milvus-standalone

# Test connection (should show "Milvus standalone is running")
curl -X GET "http://localhost:19530/health"
```

## 🔧 Environment Configuration

Make sure your `.env` file contains:
```env
# Zilliz Cloud Configuration (Recommended)
MILVUS_URI=https://your-cluster-id.zillizcloud.com:port
MILVUS_TOKEN=your_zilliz_cloud_token_here

# Local Docker Setup (Alternative - not recommended)
# MILVUS_HOST=localhost
# MILVUS_PORT=19530
```

## 🚀 Starting the AI Study Assistant

1. **Install dependencies:**
```bash
source .venv/bin/activate
uv pip install -r requirements.txt
```

2. **Start the application:** (No local setup needed with Zilliz Cloud!)
```bash
source .venv/bin/activate
python index.py
```

4. **Check system status:**
   - Go to http://localhost:8000/settings
   - Verify all components show green ✅ status

## 🧪 Test the RAG System

Try asking these questions in the chat:
- "What is machine learning?"
- "Explain neural networks like I'm 10 years old"
- "How does supervised learning work?"
- "What's the difference between classification and regression?"

## 🛠️ Troubleshooting

### Milvus Connection Issues
```bash
# Check if Milvus is running
docker-compose ps

# Restart Milvus
docker-compose restart

# Check logs for errors
docker-compose logs milvus-standalone
```

### Dependencies Issues
```bash
# Reinstall ML dependencies
uv pip install pymilvus sentence-transformers

# Check Python version (requires 3.8+)
python --version
```

### Memory Issues
Milvus requires at least 4GB RAM. If you have memory constraints:
```bash
# Stop other Docker containers
docker stop $(docker ps -q)

# Or use Zilliz Cloud (managed service) instead
```

## 📊 Collection Information

- **Collection Name:** `ml_concepts`
- **Embedding Dimension:** 384 (sentence-transformers/all-MiniLM-L6-v2)
- **Metric Type:** COSINE similarity
- **Index Type:** IVF_FLAT for efficient search

The collection is automatically created and populated when you first start the application.
