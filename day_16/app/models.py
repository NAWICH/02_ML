from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class UserRegister(BaseModel):
    """Data from User sign up"""
    full_name : str = Field(...,min_length=3, max_length=30)
    email : EmailStr
    password: str = Field(..., min_length=8, max_length=30)

class UserLogin(BaseModel):
    """data from user login"""
    email: EmailStr
    password: str 

class UserResponse(BaseModel):
    """User resource return to Client"""
    id: int
    email: EmailStr
    full_name: str
    is_premium: bool
    created_at: datetime

class Token(BaseModel):
    """Token response"""
    access_token: str
    token_type: str
    is_premium: bool

class TokenData(BaseModel):
    """data Extracted from token"""
    email: EmailStr = None
    is_premium: bool = False

class QuestionOption(BaseModel):
    """model for question option"""
    A: str
    B: str
    C: str
    D: str

class Question(BaseModel):
    """Question data"""
    id: str
    subject: str
    difficulty: str
    question: str
    options: QuestionOption

class QuestionWithAnswer(BaseModel):
    """question data shown to user"""
    correct: str
    explanation: str

class GenerateRequest(BaseModel):
    """request by client to make question"""
    subject: Optional[str] = None
    difficulty: Optional[str] = None
    count: int = Field(default=5, ge=1, le=10)

class SubmitAnswer(BaseModel):
    """answer submitted by user"""
    question_id: str
    selected_option: str

class SubmitResponse(BaseModel):
    """response to user after submitting answer"""
    is_correct: bool
    selected: str
    correct: str
    explanation: str
    points_earned: int

class UserStats(BaseModel):
    """current user data"""
    total_attempted: int
    total_solved: int
    total_failed: int
    accuracy_percentage: float
    by_subject: dict
    streak_days: int