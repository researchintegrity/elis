# ELIS Scientific Image Analysis System

ELIS is a document management and image analysis system built with FastAPI, MongoDB, and Celery. It provides user authentication, document upload with async PDF processing, and image extraction capabilities.

## Features

- User authentication and management with JWT tokens
- Document upload and management with storage quotas
- Asynchronous PDF processing with Celery workers
- Image extraction and retrieval
- Full test coverage with 62 passing tests
- Docker containerization for easy deployment
- MongoDB for persistent storage
- Redis for task queue and caching

## Project Structure

```
elis-system/
├── app/
│   ├── main.py                 # Main FastAPI application
│   ├── schemas.py              # Pydantic validation models
│   ├── celery_config.py        # Celery configuration
│   ├── routes/                 # API route handlers
│   │   ├── auth.py             # Authentication endpoints
│   │   ├── users.py            # User management endpoints
│   │   ├── documents.py        # Document upload and management
│   │   └── images.py           # Image retrieval and management
│   ├── tasks/                  # Celery task definitions
│   │   └── image_extraction.py # Async PDF image extraction
│   ├── db/                     # Database layer
│   │   └── mongodb.py          # MongoDB connection & configuration
│   └── utils/                  # Utility functions
│       ├── security.py         # JWT, password hashing
│       └── file_storage.py     # File upload and management
├── tests/                      # Test suite (62 tests)
│   ├── conftest.py             # Pytest configuration and fixtures
│   ├── test_document_upload.py # Document and image tests
│   └── test_user_operations.py # User management tests
├── workspace/                  # User-uploaded files (created at runtime)
├── docker-compose.yml          # Multi-container orchestration
├── Dockerfile                  # API container definition
├── Dockerfile.worker           # Celery worker container definition
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Getting Started

### Prerequisites

- Docker and Docker Compose (for containerized setup)
- Python 3.12+
- Git

### Quick Start with Docker (Recommended)

The easiest way to get the system running is with Docker Compose. This starts all required services automatically.

1. Clone and navigate to the repository:

```bash
git clone <repository-url>
cd elis-system
```

2. Start all services:

```bash
docker-compose up -d
```

3. Verify services are running:

```bash
docker-compose ps
```

All services will be available once running:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- Flower Dashboard: http://localhost:5555
- MongoDB: localhost:27017
- Redis: localhost:6379

### Manual Setup (Local Development)

If you prefer to run services locally without Docker, follow these steps:

1. Clone the repository:

```bash
git clone <repository-url>
cd elis-system
```

2. Create and activate a virtual environment:

```bash
python -m venv uvenv
source uvenv/bin/activate  # On Windows: uvenv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Ensure required services are running:

- MongoDB: Start MongoDB service or use a remote instance
- Redis: Start Redis server for Celery task queue

5. Configure environment variables:

```bash
cp .env.example .env
# Edit .env with your settings
```

6. Start the services in separate terminals:

Terminal 1 - FastAPI:
```bash
uvicorn app.main:app --reload
```

Terminal 2 - Celery Worker:
```bash
celery -A app.celery_config worker -l info
```

Terminal 3 - Flower Monitoring (optional):
```bash
celery -A app.celery_config flower --port=5555
```

The API will be available at http://localhost:8000

### Technology Stack

The system uses several key technologies:

**Web Framework**
- FastAPI: Modern Python web framework with automatic API documentation

**Database**
- MongoDB: NoSQL database for flexible document storage
- PyMongo: MongoDB Python driver for database operations

**Asynchronous Task Processing**
- Celery: Distributed task queue for background jobs
- Redis: Message broker and result backend for Celery

**Authentication & Security**
- PyJWT: JWT token generation and validation
- Passlib & Bcrypt: Secure password hashing

**File Handling**
- python-multipart: Form data and file upload handling

**Validation & Documentation**
- Pydantic: Data validation and automatic schema generation
- email-validator: Email address validation

**Testing**
- Pytest: Testing framework
- FastAPI TestClient: API testing utilities

### Docker Architecture

The system runs multiple containers orchestrated by Docker Compose:

**API Container**
- Runs FastAPI application on port 8000
- Mounts workspace volume for file storage
- Depends on MongoDB and Redis

**Worker Containers (2 instances)**
- Run Celery workers for background PDF processing
- Access shared workspace volume
- Connect to Redis for task queue
- Connect to MongoDB for result storage

**MongoDB**
- Main database for user data and documents
- Runs on port 27017

**MongoDB Test Database**
- Isolated database for test execution
- Runs on port 27018
- Unauthenticated for local development

**Redis**
- Message broker for Celery
- Result backend for task status
- Runs on port 6379

**Flower**
- Celery monitoring dashboard
- Real-time view of background tasks
- Available on port 5555

## API Documentation

Interactive API documentation is available at [Swagger UI](http://localhost:8000/docs) or [ReDoc](http://localhost:8000/redoc).

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

Response includes access token and user details.

#### Login User

```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=john_doe&password=SecurePassword123
```

Returns access token for authenticated requests.

### User Management Endpoints

#### Get Current User Profile

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

Removes user and all associated data.

### Document Management Endpoints

#### Upload Document

```http
POST /documents/upload
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

file: <PDF file>
```

Returns document ID and extraction status (pending or completed).

#### List Documents

```http
GET /documents
Authorization: Bearer <access_token>
```

Returns paginated list of user documents with storage quota information.

#### Get Document Details

```http
GET /documents/{document_id}
Authorization: Bearer <access_token>
```

#### Delete Document

```http
DELETE /documents/{document_id}
Authorization: Bearer <access_token>
```

Deletes document and associated extracted images.

### Image Management Endpoints

#### Upload Image

```http
POST /images/upload
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

file: <image file>
document_id: <document_id>
```

#### List Images

```http
GET /images
Authorization: Bearer <access_token>
```

#### Get Extracted Images for Document

```http
GET /documents/{document_id}/images
Authorization: Bearer <access_token>
```

#### Delete Image

```http
DELETE /images/{image_id}
Authorization: Bearer <access_token>
```

## Architecture

### System Overview

The ELIS system uses a distributed architecture with separate services for web APIs, background processing, and data storage:

```
┌─────────────────┐
│   FastAPI       │
│   (Port 8000)   │ ◄────┐
└────────┬────────┘      │
         │               │
         ├─► MongoDB     │ Client
         │   (Main DB)   │ Requests
         │               │
         ├─► Redis ◄─────┼──────┐
         │                      │
         └───► Celery Workers   │
              (Task Processing) │
                                │
         ┌──────────────────────┘
         │
      Workspace
    (Shared Storage)
```

### Component Responsibilities

#### FastAPI API Layer

- Handles HTTP requests and responses
- Performs request validation with Pydantic
- Manages user authentication with JWT tokens
- Routes requests to appropriate handlers
- Submits long-running tasks to Celery

#### Celery Workers

- Process background tasks asynchronously
- Extract images from uploaded PDFs
- Perform heavy computations without blocking API
- Retry failed tasks automatically
- Multiple workers for parallel processing

#### MongoDB Database

- Stores user accounts and authentication data
- Stores document metadata and extraction history
- Maintains extraction status and task information
- Provides persistent data layer

#### Redis Message Broker

- Transfers task messages between API and workers
- Stores task results temporarily
- Manages task queue distribution
- Enables worker communication

### Data Flow - Document Upload

1. User uploads PDF file to FastAPI endpoint
2. FastAPI validates file and saves to `workspace/{user_id}/pdfs/`
3. MongoDB document record created with status `pending`
4. Celery task message sent to Redis
5. Available Celery worker picks up task
6. Worker extracts images from PDF
7. Images saved to `workspace/{user_id}/images/extracted/{doc_id}/`
8. MongoDB document status updated to `completed`
9. API returns document ID (can be checked for status)

### Module Organization

#### Database Layer (`app/db/`)

- MongoDB connection management
- Singleton pattern for connection pooling
- Dynamic connection URL reading for testing
- Collection access methods

#### Security Layer (`app/utils/`)

- Password hashing and verification using bcrypt
- JWT token generation and validation
- OAuth2 scheme implementation
- User authentication dependency

#### Task Processing (`app/celery_config.py` and `app/tasks/`)

- Celery configuration and initialization
- Async task definitions for image extraction
- Redis integration for message brokering
- Retry logic and error handling

#### Routes Layer (`app/routes/`)

- Authentication endpoints (register, login)
- User management endpoints (profile, update, delete)
- Document upload and management endpoints
- Image management endpoints
- Clear separation of concerns

#### Schemas Layer (`app/schemas.py`)

- Pydantic data validation
- Request/response models
- Type hints for IDE support
- Automatic OpenAPI documentation

#### File Storage (`app/utils/file_storage.py`)

- User-isolated directory management
- PDF upload handling
- Image extraction output paths
- File system operations

## Testing

Run the complete test suite with pytest:

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_document_upload.py -v

# Run with coverage report
pytest tests/ --cov=app --cov-report=html
```

### Test Organization

- **test_user_operations.py**: User registration, login, and profile management
- **test_document_upload.py**: Document upload, image extraction, and file storage
- Tests use separate MongoDB database on port 27018
- Redis connection verified for Celery task testing
- Full integration testing with actual services

### Test Data

Test fixtures automatically:

- Create temporary test database
- Clean up test documents after each test
- Isolate user data per test
- Provide sample PDF and image files

## Environment Configuration

### Required Variables

```env
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=elis_system
JWT_SECRET=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Docker Environment

When running with Docker Compose, environment variables are automatically configured:

```env
MONGODB_URL=mongodb://mongodb:27017
REDIS_URL=redis://redis:6379/0
```

## Dependencies

### Web Framework

- **fastapi**: Modern async web framework with automatic API documentation
- **uvicorn**: ASGI server for running FastAPI
- **starlette**: Web framework foundation used by FastAPI

### Database

- **pymongo**: Python driver for MongoDB
- **dnspython**: DNS support for MongoDB connection strings

### Async Task Processing

- **celery**: Distributed task queue
- **redis**: Message broker and result backend
- **flower**: Celery monitoring and management interface

### Authentication & Security

- **pyjwt**: JWT token generation and validation
- **passlib**: Password hashing framework
- **bcrypt**: Secure password hashing algorithm
- **cryptography**: Cryptographic recipes and primitives

### Data Validation

- **pydantic**: Data validation and serialization using type hints
- **email-validator**: Email validation for user registration

### Utilities

- **python-dotenv**: Environment variable management
- **python-multipart**: Multipart form data parsing
- **typing-extensions**: Backports of new typing features

### Development & Testing

- **pytest**: Testing framework
- **pytest-asyncio**: Async test support
- **httpx**: HTTP client for API testing

## Development

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

## Troubleshooting

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
