# Vercel Deployment Setup with YouTube Monitoring

## 🚀 **Vercel-Optimized Architecture**

Since Vercel is serverless, we've redesigned the YouTube monitoring as **API endpoints** instead of background processes:

### **🔄 How It Works on Vercel:**

1. **Main App**: Your existing RAG application runs normally
2. **YouTube Monitoring**: Triggered via API endpoints (not background process)
3. **State Storage**: Uses Supabase instead of local files
4. **Automation**: External cron service calls monitoring endpoints

## 📋 **Deployment Steps**

### **1. Supabase Setup**
```sql
-- Run this in your Supabase SQL Editor
-- (Content from VERCEL_SUPABASE_SETUP.sql)
```

### **2. Vercel Environment Variables**
Set these in your Vercel dashboard (Settings → Environment Variables):

```
OPENAI_API_KEY=your_openai_key
YOUTUBE_API_KEY=your_youtube_key  
MILVUS_URI=your_milvus_uri
MILVUS_TOKEN=your_milvus_token
NEO4J_URI=your_neo4j_uri
NEO4J_PASSWORD=your_neo4j_password
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_key
JWT_SECRET_KEY=your_jwt_secret
```

### **3. Deploy to Vercel**
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel --prod
```

## 🔄 **YouTube Monitoring on Vercel**

### **Available Endpoints:**

| Endpoint | Method | Purpose | Usage |
|----------|--------|---------|-------|
| `/api/youtube/check` | GET | Check for new videos | Manual or cron |
| `/api/youtube/process` | POST | Process new videos | Manual or cron |
| `/api/youtube/status` | GET | Monitor status | Health check |

### **Manual Monitoring:**
```bash
# Check for new videos
curl https://your-app.vercel.app/api/youtube/check

# Process new videos  
curl -X POST https://your-app.vercel.app/api/youtube/process
```

## ⏰ **Automated Monitoring Options**

### **Option 1: Vercel Cron (Recommended)**

Create `vercel.json` with cron:
```json
{
  "crons": [
    {
      "path": "/api/youtube/process",
      "schedule": "0 */30 * * * *"
    }
  ]
}
```

### **Option 2: External Cron Service**

Use services like:
- **cron-job.org** (free)
- **EasyCron** 
- **GitHub Actions**

Example GitHub Actions (`.github/workflows/youtube-monitor.yml`):
```yaml
name: YouTube Monitor
on:
  schedule:
    - cron: '0 */30 * * *'  # Every 30 minutes
  workflow_dispatch:

jobs:
  monitor:
    runs-on: ubuntu-latest
    steps:
      - name: Check YouTube
        run: |
          curl -X POST https://your-app.vercel.app/api/youtube/process
```

### **Option 3: Zapier/IFTTT**
- Create automation that calls your endpoint every 30 minutes

## 🔍 **Monitoring & Debugging**

### **Check Status:**
```bash
curl https://your-app.vercel.app/api/youtube/status
```

### **View Logs:**
```bash
vercel logs your-app-url
```

### **Supabase Dashboard:**
- Monitor `youtube_processed_videos` table
- Check processing history

## 📊 **Differences from Local Setup**

| Feature | Local Setup | Vercel Setup |
|---------|-------------|--------------|
| **Process Type** | Background service | API endpoints |
| **State Storage** | `processed_videos.json` | Supabase table |
| **Triggering** | Automatic (30 min timer) | Manual/Cron calls |
| **Monitoring** | File logs | Vercel logs + Supabase |
| **Scaling** | Single process | Serverless functions |

## ✅ **Advantages of Vercel Setup**

- ✅ **Serverless**: Auto-scaling, no server management
- ✅ **Reliable**: Vercel's infrastructure reliability
- ✅ **Cost-Effective**: Pay per execution
- ✅ **Integrated**: Everything in one deployment
- ✅ **Monitorable**: Clear API endpoints for monitoring

## 🚀 **Quick Start**

1. **Setup Supabase table** (run SQL from `VERCEL_SUPABASE_SETUP.sql`)
2. **Deploy to Vercel** with updated `vercel.json`
3. **Set environment variables** in Vercel dashboard
4. **Setup cron** (GitHub Actions or external service)
5. **Test endpoints** manually first

Your YouTube monitoring will then run automatically on Vercel! 🎯
