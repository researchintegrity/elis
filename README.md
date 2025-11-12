# ELIS User Management System

A modern, modular FastAPI-based authentication and user management system with MongoDB persistence.

## 🏗️ Project Structure

```
elis-system/
├── app/
│   ├── main.py                 # Main FastAPI application
│   ├── schemas.py              # Pydantic validation models
│   ├── routes/                 # API route handlers
│   │   ├── __init__.py
│   │   ├── auth.py             # Authentication endpoints (register, login)
│   │   └── users.py            # User management endpoints
│   ├── db/                     # Database layer
│   │   ├── __init__.py
│   │   └── mongodb.py          # MongoDB connection & configuration
│   └── utils/                  # Utility functions
│       ├── __init__.py
│       └── security.py         # JWT, password hashing, authentication
├── static/                     # Frontend HTML/CSS/JS
│   ├── index.html              # Login/register interface
│   └── success.html            # Post-login success page
├── tests/                      # Test suite
│   └── test_user_management.py
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables
└── README.md                   # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MongoDB running locally or remote instance
- pip or conda

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd elis-system
```

2. **Create virtual environment**
```bash
# Windows PowerShell
python -m venv dev-venv
.\dev-venv\Scripts\Activate.ps1

# Or use the provided script
.\start.ps1
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
# Update .env file with your settings
# Ensure MongoDB is running at MONGODB_URL
# Generate a strong JWT_SECRET for production
```

5. **Start the server**
```bash
# Using uvicorn directly
uvicorn app.main:app --reload

# Or use the provided script
.\start.bat
```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

### Automatic Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Authentication Endpoints

#### Register User
```http
POST /auth/register
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePassword123",
  "full_name": "John Doe"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "username": "john_doe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T10:30:00Z"
  },
  "expires_in": 86400
}
```

#### Login
```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=john_doe&password=SecurePassword123
```

**Response:** Same as register (TokenResponse)

### User Management Endpoints

#### Get Current User
```http
GET /users/me
Authorization: Bearer <access_token>
```

#### Update User Profile
```http
PUT /users/me
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "full_name": "John Updated",
  "email": "newemail@example.com"
}
```

#### Delete User Account
```http
DELETE /users/me
Authorization: Bearer <access_token>
```

#### Get User by Username
```http
GET /users/{username}
Authorization: Bearer <access_token>
```

### General Endpoints

#### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "version": "1.0.0"
}
```

## 🔐 Security Features

### Password Security
- **Hashing**: Bcrypt with automatic salt generation
- **Verification**: Constant-time comparison
- **Minimum Length**: 4 characters

### Authentication
- **JWT Tokens**: HS256 algorithm
- **Bearer Tokens**: OAuth2 compatible
- **Token Expiration**: Configurable (default 24 hours)
- **Stateless**: No session storage required

### Database
- **Indexes**: Unique indexes on username and email
- **Validation**: Pydantic schemas for all inputs
- **Error Handling**: Comprehensive error messages without exposing internals

## 🏗️ Architecture

### Modular Design

**Database Layer (`app/db/`)**
- MongoDB connection management
- Singleton pattern for connection pooling
- Automatic index creation
- Collection access methods

**Security Layer (`app/utils/`)**
- Password hashing and verification
- JWT token generation and validation
- OAuth2 scheme implementation
- User authentication dependency

**Routes Layer (`app/routes/`)**
- Authentication routes (register, login)
- User management routes (profile, update, delete)
- Clear separation of concerns
- Dependency injection for security

**Schemas Layer (`app/schemas.py`)**
- Pydantic data validation
- Request/response models
- Type hints for IDE support
- Automatic OpenAPI documentation

### Data Flow

```
Frontend Request
    ↓
FastAPI Route Handler
    ↓
Dependency Injection (get_current_active_user)
    ↓
Security Validation (JWT verification)
    ↓
MongoDB Database Layer
    ↓
Response with appropriate HTTP status
```

## 🧪 Testing

Run the test suite:
```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_user_management.py -v

# Run with coverage
pytest tests/ --cov=app
```

## 📦 Dependencies

### Core
- **fastapi**: Modern web framework
- **uvicorn**: ASGI server
- **pymongo**: MongoDB Python driver

### Security
- **PyJWT**: JWT token handling
- **passlib**: Password hashing framework
- **bcrypt**: Bcrypt algorithm

### Data
- **pydantic**: Data validation and serialization
- **email-validator**: Email validation

### Utilities
- **python-dotenv**: Environment configuration
- **python-multipart**: Form data parsing

## 🌍 Environment Configuration

### Required Variables
```env
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=elis_system
JWT_SECRET=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
```

### Optional Variables
```env
ENVIRONMENT=development
DEBUG=True
```

## 🛠️ Development

### Code Style
- Use type hints for all function parameters and returns
- Follow PEP 8 conventions
- Document functions with docstrings

### Adding New Endpoints

1. Create route function in appropriate file (`app/routes/`)
2. Define Pydantic schemas in `app/schemas.py`
3. Use dependency injection for security: `current_user: dict = Depends(get_current_active_user)`
4. Return appropriate HTTP status codes
5. Add tests to `tests/`

### Example New Endpoint
```python
from fastapi import APIRouter, Depends, status
from app.utils.security import get_current_active_user
from app.schemas import UserResponse

router = APIRouter(prefix="/example", tags=["Example"])

@router.get("/protected", response_model=UserResponse)
async def protected_endpoint(current_user: dict = Depends(get_current_active_user)):
    """This endpoint requires authentication"""
    return current_user
```

## 🐛 Troubleshooting

### MongoDB Connection Failed
- Ensure MongoDB is running: `mongod` or `mongo` service
- Check MONGODB_URL in .env file
- Verify firewall allows connection to MongoDB port (27017)

### JWT Token Errors
- Ensure JWT_SECRET is set in .env
- Check token hasn't expired
- Verify token format: `Authorization: Bearer <token>`

### Duplicate Key Error
- Username or email already exists in database
- Clear database: `db.users.deleteMany({})`
- Or use different username/email

### Password Verification Failed
- Ensure password meets minimum length (4 characters)
- Check password matches stored hash
- Verify bcrypt library is properly installed

## 📝 License

This project is licensed under the MIT License.

## 👨‍💻 Contributing

1. Create a feature branch
2. Make your changes
3. Run tests: `pytest tests/`
4. Submit a pull request

---

**Version**: 1.0.0  
**Last Updated**: January 2025  
**Status**: Active Development
