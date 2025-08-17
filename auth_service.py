# Authentication service for Supabase integration and user management
import os
import jwt
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from supabase import create_client, Client
from auth_models import UserRegistration, UserLogin, UserProfile, UserSession
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Fix SSL certificate issues for Railway deployment
import ssl
import certifi
import os

# Set SSL certificate paths for Railway
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
os.environ['SSL_CERT_FILE'] = certifi.where()

# Create SSL context with proper certificates
ssl_context = ssl.create_default_context(cafile=certifi.where())
ssl._create_default_https_context = lambda: ssl_context

# Password hashing context for secure password storage
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings for secure token generation
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Supabase client initialization for database operations
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")

if not supabase_url or not supabase_key:
    print("⚠️  Warning: Supabase configuration not found!")
    print("   Please set SUPABASE_URL and SUPABASE_ANON_KEY environment variables")
    print("   Authentication features will not work without proper Supabase configuration")
    supabase: Client = None
else:
    try:
        # Simple Supabase client for Railway deployment
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Supabase client initialized successfully")
    except FileNotFoundError as e:
        print(f"⚠️ Supabase file error: {e}")
        print("   This may be due to missing certificates in Railway container")
        supabase: Client = None
    except Exception as e:
        print(f"❌ Error initializing Supabase client: {e}")
        print(f"   Error type: {type(e).__name__}")
        supabase: Client = None

class AuthService:
    """Authentication service for user management and session handling"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash for secure authentication"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate a secure hash for password storage"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token for user session management"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return user data for session validation"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.PyJWTError:
            return None
    # OLD METHOD
    # @staticmethod
    # async def register_user(user_data: UserRegistration) -> Dict[str, Any]:
    #     """Register a new user with comprehensive study information"""
    #     try:
    #         # Check if Supabase is configured
    #         if supabase is None:
    #             raise ValueError("Supabase is not configured. Please set SUPABASE_URL and SUPABASE_ANON_KEY environment variables.")
            
    #         # Check if user already exists
    #         existing_user = supabase.table("users").select("email").eq("email", user_data.email).execute()
    #         if existing_user.data:
    #             raise ValueError("User with this email already exists")
            
    #         # Check if username is taken
    #         existing_username = supabase.table("users").select("username").eq("username", user_data.username).execute()
    #         if existing_username.data:
    #             raise ValueError("Username already taken")
            
    #         # Hash password for secure storage
    #         hashed_password = AuthService.get_password_hash(user_data.password)
            
    #         # Prepare user data for database insertion
    #         user_dict = user_data.dict()
    #         user_dict.pop("password")  # Remove plain password
    #         user_dict["hashed_password"] = hashed_password
    #         user_dict["created_at"] = datetime.utcnow().isoformat()
    #         user_dict["topics_of_interest"] = json.dumps(user_data.topics_of_interest)
    #         user_dict["current_goals"] = json.dumps(user_data.current_goals)
    #         user_dict["date_of_birth"] = user_data.date_of_birth.isoformat()
            
    #         # Insert user into database
    #         result = supabase.table("users").insert(user_dict).execute()
            
    #         if result.data:
    #             user_id = result.data[0]["id"]
    #             # Create access token for immediate login
    #             access_token = AuthService.create_access_token(data={"sub": user_id})
    #             return {
    #                 "user_id": user_id,
    #                 "access_token": access_token,
    #                 "message": "User registered successfully"
    #             }
    #         else:
    #             raise ValueError("Failed to create user")
                
    #     except FileNotFoundError as e:
    #         traceback.print_exc()
    #         print(f"⚠️ Auth service file error: {e}")
    #         print("   This may be due to missing certificates or SSL configuration")
    #         raise ValueError(f"Registration failed due to file access: {str(e)}")
    #     except Exception as e:
    #         print(f"⚠️ Auth service error: {e}")
    #         print(f"   Error type: {type(e).__name__}")
    #         raise ValueError(f"Registration failed: {str(e)}")
    
    # NEW METHOD
    @staticmethod
    async def register_user(user_data: UserRegistration) -> Dict[str, Any]:
        try:
            step = "pre_checks"
            if supabase is None:
                raise ValueError("Supabase is not configured. Please set SUPABASE_URL and SUPABASE_ANON_KEY.")

            step = "check_existing_email"
            existing_user = supabase.table("users").select("email").eq("email", user_data.email).execute()
            if existing_user.data:
                raise ValueError("User with this email already exists")

            step = "check_existing_username"
            existing_username = supabase.table("users").select("username").eq("username", user_data.username).execute()
            if existing_username.data:
                raise ValueError("Username already taken")

            step = "hash_password"
            hashed_password = AuthService.get_password_hash(user_data.password)

            step = "prepare_payload"
            user_dict = user_data.model_dump() if hasattr(user_data, "model_dump") else user_data.dict()
            user_dict.pop("password", None)
            user_dict["hashed_password"] = hashed_password
            user_dict["created_at"] = datetime.now(timezone.utc).isoformat()

            # If your Supabase columns are JSONB, DON'T dump to string:
            # user_dict["topics_of_interest"] = user_data.topics_of_interest or []
            # user_dict["current_goals"] = user_data.current_goals or []
            # If your columns are TEXT, keep dumps:
            user_dict["topics_of_interest"] = json.dumps(user_data.topics_of_interest or [])
            user_dict["current_goals"] = json.dumps(user_data.current_goals or [])

            user_dict["date_of_birth"] = (
                user_data.date_of_birth.isoformat() if getattr(user_data, "date_of_birth", None) else None
            )

            step = "supabase_insert"
            result = supabase.table("users").insert(user_dict).execute()

            step = "post_insert_token"
            if result.data:
                user_id = result.data[0]["id"]
                access_token = AuthService.create_access_token(data={"sub": user_id})
                return {"user_id": user_id, "access_token": access_token, "message": "User registered successfully"}
            else:
                raise ValueError("Failed to create user (no data returned)")

        except FileNotFoundError as e:
            print(f"⚠️ FileNotFoundError at step: {step}: {e}")
            traceback.print_exc()
            raise ValueError(f"Registration failed due to file access at '{step}': {e}")
        except Exception as e:
            print(f"⚠️ Exception at step: {step}: {e} ({type(e).__name__})")
            traceback.print_exc()
            raise ValueError(f"Registration failed at '{step}': {e}")

    @staticmethod
    async def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password for secure login"""
        try:
            # Check if Supabase is configured
            if supabase is None:
                raise ValueError("Supabase is not configured. Please set SUPABASE_URL and SUPABASE_ANON_KEY environment variables.")
            
            # Get user from database
            result = supabase.table("users").select("*").eq("email", email).execute()
            
            if not result.data:
                return None
            
            user = result.data[0]
            
            # Verify password
            if not AuthService.verify_password(password, user["hashed_password"]):
                return None
            
            # Update last login timestamp
            supabase.table("users").update({"last_login": datetime.utcnow().isoformat()}).eq("id", user["id"]).execute()
            
            return user
            
        except Exception as e:
            print(f"Authentication error: {e}")
            return None
    
    @staticmethod
    async def get_user_profile(user_id: str) -> Optional[UserProfile]:
        """Retrieve user profile information for personalized experience"""
        try:
            # Check if Supabase is configured
            if supabase is None:
                raise ValueError("Supabase is not configured. Please set SUPABASE_URL and SUPABASE_ANON_KEY environment variables.")
            
            result = supabase.table("users").select("*").eq("id", user_id).execute()
            
            if not result.data:
                return None
            
            user_data = result.data[0]
            
            # Parse JSON fields back to lists
            user_data["topics_of_interest"] = json.loads(user_data["topics_of_interest"])
            user_data["current_goals"] = json.loads(user_data["current_goals"])
            
            return UserProfile(**user_data)
            
        except Exception as e:
            print(f"Error getting user profile: {e}")
            return None
    
    @staticmethod
    async def update_user_profile(user_id: str, profile_data: Dict[str, Any]) -> bool:
        """Update user profile information for personalized learning"""
        try:
            # Check if Supabase is configured
            if supabase is None:
                raise ValueError("Supabase is not configured. Please set SUPABASE_URL and SUPABASE_ANON_KEY environment variables.")
            
            # Handle JSON fields
            if "topics_of_interest" in profile_data:
                profile_data["topics_of_interest"] = json.dumps(profile_data["topics_of_interest"])
            if "current_goals" in profile_data:
                profile_data["current_goals"] = json.dumps(profile_data["current_goals"])
            if "date_of_birth" in profile_data:
                profile_data["date_of_birth"] = profile_data["date_of_birth"].isoformat()
            
            result = supabase.table("users").update(profile_data).eq("id", user_id).execute()
            return bool(result.data)
            
        except Exception as e:
            print(f"Error updating user profile: {e}")
            return False

# JSON import moved to top of file
