# MediTwin Frontend

A modern, responsive frontend for the MediTwin JWT authentication system.

## Features

- 🔐 **Secure JWT Authentication** - Complete login/register flow
- 🔄 **Automatic Token Refresh** - Seamless session management
- 🎨 **Modern UI** - Beautiful, responsive design
- 🚀 **API Testing** - Built-in tools to test protected endpoints
- 📱 **Mobile Friendly** - Works perfectly on all devices

## Quick Start

1. **Make sure your backend is running:**
   ```bash
   cd /home/user/backend/meditwin-backend
   source .venv/bin/activate
   uvicorn main:app --host 0.0.0.0 --port 8081 --reload
   ```

2. **Open the frontend:**
   ```bash
   cd /home/user/backend/meditwin-frontend
   python3 -m http.server 3000
   ```

3. **Access the app:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8081
   - API Docs: http://localhost:8081/docs

## How It Works

### Authentication Flow

1. **User Registration/Login** 
   - Frontend sends credentials to `/auth/signup` or `/auth/login`
   - Backend creates `user_id` in database and returns JWT tokens
   - Frontend stores tokens in localStorage

2. **Protected API Calls**
   - Frontend includes JWT in `Authorization: Bearer <token>` header
   - Backend extracts and validates JWT 
   - Backend automatically gets `user_id` from token `sub` claim
   - Backend scopes all data operations to that `user_id`

3. **Token Refresh**
   - When access token expires (15 min), frontend uses refresh token
   - Backend issues new access token and rotates refresh token
   - Process is transparent to user

### Key Security Features

- ✅ **No user_id in frontend** - All identity comes from JWT
- ✅ **Automatic token rotation** - Refresh tokens are rotated on use
- ✅ **Secure storage** - Tokens stored in localStorage (upgrade to httpOnly cookies for production)
- ✅ **Session timeout** - Access tokens expire in 15 minutes
- ✅ **Multi-device logout** - Can revoke all sessions

## API Endpoints Demonstrated

| Endpoint | Purpose | Shows |
|----------|---------|-------|
| `GET /users/me` | Get user profile | JWT validation, user extraction |
| `GET /api/user-data` | Get user documents | Data scoping by user_id |
| `POST /api/user-document` | Create document | Auto owner_id assignment |
| `POST /auth/refresh` | Refresh tokens | Token rotation |

## Testing the Implementation

1. **Register a new account**
2. **Login and see JWT token displayed**
3. **Test protected endpoints** - Notice how user_id is automatically extracted
4. **Try token refresh** - See new tokens issued
5. **Test logout** - Watch tokens get revoked

## Production Deployment

For production, consider these enhancements:

- Use httpOnly cookies instead of localStorage
- Add CSRF protection
- Implement rate limiting
- Add proper error logging
- Use HTTPS everywhere
- Add token blacklisting for immediate revocation

## File Structure

```
meditwin-frontend/
├── index.html          # Complete single-page application
└── README.md          # This documentation
```

The frontend is intentionally kept as a single HTML file for simplicity, but in production you'd typically split it into separate HTML, CSS, and JavaScript files or use a framework like React/Vue.
