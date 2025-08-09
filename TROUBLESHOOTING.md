# Troubleshooting Guide - Authentication Issues

## 🚨 Common Issues and Solutions

### **Issue 1: `'NoneType' object has no attribute 'table'`**

**Error Message:**
```
Authentication error: 'NoneType' object has no attribute 'table'
```

**Cause:** Supabase is not properly configured or environment variables are missing.

**Solution:**
1. **Check your .env file:**
   ```bash
   # Make sure you have these variables set in your .env file
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_ANON_KEY=your_supabase_anon_key_here
   JWT_SECRET_KEY=your_jwt_secret_key_here
   ```

2. **Run the configuration test:**
   ```bash
   python test_supabase.py
   ```

3. **Verify Supabase setup:**
   - Create a Supabase project at https://supabase.com
   - Get your project URL and anon key from the project settings
   - Run the `database_schema.sql` script in your Supabase SQL editor

### **Issue 2: `email-validator is not installed`**

**Error Message:**
```
ImportError: email-validator is not installed, run `pip install pydantic[email]`
```

**Solution:**
```bash
# Install the missing dependency
uv pip install email-validator

# Or install all dependencies
uv pip install -r requirements.txt
```

### **Issue 3: 404 Errors for Missing Routes**

**Error Messages:**
```
INFO: 127.0.0.1:53596 - "GET /forgot-password HTTP/1.1" 404 Not Found
INFO: 127.0.0.1:53632 - "GET /terms HTTP/1.1" 404 Not Found
INFO: 127.0.0.1:53632 - "GET /privacy HTTP/1.1" 404 Not Found
```

**Solution:** These routes have been added to the application. The 404 errors should be resolved.

### **Issue 4: `uv pip install requirements.txt` Not Working**

**Problem:** Incorrect syntax for uv package manager.

**Correct Commands:**
```bash
# Install from requirements.txt
uv pip install -r requirements.txt

# Install individual packages
uv pip install fastapi uvicorn openai python-dotenv

# Install with specific version
uv pip install "fastapi>=0.100.0"
```

## 🔧 Setup Verification

### **Step 1: Environment Variables Check**

Run this command to verify your environment variables:
```bash
python test_supabase.py
```

Expected output:
```
🔍 Testing Environment Variables...
==================================================
Required variables:
   OPENAI_API_KEY: ✅ Set
   SUPABASE_URL: ✅ Set
   SUPABASE_ANON_KEY: ✅ Set
   JWT_SECRET_KEY: ✅ Set

🔍 Testing Supabase Configuration...
==================================================
SUPABASE_URL: ✅ Set
SUPABASE_ANON_KEY: ✅ Set

🔧 Testing Supabase client creation...
✅ Supabase client created successfully!

🔗 Testing Supabase connection...
✅ Supabase connection successful!
```

### **Step 2: Database Schema Check**

Make sure you've run the database schema in your Supabase project:

1. Go to your Supabase project dashboard
2. Navigate to SQL Editor
3. Run the contents of `database_schema.sql`
4. Verify the tables are created:
   - `users`
   - `study_sessions`
   - `chat_history`
   - `learning_goals`
   - `study_materials`
   - `progress_tracking`

### **Step 3: Application Test**

Start the application and test the endpoints:
```bash
python index.py
```

Then visit:
- http://localhost:8000/login
- http://localhost:8000/register

## 🛠️ Manual Testing

### **Test Registration**

1. **Open registration page:** http://localhost:8000/register
2. **Fill out the form** with test data:
   - Username: `testuser`
   - Email: `test@example.com`
   - Password: `testpassword123`
   - Date of Birth: `1990-01-01`
   - Current Stage: `college`
   - Study Level: `beginner`
   - Topics of Interest: Select a few options
   - Current Goals: `Learn Python programming`
3. **Submit the form**

### **Test Login**

1. **Open login page:** http://localhost:8000/login
2. **Enter credentials:**
   - Email: `test@example.com`
   - Password: `testpassword123`
3. **Submit the form**

## 🐛 Debug Mode

To enable debug mode and see more detailed error messages:

```python
# In index.py, change the FastAPI app initialization
app = FastAPI(
    title="AI Study Assistant",
    version="1.0.0",
    debug=True  # Enable debug mode
)
```

## 📞 Common Error Messages

### **Supabase Connection Errors**

```
❌ Supabase connection failed: [Errno 8] nodename nor servname provided, or not known
```
**Solution:** Check your `SUPABASE_URL` format. It should be: `https://your-project-id.supabase.co`

### **Authentication Errors**

```
❌ Error creating Supabase client: Invalid API key
```
**Solution:** Check your `SUPABASE_ANON_KEY` in the Supabase project settings.

### **Database Errors**

```
❌ relation "users" does not exist
```
**Solution:** Run the `database_schema.sql` script in your Supabase SQL editor.

## 🎯 Quick Fix Checklist

- [ ] ✅ Created `.env` file with correct credentials
- [ ] ✅ Installed all dependencies: `uv pip install -r requirements.txt`
- [ ] ✅ Set up Supabase project and ran database schema
- [ ] ✅ Verified environment variables with `python test_supabase.py`
- [ ] ✅ Started application: `python index.py`
- [ ] ✅ Tested registration and login

## 🔍 Still Having Issues?

If you're still experiencing problems:

1. **Check the logs** for detailed error messages
2. **Run the test script** to verify configuration
3. **Verify Supabase setup** in your project dashboard
4. **Check environment variables** are correctly set
5. **Ensure all dependencies** are installed

For additional help, please check the main README.md file or create an issue in the repository.

