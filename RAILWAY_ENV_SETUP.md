# 🚂 Railway Environment Variables Setup

## 🔧 **Required Environment Variables**

### **Critical Variables (App Won't Work Without These):**

```env
# OpenAI API (Required for AI chat)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Database (Required for user auth)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# JWT Authentication (Required for login)
JWT_SECRET_KEY=your-super-secret-jwt-key-here
```

### **Optional Variables (For Full Features):**

```env
# Vector Database (For advanced RAG)
MILVUS_URI=https://your-milvus-instance.zillizcloud.com
MILVUS_TOKEN=your-milvus-token

# Knowledge Graph (For concept relationships)
NEO4J_URI=neo4j+s://your-instance.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-neo4j-password

# Email System (For weekly reports)
SENDGRID_API_KEY=SG.your-sendgrid-api-key
FROM_EMAIL=noreply@yourdomain.com
FROM_NAME=AI Learning Platform

# Railway-specific (Auto-configured)
RAILWAY_ENVIRONMENT_NAME=production
RAILWAY_PUBLIC_DOMAIN=https://your-app.railway.app
PORT=8000
```

---

## 🚀 **How to Add Variables in Railway**

### **Method 1: Railway Dashboard**
1. Go to your Railway project
2. Click on "Variables" tab
3. Click "New Variable"
4. Add name and value
5. Click "Add"
6. Redeploy

### **Method 2: Railway CLI**
```bash
# Set individual variables
railway variables set OPENAI_API_KEY="sk-your-key"
railway variables set SUPABASE_URL="https://your-project.supabase.co"

# Set from .env file
railway variables set --file .env
```

---

## 🔍 **How to Get Each API Key**

### **1. OpenAI API Key**
```bash
1. Go to https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Copy the key (starts with sk-)
4. Add to Railway as OPENAI_API_KEY
```

### **2. Supabase Keys**
```bash
1. Go to https://supabase.com/dashboard
2. Select your project
3. Go to Settings > API
4. Copy "URL" → SUPABASE_URL
5. Copy "anon public" → SUPABASE_ANON_KEY
6. Copy "service_role" → SUPABASE_SERVICE_ROLE_KEY
```

### **3. JWT Secret Key**
```bash
# Generate a random secret
openssl rand -hex 32

# Or use any random string
python -c "import secrets; print(secrets.token_hex(32))"
```

### **4. SendGrid API Key (Optional)**
```bash
1. Go to https://sendgrid.com
2. Sign up for free account
3. Go to Settings > API Keys
4. Create API key with Mail Send permissions
5. Copy key → SENDGRID_API_KEY
```

---

## 🎯 **Test After Setup**

### **Check Environment Variables**
```bash
# Visit your app's health endpoint
https://your-app.railway.app/api/health

# Should show:
{
  "status": "healthy",
  "services": {
    "openai": {"status": "available"},
    "supabase": {"status": "connected"}
  }
}
```

### **Test Frontend**
```bash
# Visit your app
https://your-app.railway.app/

# Should show beautiful UI with:
✅ Colorful gradient background
✅ Header with AI/ML Tutor logo
✅ Three-panel layout
✅ Working chat interface
```

---

## ⚠️ **Common Issues & Fixes**

### **CSS Not Loading**
- ✅ Check browser dev tools for 404 errors
- ✅ Verify static files are deployed
- ✅ Check CORS and security headers

### **OpenAI Errors**
- ✅ Verify API key is valid
- ✅ Check OpenAI account has credits
- ✅ Test key: `curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models`

### **Database Errors**
- ✅ Verify Supabase URL and keys
- ✅ Check if Row Level Security is disabled
- ✅ Ensure user_profiles table exists

### **Health Check Fails**
- ✅ Check Railway build logs
- ✅ Verify all critical env vars are set
- ✅ Test `/api/health` endpoint

---

## 🔐 **Security Notes**

1. **Never commit real API keys** to git
2. **Use Railway's environment variables** for all secrets
3. **HTTPS is enforced** automatically in production
4. **CORS is configured** for your Railway domain
5. **Security headers** are added automatically

---

## 📞 **Need Help?**

If you're still having issues:

1. **Check Railway logs:**
   - Go to project → Deployments → Latest → Build/Deploy logs

2. **Test health endpoint:**
   - `curl https://your-app.railway.app/api/health`

3. **Check browser console:**
   - F12 → Console tab for frontend errors

4. **Verify environment variables:**
   - Railway dashboard → Variables tab

Share the results of these checks for specific help! 🚂✨
