"""
Advanced Guardrails System for AI/ML Educational Platform
========================================================

Multi-layered protection system with:
1. Input hygiene & sanitization
2. Follow-up allowance for natural conversation 
3. Jailbreak/prompt-injection detection
4. ML-only scope filtering (keyword + LLM-based)
5. OpenAI moderation for safety

Provides reliable, fast, and comprehensive content filtering.
"""
import re
import time
import os
from typing import Tuple, Optional, Dict, Any
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Guardrail configurations
FOLLOW_UP = {"yes","ok","okay","continue","next","more","example","details","go on","tell me more"}

DENY_PATTERNS = [
    r"(?i)\b(ignore (all|previous|above)|system prompt|developer mode)\b",
    r"(?i)\b(jailbreak|bypass|override|hack|crack)\b",
    r"(?i)\b(act as|pretend to be|roleplay as)\b",
    r"(?i)\b(previous instructions|initial prompt|system message)\b",
]

NON_ML_TOPICS = [
    "recipe","cooking","celebrity","politics","dating","religion",
    "sports betting","stock tips","movie spoilers","travel itinerary",
    "weather","news","gossip","fashion","shopping","entertainment"
]

ML_KEYWORDS = [
    "machine learning","ml","ai","artificial intelligence","deep learning","neural","transformer",
    "embedding","vector","rag","pca","regression","classification","clustering",
    "xgboost","cnn","rnn","bert","gpt","dataset","overfitting","underfitting",
    "bias variance","cross validation","confusion matrix","roc","auc","llm",
    "supervised","unsupervised","reinforcement","gradient","optimization",
    "algorithm","model","training","testing","prediction","feature","label"
]

# Common greetings and casual phrases that should be handled politely  
GREETINGS = {"hi","hello","hey","thanks","thank you","bye","goodbye","good morning","good afternoon","what's up","whats up","sup","how are you","howdy"}

def sanitize(text: str) -> str:
    return (text or "").strip()

def too_long(text: str, max_len: int = 800) -> bool:
    return len(text) > max_len

def is_followup(text: str) -> bool:
    """Check if text is a simple conversation follow-up (exact matches only)"""
    t = text.lower().strip()
    # Only allow EXACT matches for follow-ups, not partial matches
    return t in FOLLOW_UP

def hits_deny_patterns(text: str) -> bool:
    return any(re.search(p, text) for p in DENY_PATTERNS)

def is_greeting(text: str) -> bool:
    """Check if text is a simple greeting"""
    t = text.lower().strip()
    return t in GREETINGS

def is_in_educational_context(text: str, conversation_history: Optional[list] = None) -> bool:
    """Check if user is responding to a quiz, giving answers, or in educational conversation"""
    if not conversation_history:
        return False
    
    # Look at recent assistant messages for educational context
    recent_messages = conversation_history[-3:] if len(conversation_history) >= 3 else conversation_history
    
    for msg in recent_messages:
        if msg.get("role") == "assistant":
            content = msg.get("content", "").lower()
            # Check if assistant recently asked educational questions or gave quizzes
            if any(keyword in content for keyword in [
                "quiz", "question", "which", "what is", "choose", "select", 
                "true or false", "correct answer", "explain", "define",
                "example", "compare", "learning", "study", "understand",
                "neural network", "machine learning", "algorithm", "model",
                "data", "training", "prediction", "classification"
            ]):
                return True
    
    # Check if current message looks like an educational response
    t = text.lower().strip()
    
    # Common quiz answer patterns
    quiz_patterns = [
        # Multiple choice answers
        r"^[a-d]$", r"^option [a-d]$", r"^choice [a-d]$",
        # Short technical terms (common in ML)
        r"^(cnn|rnn|lstm|gru|bert|gpt|svm|knn|pca|nlp|ai|ml)$",
        # Yes/No answers
        r"^(yes|no|true|false|correct|incorrect)$",
        # Numbers (for technical questions)
        r"^\d+$", r"^\d+\.\d+$",
        # Common ML terms as answers
        r"^(neural network|deep learning|supervised|unsupervised|regression|classification)$"
    ]
    
    import re
    for pattern in quiz_patterns:
        if re.match(pattern, t):
            return True
    
    # Check for short answers that might be technical terms
    if len(t.split()) <= 3 and any(keyword in t for keyword in [
        "network", "learning", "model", "algorithm", "data", "training",
        "prediction", "feature", "layer", "activation", "gradient", "loss",
        "accuracy", "precision", "recall", "overfitting", "underfitting"
    ]):
        return True
    
    return False

def cheap_ml_scope(text: str) -> bool:
    """Fast keyword-based ML scope check"""
    t = text.lower()
    
    # Explicit ML keywords always pass
    if any(k in t for k in ML_KEYWORDS):
        return True
    
    # Obvious non-ML topics fail
    if any(w in t for w in NON_ML_TOPICS):
        return False
    
    # Question patterns need ML context to pass
    if any(p in t for p in ["what is","how does","explain","difference","compare","when to use"]):
        # Only allow if has some ML-adjacent context
        ml_context = ["learning","model","algorithm","data","prediction","analysis","intelligence","automation"]
        if any(ctx in t for ctx in ml_context):
            return True
        else:
            return False  # Generic questions without ML context fail
    
    # Default: reject (was permissive before, now strict)
    return False

# Optional: embedding-based scope (fast + robust)
def ml_scope_embedding(similarity: float, threshold: float = 0.55) -> bool:
    return similarity >= threshold

# LLM-based scope checking (most reliable)
def llm_scope_label(text: str) -> bool:
    """Use GPT to classify if query is ML-related"""
    try:
        system_prompt = """You are a content classifier for an AI/ML educational platform. 
Your job is to determine if a user's question is related to machine learning, artificial intelligence, data science, or related technical topics.

Respond with exactly one word:
- "ML" if the question is about machine learning, AI, data science, algorithms, programming, statistics, or technical topics
- "NONML" if the question is about unrelated topics like cooking, entertainment, personal advice, etc.

Examples:
- "What is machine learning?" → ML
- "How do neural networks work?" → ML  
- "What's the weather like?" → NONML
- "Hey" → NONML
- "Tell me about cooking" → NONML"""

        user_prompt = f"Question: {text}"
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            max_tokens=5,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        label = (response.choices[0].message.content or "").strip().upper()
        return label == "ML"
        
    except Exception as e:
        print(f"⚠️ LLM scope check failed: {e}")
        # Fallback to keyword-based check
        return cheap_ml_scope(text)

# Fallback LLM with strict ML-only system prompt
def fallback_ml_response(text: str, user_age_group: str = "adult") -> str:
    """
    Generate ML-focused response using LLM with strict system prompt
    This ensures we only provide ML/AI educational content
    """
    try:
        # Adjust tone based on user age
        if user_age_group == "child":
            tone = "simple, kid-friendly language with fun analogies"
            audience = "a curious child"
        elif user_age_group == "teen":
            tone = "engaging, age-appropriate language with practical examples"
            audience = "a teenager"
        else:
            tone = "clear, professional language with technical depth"
            audience = "an adult learner"

        system_prompt = f"""You are an AI/ML educational assistant for {audience}. You MUST follow these strict guidelines:

1. ONLY answer questions related to:
   - Machine Learning, AI, Data Science
   - Algorithms, programming, statistics
   - Technical concepts and educational topics

2. If the question is NOT clearly about ML/AI/tech:
   - Politely redirect to ML topics
   - Suggest a related ML concept they might find interesting
   - DO NOT answer off-topic questions

3. Use {tone} and keep responses educational and helpful.

4. If unsure whether something is ML-related, err on the side of redirection.

Examples:
- "What should I study now?" → Suggest ML learning paths
- "How do I get better?" → Assume they mean at ML and suggest practice methods
- "What's for dinner?" → Redirect: "I can help with ML topics! How about learning about recommendation algorithms that food apps use?"
"""

        user_prompt = f"Question: {text}"
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=500,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        return response.choices[0].message.content or "I'm here to help with AI and machine learning topics. What would you like to learn?"
        
    except Exception as e:
        print(f"⚠️ Fallback LLM failed: {e}")
        return "I specialize in AI and machine learning! Please ask me about topics like neural networks, algorithms, data science, or any ML concepts you'd like to understand."

# OpenAI moderation check
def check_moderation(text: str) -> Tuple[bool, str]:
    """Check content against OpenAI moderation policies"""
    try:
        response = openai_client.moderations.create(input=text)
        result = response.results[0]
        
        if result.flagged:
            categories = [cat for cat, flagged in result.categories.dict().items() if flagged]
            return False, f"Content policy violation: {', '.join(categories)}"
        
        return True, "Content passed moderation"
        
    except Exception as e:
        print(f"⚠️ Moderation check failed: {e}")
        # Fail open (allow content if moderation service is down)
        return True, "Moderation service unavailable"

def guardrail_result(allowed: bool, reason: str, http_status: int = 400):
    return {"allowed": allowed, "reason": reason, "http_status": http_status}

async def run_guardrails(
    text: str,
    *,
    conversation_history: Optional[list] = None,
    max_len: int = 800,
    use_llm_scope: bool = True,  # Default to True for better accuracy
    use_moderation: bool = True,  # Default to True for safety
    embedding_similarity: Optional[float] = None
) -> Dict[str, Any]:
    """
    Run comprehensive guardrails on user input
    
    Args:
        text: User input text
        conversation_history: Optional list of previous conversation messages for context
        max_len: Maximum allowed text length
        use_llm_scope: Whether to use LLM for scope checking (most accurate)
        use_moderation: Whether to run OpenAI moderation
        embedding_similarity: Optional embedding similarity score
    
    Returns:
        Dict with 'allowed', 'reason', and optional 'http_status', 'latency_ms'
    """
    t0 = time.time()
    
    # 1. Input hygiene
    q = sanitize(text)
    if not q:
        return guardrail_result(False, "Empty prompt.")
    
    if too_long(q, max_len):
        return guardrail_result(False, f"Prompt too long (> {max_len} chars).")
    
    # 2. Handle greetings politely
    if is_greeting(q):
        return guardrail_result(False, "Hello! 👋 I'm your AI/ML learning assistant. I can help you understand machine learning, deep learning, data science, and AI concepts. What would you like to learn about today?")
    
    # 3. Allow conversation follow-ups
    if is_followup(q):
        return guardrail_result(True, "Conversation follow-up.")
    
    # 3.5. Check if user is in educational context (quiz answers, etc.)
    if is_in_educational_context(q, conversation_history):
        latency_ms = int((time.time() - t0) * 1000)
        return {
            "allowed": True, 
            "reason": "Educational context - quiz answer or learning response", 
            "latency_ms": latency_ms
        }
    
    # 4. Check for prompt injection attempts
    if hits_deny_patterns(q):
        return guardrail_result(False, "I'm designed to help with AI and machine learning topics. Please ask me about ML concepts, algorithms, or data science!")
    
    # 5. Content moderation (safety check)
    if use_moderation:
        moderation_ok, mod_reason = check_moderation(q)
        if not moderation_ok:
            return guardrail_result(False, "Content not allowed due to safety policies.", 403)
    
    # 6. ML scope checks (relaxed approach)
    
    # Fast keyword-based check first
    if cheap_ml_scope(q):
        # Clear ML content - allow through
        latency_ms = int((time.time() - t0) * 1000)
        return {
            "allowed": True, 
            "reason": "Clear ML content detected", 
            "latency_ms": latency_ms
        }
    
    # For ambiguous content, use LLM scope check if enabled
    if use_llm_scope:
        llm_ok = llm_scope_label(q)
        if llm_ok:
            # LLM says it's ML-related - allow through
            latency_ms = int((time.time() - t0) * 1000)
            return {
                "allowed": True, 
                "reason": "LLM classified as ML-related", 
                "latency_ms": latency_ms
            }
        else:
            # LLM says not ML-related - use fallback LLM with strict prompt
            latency_ms = int((time.time() - t0) * 1000)
            return {
                "allowed": "fallback_llm",  # Special flag for fallback
                "reason": "Using fallback LLM with ML-only system prompt", 
                "latency_ms": latency_ms
            }
    else:
        # No LLM scope check - use fallback LLM for ambiguous content
        latency_ms = int((time.time() - t0) * 1000)
        return {
            "allowed": "fallback_llm",  # Special flag for fallback
            "reason": "Ambiguous content - using fallback LLM", 
            "latency_ms": latency_ms
        }
    
    # Optional embedding similarity check (still allow fallback if fails)
    if embedding_similarity is not None and not ml_scope_embedding(embedding_similarity):
        latency_ms = int((time.time() - t0) * 1000)
        return {
            "allowed": "fallback_llm",  # Use fallback instead of blocking
            "reason": "Low similarity - using fallback LLM", 
            "latency_ms": latency_ms
        }
