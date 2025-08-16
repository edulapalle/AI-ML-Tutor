# 🚀 Vercel Deployment Guide for AI/ML Educational Platform

## 📋 Prerequisites

### 1. **Node.js 18+**
```bash
# Check your Node version
node --version

# If you have Node 16 or lower, update it:
# Option 1: Using nvm (recommended)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18

# Option 2: Download from nodejs.org
# Visit https://nodejs.org and download Node.js 18+
```

### 2. **Vercel Account**
- Go to [vercel.com](https://vercel.com)
- Sign up with GitHub (recommended)
- Free tier includes:
  - 100GB bandwidth
  - 1000 serverless function invocations
  - Unlimited static deployments

### 3. **GitHub Repository**
- Create a new repository on GitHub
- Push your code there (we'll do this below)

---

## 🔧 Step-by-Step Deployment

### **Step 1: Install Vercel CLI**

```bash
# Install Vercel CLI globally
npm install -g vercel

# Login to your Vercel account
vercel login
```

### **Step 2: Push Code to GitHub**

```bash
# Initialize git if not already done
git init

# Add all files
git add .

# Commit your code
git commit -m "Initial commit - AI/ML Educational Platform"

# Create GitHub repository and push
# (Replace YOUR_USERNAME and YOUR_REPO with your actual GitHub details)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

### **Step 3: Deploy to Vercel**

#### **Option A: Deploy via Vercel CLI (Recommended)**

```bash
# In your project directory
vercel

# Follow the prompts:
# ? Set up and deploy "rag-vercel-example"? [Y/n] y
# ? Which scope do you want to deploy to? [Your Account]
# ? Link to existing project? [y/N] n
# ? What's your project's name? ai-ml-education-platform
# ? In which directory is your code located? ./
```

#### **Option B: Deploy via Vercel Dashboard**

1. Go to [vercel.com/dashboard](https://vercel.com/dashboard)
2. Click "New Project"
3. Import your GitHub repository
4. Configure settings (see below)
5. Click "Deploy"

---

## ⚙️ Environment Variables Configuration

After deployment, you MUST configure these environment variables in Vercel:

### **Go to Vercel Dashboard → Your Project → Settings → Environment Variables**

Add all these variables:

#### **🤖 OpenAI Configuration**
```
OPENAI_API_KEY = your_openai_api_key
```

#### **🗄️ Supabase Configuration**
```
SUPABASE_URL = your_supabase_url
SUPABASE_ANON_KEY = your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY = your_service_role_key
JWT_SECRET_KEY = your_jwt_secret_key
```

#### **🔍 Milvus/Zilliz Cloud Configuration**
```
MILVUS_URI = your_milvus_uri
MILVUS_TOKEN = your_milvus_token
```

#### **📊 Neo4j Aura Configuration**
```
NEO4J_URI = your_neo4j_uri
NEO4J_USERNAME = your_neo4j_username
NEO4J_PASSWORD = your_neo4j_password
```

#### **📧 Email Configuration (Optional)**
```
SMTP_SERVER = smtp.gmail.com
SMTP_PORT = 587
EMAIL_USERNAME = your_email@gmail.com
EMAIL_PASSWORD = your_app_specific_password
FROM_EMAIL = your_email@gmail.com
FROM_NAME = AI Learning Platform
```

#### **🎥 YouTube API (Optional)**
```
YOUTUBE_API_KEY = your_youtube_api_key
```

---

## 🔧 Post-Deployment Setup

### **1. Test Your Deployment**

Visit your Vercel URL (e.g., `https://your-app.vercel.app`) and test:

```bash
# Health check
curl https://your-app.vercel.app/api/health

# Should return:
{
  "status": "healthy",
  "platform": "vercel",
  "features": ["rag_chat", "youtube_monitoring_serverless", ...]
}
```

### **2. Set Up Custom Domain (Optional)**

1. In Vercel Dashboard → Your Project → Settings → Domains
2. Add your custom domain
3. Configure DNS settings as instructed

### **3. Set Up Monitoring**

1. **Vercel Analytics**: Automatically enabled
2. **Error Tracking**: Check Vercel Dashboard → Functions tab
3. **Performance**: Monitor response times in dashboard

---

## 📊 Vercel-Specific Features

### **Serverless Functions**

Your app runs as serverless functions with these benefits:
- ✅ **Auto-scaling**: Handles traffic spikes automatically
- ✅ **Pay-per-use**: Only pay for actual usage
- ✅ **Global CDN**: Fast worldwide access
- ✅ **Zero maintenance**: No server management

### **YouTube Monitoring on Vercel**

Since Vercel doesn't support background processes, YouTube monitoring works via endpoints:

```bash
# Check for new videos
curl https://your-app.vercel.app/api/youtube/check

# Process new videos
curl -X POST https://your-app.vercel.app/api/youtube/process
```

### **Automatic Deployments**

Every push to your main branch triggers automatic deployment:
- ✅ **Preview deployments** for pull requests
- ✅ **Production deployments** for main branch
- ✅ **Rollback capability** if issues arise

---

## 🚨 Important Limitations

### **Vercel Constraints to Keep in Mind:**

1. **Function Timeout**: 10 seconds (Hobby), 300 seconds (Pro)
2. **Memory Limit**: 1024MB (Hobby), 3008MB (Pro)
3. **No Background Processes**: YouTube monitoring uses API endpoints
4. **Cold Starts**: First request may be slower

### **Solutions Implemented:**

1. **Timeout**: We use background tasks for long operations
2. **Memory**: Optimized data processing in chunks
3. **Background**: YouTube monitoring via cron jobs or manual triggers
4. **Cold Starts**: Minimal impact due to efficient app structure

---

## 🔄 Continuous Deployment Workflow

### **Development Workflow:**

```bash
# 1. Make changes locally
git add .
git commit -m "Add new feature"

# 2. Push to GitHub
git push origin main

# 3. Vercel auto-deploys in ~30 seconds
# 4. Check deployment status in Vercel dashboard
```

### **Environment Management:**

- **Production**: `main` branch → your-app.vercel.app
- **Staging**: `staging` branch → staging-your-app.vercel.app
- **Development**: Local development with `python app.py`

---

## 📈 Scaling and Performance

### **Free Tier Limits:**
- **Function Executions**: 100,000/month
- **Bandwidth**: 100GB/month
- **Build Time**: 6,000 minutes/month

### **When to Upgrade to Pro:**
- High traffic (>100K requests/month)
- Longer function execution times needed
- Need team collaboration features
- Want advanced analytics

---

## 🆘 Troubleshooting

### **Common Issues:**

#### **1. Build Failures**
```bash
# Check build logs in Vercel dashboard
# Common causes:
# - Missing dependencies in requirements.txt
# - Python version conflicts
# - Import errors
```

#### **2. Function Timeouts**
```bash
# Optimize long-running operations
# Use background tasks
# Consider splitting complex operations
```

#### **3. Environment Variable Issues**
```bash
# Ensure all variables are set in Vercel dashboard
# Check variable names match exactly
# Redeploy after adding new variables
```

#### **4. Database Connection Issues**
```bash
# Verify database URLs are accessible from Vercel
# Check firewall settings
# Test connections in function logs
```

---

## 📞 Support and Resources

### **Vercel Documentation:**
- [Vercel Python Guide](https://vercel.com/docs/functions/serverless-functions/runtimes/python)
- [Environment Variables](https://vercel.com/docs/concepts/projects/environment-variables)
- [Custom Domains](https://vercel.com/docs/concepts/projects/domains)

### **Getting Help:**
- **Vercel Support**: [vercel.com/support](https://vercel.com/support)
- **Community**: [GitHub Discussions](https://github.com/vercel/vercel/discussions)
- **Discord**: [Vercel Discord](https://vercel.com/discord)

---

## ✅ Deployment Checklist

Before going live, ensure:

- [ ] All environment variables configured in Vercel
- [ ] Database connections working
- [ ] Health check endpoint responding
- [ ] Authentication flow tested
- [ ] Email system configured (if using)
- [ ] Custom domain set up (optional)
- [ ] Monitoring and alerts configured
- [ ] Backup strategy in place

---

## 🎉 You're Ready to Deploy!

Your AI/ML Educational Platform is ready for production deployment on Vercel. The platform will be:

- ✅ **Globally accessible** via CDN
- ✅ **Auto-scaling** for traffic spikes  
- ✅ **Highly available** with 99.99% uptime
- ✅ **Secure** with HTTPS and modern security
- ✅ **Fast** with serverless optimization

Good luck with your deployment! 🚀
