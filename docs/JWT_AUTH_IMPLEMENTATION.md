# JWT Authentication Implementation Guide

This guide explains how to implement and test the JWT-based authentication system in the MediTwin backend.

## Overview

The authentication system follows the flowchart specification:
1. **User ID Creation**: User ID is created at signup and stored in PostgreSQL (currently using in-memory storage for demo)
2. **JWT Token Generation**: On login, JWT tokens are generated with `user_id` in the `sub` claim
3. **Token-Based Authentication**: All protected endpoints extract `user_id` from JWT tokens only
4. **Data Scoping**: All database operations are scoped to the authenticated user's ID
5. **Refresh Token Support**: Long-lived refresh tokens for seamless authentication

## Architecture

```
Frontend → POST /auth/login → Backend verifies credentials → JWT (sub = user_id)
Frontend stores JWT → Protected API calls → Authorization: Bearer <token>
Backend extracts token → Verifies signature & expiry → Extracts user_id → Scoped DB operations
```

## Files Updated

### Backend (`/home/user/agents/meditwin-agents/`)

1. **`src/config/settings.py`**
   - Added JWT configuration parameters
   - `access_token_expire_minutes`, `refresh_token_expire_days`
   - Optional separate refresh token secret

2. **`src/auth/models.py`**
   - Updated to use standard JWT claims (`sub` for user_id)
   - Added `UserCreate`, `UserLogin`, `TokenResponse` models
   - Added `refresh_expires_in` to token response

3. **`src/auth/jwt_auth.py`**
   - Complete modular JWT implementation
   - Password hashing with bcrypt
   - Access and refresh token creation/verification
   - In-memory refresh token store (use Redis/DB in production)
   - User extraction from JWT tokens

4. **`src/api/endpoints/auth.py`**
   - `/auth/signup` - Create user and return tokens
   - `/auth/login` - Authenticate and return tokens
   - `/auth/refresh` - Refresh access token using refresh token
   - `/auth/logout` - Invalidate refresh token
   - `/auth/me` - Get user profile from JWT
   - `/auth/verify` - Verify token validity

5. **`src/api/endpoints/chat.py`**
   - Updated to use JWT authentication (`CurrentUser` dependency)
   - Removed `user_id` from request body (extracted from JWT)
   - All chat operations scoped to authenticated user

6. **`src/api/endpoints/anatomy.py`**
   - Updated to use JWT authentication
   - Removed `user_id` query parameters

7. **`src/utils/schema.py`**
   - Removed `user_id` from `ChatRequest` and `TimelineRequest`
   - User ID now extracted from JWT tokens

8. **`src/api/__init__.py`**
   - Added auth router to API registration

## Setup Instructions

### 1. Environment Configuration

Copy `.env.example` to `.env` and update the JWT settings:

```bash
# JWT Configuration
JWT_SECRET_KEY=your_super_secret_jwt_key_change_this_in_production
JWT_REFRESH_SECRET_KEY=your_super_secret_refresh_key_change_this_in_production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
JWT_REQUIRE_AUTH=false  # Set to true in production
```

**Generate secure keys:**
```bash
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('JWT_REFRESH_SECRET_KEY=' + secrets.token_urlsafe(32))"
```

### 2. Install Dependencies

```bash
cd /home/user/agents/meditwin-agents
pip install passlib[bcrypt] python-jose[cryptography]
```

### 3. Start the Backend

```bash
# Development mode
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Production mode
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### 4. Test the Authentication

#### Option A: Using the Frontend Test Page

1. Open `frontend_test.html` in a web browser
2. Update the `API_BASE_URL` if your backend runs on a different port
3. Test signup, login, and protected endpoints

#### Option B: Using cURL

**Signup:**
```bash
curl -X POST "http://localhost:8000/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "password123",
    "full_name": "Test User"
  }'
```

**Login:**
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

**Protected Endpoint:**
```bash
# Use the access_token from login response
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Chat API:**
```bash
curl -X POST "http://localhost:8000/chat/message" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, I have a headache"
  }'
```

## Key Features

### 1. Modular JWT System

- **Token Creation**: `create_access_token()`, `create_refresh_token()`
- **Token Verification**: `verify_token()`, `verify_refresh_token()`
- **User Extraction**: `get_current_user()` dependency
- **Token Response**: `create_token_response()` for complete token pairs

### 2. Security Features

- **Password Hashing**: bcrypt with salt rounds
- **Token Expiration**: Short-lived access tokens (15 min), long-lived refresh tokens (7 days)
- **Token Rotation**: Refresh tokens are invalidated on use (optional)
- **User Scoping**: All data operations scoped to authenticated user

### 3. FastAPI Integration

- **Dependencies**: `CurrentUser = Depends(get_current_user)`
- **Automatic Validation**: JWT extraction and verification in middleware
- **Error Handling**: Standard HTTP 401/403 responses for auth failures

### 4. Frontend Integration

- **Token Storage**: localStorage or HTTP-only cookies
- **Authorization Headers**: `Authorization: Bearer <token>`
- **Automatic Refresh**: Handle token expiration gracefully
- **No User ID Transmission**: Frontend never sends user_id separately

## Production Considerations

### 1. Database Integration

Replace the in-memory `UserDB` class with actual database operations:

```python
# Example PostgreSQL integration
from src.db.postgres_db import get_postgres

class UserDB:
    @staticmethod
    async def create_user(email: str, username: str, password: str, full_name: str = None) -> str:
        conn = await get_postgres()
        user_id = str(uuid.uuid4())
        password_hash = hash_password(password)
        
        await conn.execute("""
            INSERT INTO users (user_id, email, username, password_hash, full_name, created_at)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, user_id, email, username, password_hash, full_name, datetime.now(timezone.utc))
        
        return user_id
```

### 2. Refresh Token Storage

Use Redis or database for refresh token storage:

```python
# Example Redis integration
import redis
redis_client = redis.Redis(host='localhost', port=6379, db=0)

def store_refresh_token(token: str, user_id: str):
    redis_client.setex(f"refresh_token:{token}", 
                      settings.refresh_token_expire_days * 24 * 60 * 60, 
                      user_id)
```

### 3. Environment Security

- Use strong, unique secrets for JWT signing
- Set `JWT_REQUIRE_AUTH=true` in production
- Use HTTPS for all API communications
- Implement rate limiting on auth endpoints

### 4. Role-Based Access Control (Future)

The system is designed for easy RBAC extension:

```python
# Add roles to JWT payload
def create_access_token(user_id: str, roles: List[str] = None):
    payload = {
        "sub": user_id,
        "roles": roles or [],
        # ... other fields
    }
    
# Check roles in endpoints
def require_role(required_role: str):
    def role_checker(current_user: User = Depends(get_current_user)):
        if required_role not in current_user.roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker

# Usage
@router.get("/admin/users")
async def get_all_users(admin_user: User = Depends(require_role("admin"))):
    # Admin-only endpoint
    pass
```

## Testing

### Unit Tests

```python
# Test JWT token creation and verification
def test_token_creation():
    user_id = "test_user_123"
    token = create_access_token({"sub": user_id})
    assert verify_token(token)
    
    decoded = decode_token(token)
    assert decoded.sub == user_id
```

### Integration Tests

```python
# Test auth endpoints
def test_signup_login_flow():
    # Test signup
    response = client.post("/auth/signup", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "password123"
    })
    assert response.status_code == 201
    
    # Test login
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    tokens = response.json()
    
    # Test protected endpoint
    response = client.get("/auth/me", headers={
        "Authorization": f"Bearer {tokens['access_token']}"
    })
    assert response.status_code == 200
```

## API Documentation

All authentication endpoints are automatically documented at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Support

For issues or questions about the authentication implementation:
1. Check the logs for detailed error messages
2. Verify JWT token format and expiration
3. Ensure proper Authorization header format
4. Test with the provided frontend test page

## Next Steps

1. **Database Integration**: Replace in-memory storage with PostgreSQL
2. **Redis Integration**: Use Redis for refresh token storage
3. **Role-Based Access**: Implement user roles and permissions
4. **Audit Logging**: Log authentication events for security monitoring
5. **Rate Limiting**: Implement rate limiting on auth endpoints
6. **Email Verification**: Add email verification for signup process
