from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from openai import OpenAI
from enum import Enum
import os
import json
from dotenv import load_dotenv

from database import engine, get_db
from models import Base, UserDB, TaskDB
from auth import create_access_token, get_current_user
from otp_service import OTPService

# Load environment variables
load_dotenv()


# Priority enum
class Priority(str, Enum):
    """Task priority levels"""
    URGENT = "Urgent"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


# Configure Liara AI (OpenAI compatible)
LIARA_API_KEY = os.getenv("LIARA_API_KEY")
LIARA_BASE_URL = os.getenv("LIARA_BASE_URL")
LIARA_MODEL = os.getenv("LIARA_MODEL", "gpt-4o-mini")

# Initialize OpenAI client with Liara AI
liara_client = None
if LIARA_API_KEY and LIARA_BASE_URL:
    liara_client = OpenAI(
        api_key=LIARA_API_KEY,
        base_url=LIARA_BASE_URL
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager to handle startup and shutdown events
    """
    # Startup: Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully")

    yield

    # Shutdown: Dispose of the engine
    await engine.dispose()
    print("Database connection closed")


app = FastAPI(
    title="Task Manager API",
    version="1.0.0",
    description="""
    ## Task Manager API with AI-powered task processing

    This API provides comprehensive task management functionality with:

    * **OTP Authentication** - Secure phone-based authentication with Faraz SMS
    * **AI Task Processing** - Automatically clean and generate titles for tasks using Liara AI
    * **User Management** - JWT-based authentication and user profiles
    * **Task Management** - Full CRUD operations for tasks (coming soon)

    ### Authentication Flow

    1. Send OTP to phone number: `POST /auth/send-otp`
    2. Verify OTP and get JWT token: `POST /auth/verify-otp`
    3. Use JWT token in Authorization header: `Bearer {token}`

    ### Getting Started

    1. Request OTP for your phone number
    2. Verify OTP to receive access token
    3. Use access token for authenticated endpoints

    ### External Services

    - **Liara AI**: AI-powered task processing
    - **Faraz SMS**: OTP delivery via SMS
    """,
    lifespan=lifespan,
    contact={
        "name": "API Support",
        "url": "https://github.com/your-repo",
        "email": "support@example.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    openapi_tags=[
        {
            "name": "Health",
            "description": "Health check and status endpoints"
        },
        {
            "name": "Authentication",
            "description": "OTP-based authentication with phone numbers"
        },
        {
            "name": "Tasks",
            "description": "AI-powered task processing and management"
        },
        {
            "name": "Users",
            "description": "User profile and management"
        }
    ]
)


class Task(BaseModel):
    """Task model with AI-processed content"""
    title: str = Field(..., description="Task title", example="Complete project documentation")
    description: str = Field(None, description="Task description", example="Write comprehensive API documentation")
    proprietary: float = Field(..., description="Priority level (0-10)", example=8.5, ge=0, le=10)
    time: int = Field(0, description="Estimated time in minutes", example=120, ge=0)
    tags: list[str] = Field(default=[], description="Task tags", example=["documentation", "urgent"])

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Complete project documentation",
                "description": "Write comprehensive API documentation for the task manager",
                "proprietary": 8.5,
                "time": 120,
                "tags": ["documentation", "urgent"]
            }
        }


class TaskRequest(BaseModel):
    """Request model for AI task processing"""
    task_text: str = Field(
        ...,
        description="Raw task text in Persian (may contain typos or missing words)",
        example="تسم زمگ به یکی"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "task_text": "تسم زمگ به یکی"
            }
        }


class TaskResponse(BaseModel):
    """Response model with AI-processed task"""
    title: str = Field(..., description="AI-generated task title in Persian", example="تماس تلفنی")
    preprocessed_text: str = Field(
        ...,
        description="Cleaned and corrected task description in Persian",
        example="تماس زنگ زدن به یکی"
    )
    original_text: str = Field(..., description="Original task text", example="تسم زمگ به یکی")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "تماس تلفنی",
                "preprocessed_text": "تماس زنگ زدن به یکی",
                "original_text": "تسم زمگ به یکی"
            }
        }


class PhoneLoginRequest(BaseModel):
    """Phone number for OTP authentication"""
    phone: str = Field(
        ...,
        description="User's phone number (international format recommended)",
        example="09123456789",
        min_length=10,
        max_length=15
    )

    class Config:
        json_schema_extra = {
            "example": {
                "phone": "09123456789"
            }
        }


class OTPVerifyRequest(BaseModel):
    """OTP verification request"""
    phone: str = Field(..., description="User's phone number", example="09123456789")
    otp: str = Field(..., description="6-digit OTP code", example="123456", min_length=6, max_length=6)

    class Config:
        json_schema_extra = {
            "example": {
                "phone": "09123456789",
                "otp": "123456"
            }
        }


class OTPSendResponse(BaseModel):
    """OTP send response"""
    message: str = Field(..., description="Success message", example="OTP sent successfully")
    is_new_user: bool = Field(..., description="True if user was just created", example=False)
    phone: str = Field(..., description="Phone number OTP was sent to", example="09123456789")
    otp: str = Field(..., description="OTP code (FOR TESTING ONLY - Remove in production)", example="123456")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "OTP sent successfully",
                "is_new_user": False,
                "phone": "09123456789",
                "otp": "123456"
            }
        }


class TokenResponse(BaseModel):
    """JWT authentication token response"""
    access_token: str = Field(
        ...,
        description="JWT access token (valid for 7 days)",
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    )
    token_type: str = Field(..., description="Token type", example="bearer")
    user_id: int = Field(..., description="User ID", example=1)
    phone: str = Field(..., description="User's phone number", example="09123456789")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzM1MzI0ODAwfQ...",
                "token_type": "bearer",
                "user_id": 1,
                "phone": "09123456789"
            }
        }


class TaskCreate(BaseModel):
    """Request model for creating a task manually"""
    title: str = Field(..., description="Task title in Persian", example="تماس تلفنی", min_length=1)
    description: str = Field(None, description="Task description in Persian", example="تماس زنگ زدن به یکی از همکاران")
    proprietary: Priority = Field(Priority.LOW, description="Priority level: Urgent, High, Medium, Low", example=Priority.HIGH)
    time: int = Field(0, description="Estimated time in minutes", example=30, ge=0)
    tags: list[str] = Field(default_factory=list, description="Task tags", example=["تماس", "فوری"])
    deadline: datetime | None = Field(None, description="Task deadline (ISO 8601 format)", example="2025-12-31T23:59:59")
    with_ai_flag: bool = Field(False, description="Whether task was processed with AI", example=False)

    class Config:
        json_schema_extra = {
            "example": {
                "title": "تماس تلفنی",
                "description": "تماس زنگ زدن به یکی از همکاران",
                "proprietary": "High",
                "time": 30,
                "tags": ["تماس", "فوری"],
                "deadline": "2025-12-31T23:59:59",
                "with_ai_flag": False
            }
        }


class TaskSubmitProcessed(BaseModel):
    """Request model for submitting an AI-processed task"""
    title: str = Field(..., description="AI-generated task title", example="تماس تلفنی", min_length=1)
    description: str = Field(..., description="AI-processed task description", example="تماس زنگ زدن به یکی از همکاران", min_length=1)
    proprietary: Priority = Field(Priority.LOW, description="Priority level: Urgent, High, Medium, Low", example=Priority.HIGH)
    time: int = Field(0, description="Estimated time in minutes", example=30, ge=0)
    tags: list[str] = Field(default_factory=list, description="Task tags", example=["تماس", "فوری"])
    deadline: datetime | None = Field(None, description="Task deadline (ISO 8601 format)", example="2025-12-31T23:59:59")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "تماس تلفنی",
                "description": "تماس زنگ زدن به یکی از همکاران",
                "proprietary": "Medium",
                "time": 15,
                "tags": ["تماس"],
                "deadline": "2025-12-01T18:00:00"
            }
        }


class TaskUpdate(BaseModel):
    """Request model for updating a task (all fields optional)"""
    title: str | None = Field(None, description="Task title in Persian", example="تماس تلفنی به مدیر", min_length=1)
    description: str | None = Field(None, description="Task description in Persian", example="تماس فوری به مدیر پروژه")
    proprietary: Priority | None = Field(None, description="Priority level: Urgent, High, Medium, Low", example=Priority.URGENT)
    time: int | None = Field(None, description="Estimated time in minutes", example=45, ge=0)
    tags: list[str] | None = Field(None, description="Task tags", example=["تماس", "فوری", "مدیریت"])
    deadline: datetime | None = Field(None, description="Task deadline (ISO 8601 format)", example="2025-12-15T18:00:00")
    with_ai_flag: bool | None = Field(None, description="Whether task was processed with AI", example=True)

    class Config:
        json_schema_extra = {
            "example": {
                "title": "تماس تلفنی به مدیر",
                "proprietary": "Urgent",
                "tags": ["تماس", "فوری", "مدیریت"]
            }
        }


class TaskInDB(BaseModel):
    """Response model for task stored in database"""
    id: int = Field(..., description="Task ID", example=1)
    title: str = Field(..., description="Task title", example="تماس تلفنی")
    description: str | None = Field(None, description="Task description", example="تماس زنگ زدن به یکی از همکاران")
    proprietary: Priority = Field(..., description="Priority level: Urgent, High, Medium, Low", example=Priority.HIGH)
    time: int = Field(..., description="Estimated time in minutes", example=30)
    tags: list[str] = Field(..., description="Task tags", example=["تماس", "فوری"])
    deadline: datetime | None = Field(None, description="Task deadline", example="2025-12-31T23:59:59")
    with_ai_flag: bool = Field(..., description="Whether task was processed with AI", example=False)
    created_at: datetime = Field(..., description="When task was created", example="2025-11-28T10:00:00")
    updated_at: datetime = Field(..., description="When task was last updated", example="2025-11-28T10:00:00")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "title": "تماس تلفنی",
                "description": "تماس زنگ زدن به یکی از همکاران",
                "proprietary": "High",
                "time": 30,
                "tags": ["تماس", "فوری"],
                "deadline": "2025-12-31T23:59:59",
                "with_ai_flag": False,
                "created_at": "2025-11-28T10:00:00",
                "updated_at": "2025-11-28T10:00:00"
            }
        }



@app.get(
    "/",
    tags=["Health"],
    summary="Welcome endpoint",
    response_description="Welcome message"
)
async def root():
    """
    ## Welcome Endpoint

    Returns a welcome message for the API.

    **Public endpoint - No authentication required.**
    """
    return {"message": "Welcome to Task Manager API!"}


@app.get(
    "/health",
    tags=["Health"],
    summary="Health check",
    response_description="Health status"
)
async def health_check():
    """
    ## Health Check Endpoint

    Check if the API is running and healthy.

    **Use this endpoint for:**
    - Monitoring
    - Load balancer health checks
    - Container orchestration health probes

    **Public endpoint - No authentication required.**
    """
    return {"status": "healthy"}


@app.post(
    "/auth/send-otp",
    response_model=OTPSendResponse,
    tags=["Authentication"],
    summary="Send OTP to phone number",
    response_description="OTP sent successfully",
    status_code=200
)
async def send_otp(request: PhoneLoginRequest, db: AsyncSession = Depends(get_db)):
    """
    ## Send OTP for Authentication

    Request an OTP (One-Time Password) to be sent to the provided phone number.

    **Flow:**
    1. If phone number exists in database → Send OTP to existing user
    2. If phone number is new → Create new user account and send OTP

    **OTP Details:**
    - 6-digit numeric code
    - Valid for 5 minutes
    - Sent via Faraz SMS service
    - Can be requested multiple times (replaces previous OTP)

    **Response:**
    - `message`: Success message
    - `is_new_user`: Boolean indicating if this is a new user registration
    - `phone`: The phone number OTP was sent to
    - `otp`: **[TESTING MODE]** The OTP code (for easy testing - remove in production)

    **⚠️ IMPORTANT:** The OTP is included in the response for testing purposes only.
    In production, remove the `otp` field from the response model.

    **Public endpoint - No authentication required.**
    """
    # Check if user exists
    result = await db.execute(select(UserDB).filter(UserDB.phone == request.phone))
    user = result.scalar_one_or_none()

    is_new_user = False

    # If user doesn't exist, create new user
    if not user:
        user = UserDB(phone=request.phone)
        db.add(user)
        is_new_user = True

    # Generate OTP
    otp_code = OTPService.generate_otp()

    # Update user with OTP
    user.otp_code = otp_code
    user.otp_created_at = datetime.utcnow()
    user.otp_verified = False

    await db.commit()

    # Send OTP (you will integrate SMS provider here)
    otp_sent = await OTPService.send_otp(request.phone, otp_code)

    if not otp_sent:
        raise HTTPException(
            status_code=500,
            detail="Failed to send OTP. Please try again."
        )

    return OTPSendResponse(
        message="OTP sent successfully" if not is_new_user else "New user created. OTP sent successfully",
        is_new_user=is_new_user,
        phone=request.phone,
        otp=otp_code  # FOR TESTING ONLY - Remove in production
    )


@app.post(
    "/auth/verify-otp",
    response_model=TokenResponse,
    tags=["Authentication"],
    summary="Verify OTP and get access token",
    response_description="JWT token and user information",
    status_code=200
)
async def verify_otp(request: OTPVerifyRequest, db: AsyncSession = Depends(get_db)):
    """
    ## Verify OTP and Login

    Verify the OTP code received via SMS and get a JWT access token.

    **Validation:**
    - OTP must match the one sent to the phone number
    - OTP must not be expired (5-minute validity)
    - User must exist in database

    **Returns:**
    - `access_token`: JWT token for authentication (valid for 7 days)
    - `token_type`: Always "bearer"
    - `user_id`: User's unique identifier
    - `phone`: User's phone number

    **Usage:**
    Use the returned access token in the Authorization header for protected endpoints:
    ```
    Authorization: Bearer {access_token}
    ```

    **Public endpoint - No authentication required.**
    """
    # Get user
    result = await db.execute(select(UserDB).filter(UserDB.phone == request.phone))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found. Please request OTP first."
        )

    # Check if OTP exists
    if not user.otp_code:
        raise HTTPException(
            status_code=400,
            detail="No OTP found. Please request a new OTP."
        )

    # Check if OTP is expired
    if not OTPService.is_otp_valid(user.otp_created_at):
        raise HTTPException(
            status_code=400,
            detail="OTP has expired. Please request a new OTP."
        )

    # Verify OTP
    if user.otp_code != request.otp:
        raise HTTPException(
            status_code=400,
            detail="Invalid OTP. Please try again."
        )

    # Mark OTP as verified and clear it
    user.otp_verified = True
    user.otp_code = None
    user.otp_created_at = None

    await db.commit()

    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        phone=user.phone
    )


@app.get(
    "/auth/me",
    tags=["Users"],
    summary="Get current user profile",
    response_description="User profile information",
    status_code=200
)
async def get_me(current_user: UserDB = Depends(get_current_user)):
    """
    ## Get Current User Profile

    Retrieve profile information for the currently authenticated user.

    **Authentication Required:**
    - Include JWT token in Authorization header
    - Format: `Authorization: Bearer {access_token}`

    **Returns:**
    - `user_id`: User's unique identifier
    - `phone`: User's phone number
    - `created_at`: Account creation timestamp
    - `updated_at`: Last update timestamp
    """
    return {
        "user_id": current_user.id,
        "phone": current_user.phone,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at
    }


@app.post(
    "/tasks/process",
    response_model=TaskResponse,
    tags=["Tasks"],
    summary="Process task text with AI",
    response_description="AI-processed task with title and cleaned text",
    status_code=200
)
async def process_task(
    request: TaskRequest,
    current_user: UserDB = Depends(get_current_user)
):
    """
    ## AI-Powered Persian Task Processing (Preview Only)

    Process raw Persian task text using Liara AI to preview corrections and title generation.
    **This endpoint does NOT save to database** - it only shows you the AI-processed result.

    After reviewing the AI output, use the `POST /tasks/submit-processed` endpoint to save it.

    **AI Processing:**
    1. **Fix Persian typos** - Automatically correct Persian spelling mistakes (e.g., "تسم" → "تماس")
    2. **Complete missing words** - Fill in missing or incomplete Persian words
    3. **Generate Persian title** - Create a concise, descriptive title in Persian (3-7 words)
    4. **Clean formatting** - Make text clear and professional in Persian

    **Example:**
    - Input (Persian with typos): `"تسم زمگ به یکی"`
    - Corrected Title (Persian): `"تماس تلفنی"`
    - Corrected Text (Persian): `"تماس زنگ زدن به یکی"`

    **Important:**
    - Input must be in Persian/Farsi
    - Output will always be in Persian (not translated to English)
    - AI corrects typos while maintaining Persian language

    **AI Model:** Liara AI (GPT-4o-mini)

    **Authentication Required:**
    - Include JWT token in Authorization header
    - Format: `Authorization: Bearer {access_token}`

    **Returns:**
    - `title`: AI-generated task title (in Persian)
    - `preprocessed_text`: Cleaned and corrected task description (in Persian)
    - `original_text`: Your original input (for reference)

    **Next Step:**
    - Review the AI-processed result
    - If satisfied, use `POST /tasks/submit-processed` to save it to database
    """
    if not liara_client:
        raise HTTPException(
            status_code=500,
            detail="Liara AI not configured. Please set LIARA_API_KEY and LIARA_BASE_URL in .env file"
        )

    try:
        # Create prompt for AI to preprocess the task and generate title
        system_prompt = """You are a Persian/Farsi task processing assistant. You will receive a task description in Persian that may contain typos, missing words, or grammatical errors.

Your job is to:
1. First, identify and correct all Persian typos and spelling mistakes
2. Fix any missing words or grammatical errors in Persian
3. Keep the text ONLY in Persian - DO NOT translate to any other language
4. Generate a short, descriptive title in Persian (3-7 words)
5. Make the text clear and professional in Persian
6. Return ONLY a valid JSON object with Persian text

IMPORTANT RULES:
- Always return Persian text in both title and preprocessed_text
- Never translate Persian to English or any other language
- Fix Persian typos before processing (e.g., "تسم" → "تماس", "زمگ" → "زنگ")
- Keep the original meaning and intent in Persian

Examples:
Input: "تسم زمگ به یکی"
Output: {"title": "تماس تلفنی", "preprocessed_text": "تماس زنگ زدن به یکی"}

Input: "نیاز بع نوشتن مستندت"
Output: {"title": "نوشتن مستندات", "preprocessed_text": "نیاز به نوشتن مستندات"}

Return your response in this exact JSON format (no markdown, no code blocks, just pure JSON):
{
  "title": "عنوان فارسی اینجا",
  "preprocessed_text": "متن اصلاح شده فارسی اینجا"
}"""

        # Call Liara AI
        response = liara_client.chat.completions.create(
            model=LIARA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Task text to process: {request.task_text}"}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        # Get response text
        response_text = response.choices[0].message.content.strip()

        # Clean the response - remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text.replace("```json", "").replace("```", "").strip()
        elif response_text.startswith("```"):
            response_text = response_text.replace("```", "").strip()

        # Parse JSON response
        try:
            parsed_response = json.loads(response_text)
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract from response
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse AI response as JSON. Response: {response_text}"
            )

        # Validate required fields
        if "title" not in parsed_response or "preprocessed_text" not in parsed_response:
            raise HTTPException(
                status_code=500,
                detail="AI response missing required fields (title or preprocessed_text)"
            )

        return TaskResponse(
            title=parsed_response["title"],
            preprocessed_text=parsed_response["preprocessed_text"],
            original_text=request.task_text
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calling Liara AI: {str(e)}"
        )


@app.post(
    "/tasks",
    response_model=TaskInDB,
    tags=["Tasks"],
    summary="Create a new task manually",
    response_description="Task created successfully",
    status_code=201
)
async def create_task(
    task: TaskCreate,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    ## Create a New Task Manually

    Create and store a new task in the database for the authenticated user.
    Use this endpoint for manually creating tasks without AI processing.

    **Authentication Required:**
    - Include JWT token in Authorization header
    - Format: `Authorization: Bearer {access_token}`

    **Request Body:**
    - `title`: Task title (required, Persian recommended)
    - `description`: Detailed task description (optional)
    - `proprietary`: Priority level - Urgent, High, Medium, or Low (default: Low)
    - `time`: Estimated time in minutes (default: 0)
    - `tags`: List of tags for categorization (default: empty list)
    - `deadline`: Task deadline in ISO 8601 format (optional)
    - `with_ai_flag`: Set to `true` if task was AI-processed (default: false)

    **Returns:**
    - Complete task object with all fields including generated `id`, `created_at`, and `updated_at`

    **Example:**
    ```json
    {
      "title": "تماس تلفنی",
      "description": "تماس زنگ زدن به یکی از همکاران",
      "proprietary": "High",
      "time": 30,
      "tags": ["تماس", "فوری"],
      "deadline": "2025-12-31T23:59:59",
      "with_ai_flag": false
    }
    ```
    """
    # Create new task in database
    new_task = TaskDB(
        title=task.title,
        description=task.description,
        user_id=current_user.id,
        proprietary=task.proprietary,
        time=task.time,
        tags=task.tags,
        deadline=task.deadline,
        with_ai_flag=task.with_ai_flag
    )

    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    return new_task


@app.post(
    "/tasks/submit-processed",
    response_model=TaskInDB,
    tags=["Tasks"],
    summary="Submit and save an AI-processed task",
    response_description="AI-processed task saved successfully",
    status_code=201
)
async def submit_processed_task(
    task: TaskSubmitProcessed,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    ## Submit and Save AI-Processed Task

    After using `POST /tasks/process` to preview AI corrections, use this endpoint
    to save the approved task to the database.

    **Workflow:**
    1. Call `POST /tasks/process` with raw text to get AI corrections (preview only)
    2. Review the AI-generated title and corrected description
    3. Optionally add priority, time estimate, tags, and deadline
    4. Call this endpoint to save the task to database

    **Authentication Required:**
    - Include JWT token in Authorization header
    - Format: `Authorization: Bearer {access_token}`

    **Request Body:**
    - `title`: AI-generated title from `/tasks/process` (required)
    - `description`: AI-corrected description from `/tasks/process` (required)
    - `proprietary`: Priority level - Urgent, High, Medium, or Low (default: Low)
    - `time`: Estimated time in minutes (default: 0)
    - `tags`: List of tags for categorization (default: empty list)
    - `deadline`: Task deadline in ISO 8601 format (optional)

    **Returns:**
    - Complete task object with all fields including generated `id`, `created_at`, and `updated_at`
    - `with_ai_flag` is automatically set to `true` for AI-processed tasks

    **Example:**
    ```json
    {
      "title": "تماس تلفنی",
      "description": "تماس زنگ زدن به یکی از همکاران",
      "proprietary": "Medium",
      "time": 15,
      "tags": ["تماس"],
      "deadline": "2025-12-01T18:00:00"
    }
    ```
    """
    # Create new task in database with AI flag set to true
    new_task = TaskDB(
        title=task.title,
        description=task.description,
        user_id=current_user.id,
        proprietary=task.proprietary,
        time=task.time,
        tags=task.tags,
        deadline=task.deadline,
        with_ai_flag=True  # Automatically set for AI-processed tasks
    )

    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    return new_task


@app.get(
    "/tasks",
    response_model=list[TaskInDB],
    tags=["Tasks"],
    summary="Get all tasks for current user",
    response_description="List of all user's tasks",
    status_code=200
)
async def get_tasks(
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    ## Get All Tasks for Current User

    Retrieve all tasks created by the authenticated user.

    **Authentication Required:**
    - Include JWT token in Authorization header
    - Format: `Authorization: Bearer {access_token}`

    **Returns:**
    - List of all tasks belonging to the authenticated user
    - Each task includes: id, title, description, priority, time, tags, deadline, AI flag, timestamps
    - Ordered by creation date (newest first)

    **Response:**
    - Empty array `[]` if user has no tasks
    - Array of task objects if tasks exist

    **Use Cases:**
    - Display user's task list
    - Task management dashboard
    - Task overview and planning
    """
    # Query all tasks for current user
    result = await db.execute(
        select(TaskDB)
        .filter(TaskDB.user_id == current_user.id)
        .order_by(TaskDB.created_at.desc())
    )
    tasks = result.scalars().all()

    return tasks


@app.put(
    "/tasks/{task_id}",
    response_model=TaskInDB,
    tags=["Tasks"],
    summary="Update a task by ID",
    response_description="Task updated successfully",
    status_code=200
)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    ## Update an Existing Task

    Update a task by its ID. Only the task owner can update their tasks.

    **Authentication Required:**
    - Include JWT token in Authorization header
    - Format: `Authorization: Bearer {access_token}`

    **Path Parameters:**
    - `task_id`: The ID of the task to update

    **Request Body:**
    - All fields are optional - only include fields you want to update
    - `title`: Task title (optional)
    - `description`: Task description (optional)
    - `proprietary`: Priority level - Urgent, High, Medium, or Low (optional)
    - `time`: Estimated time in minutes (optional)
    - `tags`: List of tags (optional)
    - `deadline`: Task deadline in ISO 8601 format (optional)
    - `with_ai_flag`: AI processing flag (optional)

    **Returns:**
    - Updated task object with all fields

    **Error Responses:**
    - `404`: Task not found
    - `403`: Not authorized to update this task (task belongs to another user)

    **Example:**
    ```json
    {
      "title": "تماس تلفنی به مدیر",
      "proprietary": "Urgent",
      "tags": ["تماس", "فوری", "مدیریت"]
    }
    ```
    """
    # Get the task from database
    result = await db.execute(
        select(TaskDB).filter(TaskDB.id == task_id)
    )
    task = result.scalar_one_or_none()

    # Check if task exists
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Task with ID {task_id} not found"
        )

    # Check if task belongs to current user
    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to update this task"
        )

    # Update only the fields that were provided
    update_data = task_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    # Update the updated_at timestamp
    task.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(task)

    return task
