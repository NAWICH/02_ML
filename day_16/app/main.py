"""
Lok Sewa Preparation API - Main Application
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import Response
from app.auth import (
    get_hashed_password,
    verify_password,
    create_access_token,
    get_current_user,
    require_premium
)
from app.database import (
    create_user,
    find_user_by_email,
    upgrade_to_premium,
    get_question_by_id,
    save_attempt,
    get_user_attempts,
    get_user_stats,
    get_user_attempted_question_ids
)
from app.models import (
    UserRegister,
    UserLogin,
    UserResponse,
    Token,
    GenerateRequest,
    SubmitAnswer,
    SubmitResponse,
    UserStats
)
from app.question_service import QuestionService
from typing import Optional

# Initialize app
app = FastAPI(
    title="Lok Sewa Preparation API",
    description="AI-powered Lok Sewa practice questions",
    version="1.0.0"
)

# Initialize question service (loads model once)
service = QuestionService()

@app.post("/api/auth/register", response_model=UserResponse)  
async def register_user(body: UserRegister):
    """Create new user account"""

    # Check if email already exists
    if find_user_by_email(body.email):
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Hash password and create user
    hashed_password = get_hashed_password(body.password)
    new_user = create_user(body.full_name, body.email, hashed_password)

    if not new_user:
        raise HTTPException(
            status_code=500,
            detail="Failed to create user"
        )

    return UserResponse(
        id=new_user['id'],           
        full_name=new_user['full_name'],  
        email=new_user['email'],     
        is_premium=new_user['is_premium'],
        created_at=new_user['created_at']
    )


@app.post("/api/auth/login", response_model=Token)  
async def login(body: UserLogin):
    """Login and return JWT access token"""

    # Find user
    user = find_user_by_email(body.email)

    # Verify credentials (unified error for security)
    if not user or not verify_password(body.password, user['password_hash']):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    # Create token with premium status embedded
    access_token = create_access_token(
        subject=user['email'],
        is_premium=bool(user['is_premium'])
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        is_premium=bool(user['is_premium'])
    )


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "service": "Lok Sewa Prep API"}


@app.get("/api/users/me", response_model=UserResponse)
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    return UserResponse(
        id=current_user['id'],
        full_name=current_user['full_name'],
        email=current_user['email'],
        is_premium=bool(current_user['is_premium']),
        created_at=current_user['created_at']
    )


@app.get("/api/users/me/stats")
async def get_my_stats(current_user: dict = Depends(get_current_user)):
    """Get user's performance statistics"""
    stats = get_user_stats(current_user['id'])

    if not stats:
        return {
            "total_attempted": 0,
            "total_solved": 0,
            "total_failed": 0,
            "accuracy": 0.0,
            "message": "No attempts yet! Start practicing!"
        }

    return stats


@app.post("/api/questions/generate")
async def generate_questions(
    request: GenerateRequest,
    current_user: dict = Depends(get_current_user)  
):
    """
    Generate fresh Lok Sewa practice questions.

    Free users: max 5 questions
    Premium users: up to 10 questions

    Optional filters:
    - subject: GK, Nepali, English, Math, Science, CurrentAffairs
    - difficulty: easy, medium, hard
    - count: number of questions (1-5 for free, 1-10 for premium)
    """

    # Free users limited to 5 questions
    if not bool(current_user['is_premium']) and request.count > 5:
        raise HTTPException(
            status_code=403,
            detail="Free users can generate max 5 questions. Upgrade to Premium for more!"
        )

    # Generate questions
    questions = service.generate_questions(
        subject=request.subject,
        difficulty=request.difficulty,
        count=request.count,
        user_id=current_user['id']
    )

    if not questions:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate questions. Please try again."
        )

    return {
        "questions": questions,
        "count": len(questions),
        "subject": request.subject or "mixed",
        "difficulty": request.difficulty or "medium"
    }


@app.post("/api/questions/submit", response_model=SubmitResponse)
async def submit_answer(
    body: SubmitAnswer,
    current_user: dict = Depends(require_premium)
):
    """
    Submit answer for a question.
    Returns whether correct + explanation.
    """

    # Validate selected option
    if body.selected_option not in ["A", "B", "C", "D"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid option. Must be A, B, C, or D"
        )

    # Get question from database (has correct answer!)
    question = get_question_by_id(body.question_id)

    if not question:
        raise HTTPException(
            status_code=404,
            detail="Question not found"
        )

    # Check if already attempted
    attempted_ids = get_user_attempted_question_ids(current_user['id'])
    if body.question_id in attempted_ids:
        raise HTTPException(
            status_code=400,
            detail="You already answered this question!"
        )

    # Get explanation from AI
    result = service.get_explanation(dict(question), body.selected_option)

    # Save attempt to database
    save_attempt(
        user_id=current_user['id'],
        question_id=body.question_id,
        selected=body.selected_option,
        is_correct=result['is_correct']
    )

    return SubmitResponse(
        is_correct=result['is_correct'],
        selected=result['selected'],
        correct=result['correct'],
        explanation=result['explanation'],
        points_earned=result['points_earned']
    )


@app.get("/api/questions/history")
async def get_question_history(current_user: dict = Depends(get_current_user)):
    """Get user's question attempt history"""
    attempts = get_user_attempts(current_user['id'])

    if not attempts:
        return {
            "attempts": [],
            "message": "No attempts yet! Generate questions to start practicing."
        }

    return {
        "attempts": attempts,
        "total": len(attempts)
    }


#premium
@app.post("/api/questions/generate/advanced")
async def generate_advanced_questions(
    request: GenerateRequest,
    current_user: dict = Depends(require_premium)  
):
    """
    Premium feature: Generate up to 10 questions with advanced filtering.
    Includes harder questions and detailed analysis.
    """
    questions = service.generate_questions(
        subject=request.subject,
        difficulty=request.difficulty,
        count=min(request.count, 10),  # Max 10 for premium
        user_id=current_user['id']
    )

    return {
        "questions": questions,
        "count": len(questions),
        "premium_feature": True
    }


@app.post("/api/upgrade")
async def upgrade_to_premium_route(current_user: dict = Depends(get_current_user)):
    """
    Upgrade user to premium.
    (In production: integrate eSewa/Khalti payment here!)
    """
    if bool(current_user['is_premium']):
        return {"message": "You are already a premium user!"}

    success = upgrade_to_premium(current_user['id'])

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to upgrade. Please try again."
        )

    return {
        "message": "Successfully upgraded to Premium!",
        "benefits": [
            "Generate up to 10 questions at once",
            "Access to advanced filtering",
            "Detailed performance analytics",
            "Priority question updates"
        ]
    }