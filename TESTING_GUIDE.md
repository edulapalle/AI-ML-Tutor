# Comprehensive Testing Guide

This guide covers all testing requirements for the RAG system, including functional tests, abuse protection, and data quality validation.

## 📋 Test Requirements Met

### ✅ Integration Tests (≥5 functional, ≥5 abuse)

**Functional Tests (5/5):**
1. "What is overfitting?" → explain intent
2. "Compare CNN vs RNN" → compare intent  
3. "Next after logistic regression?" → next intent
4. "Explain PCA" → explain intent
5. "Common DT mistakes" → explain intent

**Abuse Tests (5/5):**
1. 1k+ chars → 400 response
2. Prompt injection → 400 response
3. Non-ML topic → 400 response
4. Profanity → 403 response
5. Burst 10/sec → 429 response

### ✅ Data Quality Checks (2 per data source)

**Generated ML Concepts:**
1. Min/max length filter validation
2. Duplicate content detection

**StatQuest Videos:**
1. Empty/low-signal chunk filtering
2. Title/URL metadata completeness

## 🧪 Test Files Overview

### `test_rag_backend.py`
- **Purpose**: Basic RAG functionality tests
- **Tests**: Query endpoint, star endpoints, next endpoint, guardrails
- **Updated**: Now includes all 5 required functional test cases

### `test_abuse_protection.py`
- **Purpose**: Comprehensive abuse protection testing
- **Tests**: 
  - Long input protection (1k+ chars)
  - Prompt injection detection
  - Non-ML topic filtering
  - Profanity filtering (403 responses)
  - Rate limiting (burst protection)
  - Input validation edge cases

### `test_integration_comprehensive.py`
- **Purpose**: End-to-end system validation
- **Tests**:
  - System health checks
  - Authentication flow
  - RAG pipeline components
  - All functional requirements
  - All abuse scenarios
- **Features**: User creation, token management, comprehensive reporting

### `test_data_quality.py`
- **Purpose**: Data validation and quality assurance
- **Tests**:
  - Content length validation (50-5000 chars)
  - Duplicate detection using MD5 hashing
  - Empty content filtering
  - Metadata completeness (titles, URLs)
- **Collections**: Both `rich_ml_education` and `youtube_creator_videos`

### `run_all_tests.py`
- **Purpose**: Master test runner with reporting
- **Features**:
  - Runs all test suites sequentially
  - Comprehensive reporting and timing
  - Server status checking
  - Individual or complete suite execution
  - Success/failure analysis with recommendations

## 🚀 How to Run Tests

### Prerequisites
```bash
# Ensure your application is running
python app.py

# Install any missing dependencies
pip install requests pytest pytest-asyncio
```

### Individual Test Suites

```bash
# Basic RAG functionality
python test_rag_backend.py

# Abuse protection (will show failures until protection is implemented)
python test_abuse_protection.py

# Data quality validation
python test_data_quality.py

# Complete integration tests
python test_integration_comprehensive.py
```

### Master Test Runner

```bash
# Run all tests
python run_all_tests.py

# Run specific test suite
python run_all_tests.py --suite rag
python run_all_tests.py --suite abuse
python run_all_tests.py --suite data
python run_all_tests.py --suite integration

# Stop on first failure
python run_all_tests.py --stop-on-failure
```

## 📊 Expected Results (Current State)

### ✅ Likely to Pass:
- **RAG Backend Tests**: Should pass (basic functionality works)
- **Data Quality Tests**: Should mostly pass (data is generally good)
- **Integration Tests - Functional**: Should pass (core RAG works)

### ❌ Likely to Fail:
- **Abuse Protection Tests**: Will fail (protection not implemented yet)
- **Integration Tests - Abuse**: Will fail (protection not implemented yet)

## 🔧 Missing Components (Need Implementation)

The tests are comprehensive, but the following protection mechanisms need to be implemented:

### 1. Rate Limiting
```python
# Needed: FastAPI rate limiting middleware
# Should return 429 for >10 requests/second
```

### 2. Content Length Protection
```python
# Needed: Input validation middleware
# Should return 400 for >1000 character inputs
```

### 3. Prompt Injection Detection
```python
# Needed: AI-based or pattern-based injection detection
# Should return 400 for injection attempts
```

### 4. Profanity Filter
```python
# Needed: Content filtering system
# Should return 403 for profane content
```

### 5. Enhanced ML Topic Detection
```python
# Needed: Improved guardrails
# Should return 400 for clearly non-ML topics
```

## 📈 Performance Monitoring (Optional)

For latency/cost monitoring, you would add:

### Request Logging
```python
# Log per-request metrics:
# - tokens_in/out
# - retrieval_ms
# - rerank_ms  
# - llm_ms
# - total_ms
```

### Simple Caching
```python
# Cache on (user_id, normalized_query) for 5-15 min
# Reduce API costs for repeated queries
```

## 🎯 Next Steps

1. **Run the tests** to see current baseline
2. **Implement missing protection mechanisms** (see above)
3. **Re-run tests** to validate protection works
4. **Add performance monitoring** (optional)
5. **Deploy with confidence** once all tests pass

## 📞 Troubleshooting

### Common Issues:

**"Server not running"**
```bash
# Start the application first
python app.py
```

**"Connection refused"**
```bash
# Check if running on correct port
curl http://localhost:8000/api/health
```

**"Milvus connection failed"**
```bash
# Check your .env file has correct Milvus credentials
cat .env | grep MILVUS
```

**"Authentication failed"**
```bash
# Check Supabase credentials in .env
cat .env | grep SUPABASE
```

## 🏆 Success Criteria

Your system is production-ready when:

- ✅ All functional tests pass (5/5)
- ✅ All abuse protection tests pass (5/5)  
- ✅ All data quality tests pass (4/4)
- ✅ Integration test score ≥80%
- ✅ No critical security gaps

Run `python run_all_tests.py` to get your current score and recommendations!
