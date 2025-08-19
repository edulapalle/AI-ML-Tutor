# Supabase Tables Usage Analysis

## ✅ **ACTIVELY USED TABLES** (DO NOT DELETE)

### 1. **`users`** 
- **Status**: ✅ CRITICAL - Core authentication
- **Usage**: User registration, login, profile management
- **Code locations**: `auth_service.py`, `app.py`
- **Data**: User profiles, goals (JSONB), interests

### 2. **`user_learning_path`**
- **Status**: ✅ ACTIVE - Learning tracking
- **Usage**: Tracks explored topics, learning history
- **Code locations**: `app.py` (store_user_topic, get_user_learning_history)
- **Data**: Topic exploration timeline

### 3. **`user_stars`**
- **Status**: ✅ ACTIVE - Bookmarks
- **Usage**: Star/bookmark functionality  
- **Code locations**: `app.py` (supabase_insert_star, supabase_select_stars)
- **Data**: User bookmarked content

### 4. **`progress_tracking`** 
- **Status**: ✅ ACTIVE - Progress monitoring
- **Usage**: Tracks learning proficiency and time spent
- **Code locations**: `app.py` (update_user_progress, get_user_progress_data)
- **Data**: Topic proficiency levels, study time

### 5. **`chat_history`**
- **Status**: ✅ ACTIVE - Conversation tracking
- **Usage**: Stores all chat conversations for agentic analysis
- **Code locations**: `app.py` (store_chat_message, get_user_chat_history)
- **Data**: User/assistant conversations, topics, quality ratings

---

## ❌ **UNUSED TABLES** (SAFE TO DELETE)

### 1. **`study_sessions`**
- **Status**: ❌ UNUSED - No active code references
- **Purpose**: Session-based learning tracking
- **Impact if deleted**: ⚠️ Moderate - chat_history has FK dependency
- **Recommendation**: Keep for now (see dependencies)

### 2. **`learning_goals`**
- **Status**: ❌ UNUSED - Only referenced in agentic system (commented out functionality)
- **Purpose**: Structured goal tracking
- **Code**: `agentic_learning_system.py` tries to fetch but gracefully handles failure
- **Impact if deleted**: ✅ Safe - uses users.current_goals JSONB instead
- **Recommendation**: Safe to delete

### 3. **`study_materials`**
- **Status**: ❌ UNUSED - No active code references
- **Purpose**: User's study resource management
- **Impact if deleted**: ✅ Safe - no dependencies
- **Recommendation**: Safe to delete

---

## 🔗 **DEPENDENCIES TO CONSIDER**

### Critical Dependencies:
1. **`chat_history.session_id`** → **`study_sessions.id`** (Foreign Key)
   - Currently set to NULL in code
   - If you delete `study_sessions`, need to modify `chat_history` schema

### Schema Modifications Needed:
```sql
-- If deleting study_sessions, first remove the FK constraint:
ALTER TABLE chat_history DROP CONSTRAINT chat_history_session_id_fkey;
ALTER TABLE chat_history ALTER COLUMN session_id DROP NOT NULL;
```

---

## 💡 **RECOMMENDATIONS**

### Option 1: **Clean Approach** (Recommended)
1. ✅ **Keep**: `users`, `user_learning_path`, `user_stars`, `progress_tracking`, `chat_history`
2. ❌ **Delete**: `learning_goals`, `study_materials` 
3. 🔄 **Modify**: Remove FK constraint from `chat_history.session_id` 
4. 🗑️ **Delete**: `study_sessions` after removing constraint

### Option 2: **Conservative Approach**
- Keep everything for future expansion
- Tables don't consume significant resources when empty
- Maintain schema flexibility

### Option 3: **Aggressive Cleanup**
- Delete all unused tables immediately
- Simplify to only actively used tables
- Modify chat_history schema

---

## 🚨 **SAFETY CONSIDERATIONS**

**Before deleting any tables:**
1. **Backup your database** 
2. **Test in development environment first**
3. **Check Supabase RLS policies** (some reference deleted tables)
4. **Update database schema file** to match production

**Tables safe to delete immediately:**
- `learning_goals` ✅
- `study_materials` ✅

**Tables requiring schema changes:**
- `study_sessions` ⚠️ (due to chat_history FK)

**Tables to NEVER delete:**
- `users` ❌
- `user_learning_path` ❌  
- `user_stars` ❌
- `progress_tracking` ❌
- `chat_history` ❌
