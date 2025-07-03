# MediTwin Authentication System

## Overview

The MediTwin backend uses JWT (JSON Web Token) authentication to secure API endpoints and manage user sessions. The authentication system is designed to work with a separate login service that issues JWT tokens.

## Authentication Flow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │
│   Frontend      │    │  Login Service  │    │ MediTwin Backend│
│   (Client)      │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │ 1. Login Request      │                       │
         │──────────────────────>│                       │
         │                       │                       │
         │ 2. JWT Token          │                       │
         │<──────────────────────│                       │
         │                       │                       │
         │ 3. API Request with JWT Token                 │
         │──────────────────────────────────────────────>│
         │                       │                       │
         │                       │ 4. Token Verification │
         │                       │<──────────────────────│
         │                       │                       │
         │ 5. API Response                               │
         │<──────────────────────────────────────────────│
```

## JWT Token Structure

The JWT tokens issued by the login service should contain the following payload:

```json
{
  "user_id": "unique_user_identifier",
  "email": "user@example.com",
  "username": "username",
  "iat": 1640995200,  // Issued at timestamp
  "exp": 1641081600   // Expiration timestamp
}
```

### Required Fields
- `user_id`: Unique identifier for the user (string)
- `exp`: Token expiration timestamp (Unix timestamp)

### Optional Fields
- `email`: User's email address
- `username`: User's username
- `iat`: Token issued at timestamp

## User ID Format

The `user_id` should be:
- **Unique**: Globally unique identifier for each user
- **Consistent**: Same ID across all services and sessions
- **Secure**: Not easily guessable or enumerable
- **Format**: Recommended formats:
  - UUID: `550e8400-e29b-41d4-a716-446655440000`
  - Prefixed ID: `user_123456789`
  - Hash-based: `usr_abc123def456789`

## Backend Configuration

### Environment Variables

```bash
# JWT Configuration
JWT_SECRET_KEY=your-very-secure-secret-key-here
JWT_ALGORITHM=HS256
JWT_REQUIRE_AUTH=true  # Set to false for development

# Example values for development
JWT_SECRET_KEY=dev-secret-key-do-not-use-in-production
JWT_ALGORITHM=HS256
JWT_REQUIRE_AUTH=false
```

### Authentication Middleware

The backend automatically:
1. Extracts JWT tokens from `Authorization: Bearer <token>` headers
2. Verifies token signature and expiration
3. Extracts `user_id` from token payload
4. Makes `user_id` available to endpoints via dependency injection

## API Usage

### With Authentication Enabled

```bash
# 1. Get JWT token from login service
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# 2. Use token in API requests
curl -X POST "http://localhost:8000/upload/document" \
     -H "Authorization: Bearer $TOKEN" \
     -F "file=@document.pdf" \
     -F "description=Medical report"

curl -X POST "http://localhost:8000/chat/message" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"message": "I have a headache", "session_id": "session_123"}'
```

### Development Mode (Authentication Disabled)

```bash
# When JWT_REQUIRE_AUTH=false, you can still pass user_id as query parameter
curl -X POST "http://localhost:8000/upload/document?user_id=test_user" \
     -F "file=@document.pdf" \
     -F "description=Medical report"
```

## Endpoint Changes

All protected endpoints now use dependency injection for user authentication:

### Before (Query Parameter)
```python
@router.post("/upload/document")
async def upload_document(
    user_id: str,  # Query parameter
    file: UploadFile = File(...)
):
```

### After (JWT Authentication)
```python
from src.auth.dependencies import AuthenticatedUserId

@router.post("/upload/document")  
async def upload_document(
    user_id: AuthenticatedUserId,  # Extracted from JWT token
    file: UploadFile = File(...)
):
```

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Authorization header required"
}
```

### 403 Forbidden  
```json
{
  "detail": "Invalid or expired token"
}
```

## Development and Testing

### Generate Test Tokens

Use the provided `test_auth_example.py` script to generate test JWT tokens:

```bash
python test_auth_example.py
```

### Disable Authentication for Development

Set in your `.env` file:
```bash
JWT_REQUIRE_AUTH=false
```

This allows endpoints to work without JWT tokens for development purposes.

## Security Considerations

1. **Secret Key**: Use a strong, random secret key in production
2. **Token Expiration**: Set appropriate expiration times (1-24 hours)
3. **HTTPS**: Always use HTTPS in production for token transmission
4. **Key Rotation**: Implement regular JWT secret key rotation
5. **Revocation**: Consider implementing token revocation for logged-out users

## Integration with Login Service

The login service should:

1. **Issue Tokens**: Generate JWT tokens with correct payload structure
2. **Share Secret**: Use the same JWT secret key as the backend
3. **Set Expiration**: Include appropriate `exp` claim
4. **User Management**: Maintain consistent `user_id` values

Example login service response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user_id": "user_123456789"
}
```
