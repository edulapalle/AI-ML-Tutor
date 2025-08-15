# Authentication models for user registration and login system
from pydantic import BaseModel, Field, computed_field
from typing import List, Optional
from datetime import date, datetime

class UserRegistration(BaseModel):
    """User registration model with comprehensive study-related information"""
    username: str = Field(..., min_length=3, max_length=50, description="Unique username for the user")
    email: str = Field(..., description="User's email address for account verification")
    password: str = Field(..., min_length=8, description="Secure password for account access")
    date_of_birth: date = Field(..., description="User's date of birth for age-appropriate content")
    topics_of_interest: List[str] = Field(..., description="List of subjects/topics the user is interested in learning")
    current_stage: str = Field(..., description="Current stage of life: school, college, work, etc.")
    current_goals: List[str] = Field(..., description="Current learning and study goals")
    study_level: str = Field(..., description="Current study level: beginner, intermediate, advanced")
    preferred_learning_style: Optional[str] = Field(None, description="Preferred learning style: visual, auditory, kinesthetic, etc.")

class UserLogin(BaseModel):
    """User login model for authentication"""
    email: str = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")

class UserProfile(BaseModel):
    """User profile model for displaying user information"""
    id: str = Field(..., description="Unique user ID")
    username: str = Field(..., description="User's username")
    email: str = Field(..., description="User's email address")
    date_of_birth: date = Field(..., description="User's date of birth")
    topics_of_interest: List[str] = Field(..., description="User's topics of interest")
    current_stage: str = Field(..., description="User's current stage of life")
    current_goals: List[str] = Field(..., description="User's current goals")
    study_level: str = Field(..., description="User's study level")
    preferred_learning_style: Optional[str] = Field(None, description="User's preferred learning style")
    created_at: datetime = Field(..., description="Account creation timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    
    @computed_field
    @property
    def user_age(self) -> int:
        """Calculate user's current age from date of birth"""
        today = date.today()
        age = today.year - self.date_of_birth.year
        
        # Adjust if birthday hasn't occurred this year yet
        if today < date(today.year, self.date_of_birth.month, self.date_of_birth.day):
            age -= 1
            
        return age
    
    @computed_field
    @property 
    def age_group(self) -> str:
        """Determine age group for content appropriateness"""
        age = self.user_age
        if age < 13:
            return "child"
        elif age < 18:
            return "teenager"
        elif age < 25:
            return "young_adult"
        elif age < 65:
            return "adult"
        else:
            return "senior"

class UserSession(BaseModel):
    """User session model for maintaining authentication state"""
    user_id: str = Field(..., description="User ID for session tracking")
    session_token: str = Field(..., description="JWT session token")
    expires_at: datetime = Field(..., description="Session expiration timestamp")

class PasswordReset(BaseModel):
    """Password reset model for account recovery"""
    email: str = Field(..., description="User's email address for password reset")

class PasswordUpdate(BaseModel):
    """Password update model for changing passwords"""
    current_password: str = Field(..., description="Current password for verification")
    new_password: str = Field(..., min_length=8, description="New secure password")
