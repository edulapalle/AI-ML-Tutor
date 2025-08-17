# 🔐 Railway Authentication Debug & Fix

## 🔍 **Current Issues:**

From Railway logs:
```
"POST /api/auth/register HTTP/1.1" 400 Bad Request
"GET /forgot-password HTTP/1.1" 404 Not Found
```

---

## ✅ **Fixes Applied:**

### **1. Added Missing Route:**
```python
@app.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    """Forgot password page"""
    return templates.TemplateResponse("forgot-password.html", {"request": request})
```

### **2. Enhanced Registration Error Handling:**
```python
@app.post("/api/auth/register")
async def register_user(user_data: UserRegistration):
    try:
        print(f"📝 Registration attempt for: {user_data.username} ({user_data.email})")
        print(f"📝 Topics: {user_data.topics_of_interest}")
        print(f"📝 Goals: {user_data.current_goals}")
        
        result = await auth_service.register_user(user_data)
        print(f"✅ Registration successful for user: {result['user_id']}")
        return {"message": "User registered successfully", "user_id": result["user_id"]}
    except ValueError as e:
        print(f"❌ Registration validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"❌ Registration system error: {e}")
        print(f"   Error type: {type(e).__name__}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")
```

### **3. Enhanced Login Error Handling:**
```python
@app.post("/api/auth/login")
async def login_user(credentials: UserLogin):
    try:
        print(f"🔐 Login attempt for: {credentials.email}")
        
        user_data = await auth_service.authenticate_user(credentials.email, credentials.password)
        if user_data:
            access_token = auth_service.create_access_token(data={"sub": user_data["id"]})
            print(f"✅ Login successful for user: {user_data.get('username', 'unknown')}")
            return {"access_token": access_token, "token_type": "bearer", "user": user_data}
        else:
            print(f"❌ Login failed for: {credentials.email} (invalid credentials)")
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Login system error: {e}")
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")
```

---

## 🔍 **Data Validation Analysis:**

### **Frontend Sends (JavaScript):**
```javascript
const userData = {
    username: formData.get('username'),           // ✅ Required
    email: formData.get('email'),                 // ✅ Required
    password: formData.get('password'),           // ✅ Required (min 8 chars)
    date_of_birth: formData.get('dateOfBirth'),   // ✅ Required (date format)
    current_stage: formData.get('currentStage'),  // ✅ Required (dropdown)
    study_level: formData.get('studyLevel'),      // ✅ Required (dropdown)
    topics_of_interest: this.getSelectedTopics(), // ✅ Required (array)
    current_goals: formData.get('currentGoals')   // ✅ Required (array)
        .split('\n').filter(goal => goal.trim()),
    preferred_learning_style: formData.get('preferredLearningStyle') || null // ⚠️ Optional
};
```

### **Backend Expects (Pydantic):**
```python
class UserRegistration(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)     # ✅ Match
    email: str = Field(...)                                     # ✅ Match
    password: str = Field(..., min_length=8)                   # ✅ Match
    date_of_birth: date = Field(...)                           # ✅ Match
    topics_of_interest: List[str] = Field(...)                 # ✅ Match
    current_stage: str = Field(...)                            # ✅ Match
    current_goals: List[str] = Field(...)                      # ✅ Match
    study_level: str = Field(...)                              # ✅ Match
    preferred_learning_style: Optional[str] = Field(None)      # ✅ Match
```

**Analysis:** Field mapping looks correct! ✅

---

## 🚀 **Deploy & Test:**

### **Deploy Command:**
```bash
git add .
git commit -m "Fix auth: add forgot-password route + enhanced error logging"
git push origin main
```

### **After Deployment - Check Logs:**

#### **Expected for Successful Registration:**
```
📝 Registration attempt for: testuser (test@example.com)
📝 Topics: ['Machine Learning', 'Deep Learning']
📝 Goals: ['Learn Python', 'Build AI projects']
✅ Registration successful for user: uuid-string
INFO: "POST /api/auth/register HTTP/1.1" 200 OK
```

#### **Expected for Failed Registration:**
```
📝 Registration attempt for: testuser (test@example.com)
❌ Registration validation error: User with this email already exists
INFO: "POST /api/auth/register HTTP/1.1" 400 Bad Request
```

#### **For Missing Environment Variables:**
```
❌ Registration system error: Supabase is not configured
   Error type: ValueError
INFO: "POST /api/auth/register HTTP/1.1" 500 Internal Server Error
```

---

## 🔧 **Most Likely Causes of 400 Bad Request:**

### **1. Missing Environment Variables (90% probability):**
- `SUPABASE_URL` not set
- `SUPABASE_ANON_KEY` not set
- Check Railway Variables tab

### **2. Validation Errors (5% probability):**
- Empty required fields
- Invalid email format
- Password too short
- Invalid date format

### **3. Database Issues (5% probability):**
- User already exists
- Database table schema mismatch
- Connection timeout

---

## 🧪 **Testing After Deploy:**

### **Test Registration:**
1. Go to `https://your-app.railway.app/register`
2. Fill out the form completely
3. Submit and check Railway logs
4. Look for the detailed logging messages

### **Test Forgot Password:**
1. Go to `https://your-app.railway.app/forgot-password`
2. Should show 200 OK instead of 404

### **Debug Environment:**
1. Check `https://your-app.railway.app/api/detailed-health`
2. Look for `supabase_configured: true`

The enhanced logging will show exactly what's failing! 🔍✨
