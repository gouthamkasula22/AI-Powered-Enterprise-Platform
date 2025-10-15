# AI-Powered Enterprise Platform

[![CI](https://github.com/gouthamkasula22/AI-Powered-Enterprise-Platform/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/gouthamkasula22/AI-Powered-Enterprise-Platform/actions/workflows/ci.yml)
[![Docker Compose](https://github.com/gouthamkasula22/AI-Powered-Enterprise-Platform/actions/workflows/docker-build.yml/badge.svg?branch=main)](https://github.com/gouthamkasula22/AI-Powered-Enterprise-Platform/actions/workflows/docker-build.yml)
[![codecov](https://codecov.io/gh/gouthamkasula22/AI-Powered-Enterprise-Platform/graph/badge.svg?token=LJLL5PE84T)](https://codecov.io/gh/gouthamkasula22/AI-Powered-Enterprise-Platform)

A production-ready authentication system with integrated AI capabilities, built using FastAPI and React. This platform combines secure user management with powerful AI features including natural language Excel analysis, image generation, and Claude-powered chat.

## What This System Does

This is a comprehensive authentication and AI platform designed for real-world applications. At its core, it provides secure user authentication with role-based access control, but it goes beyond traditional auth systems by integrating advanced AI capabilities that work seamlessly with your user data.

The system handles everything from user registration and login to complex operations like analyzing Excel files using natural language queries, generating images from text prompts, and maintaining intelligent chat conversations. It's built with clean architecture principles, making it maintainable and scalable for production use.

## Key Features

### Authentication & Security
The authentication system uses JWT tokens with refresh rotation, Argon2 password hashing, and comprehensive role-based access control. Users can register with email verification, reset passwords securely, and manage their profiles. The RBAC system supports three role levels (USER, ADMIN, SUPERADMIN) with granular permissions that control access to different parts of the application.

OAuth integrations with Google, Facebook, and LinkedIn are implemented, allowing users to sign in with their existing accounts. The system includes CSRF protection, SQL injection prevention through SQLAlchemy, and follows security best practices throughout.

### Excel Q&A System
One of the standout features is the Excel Q&A system, which lets users upload Excel files and ask questions in plain English. Behind the scenes, it uses Claude AI (claude-3-haiku-20240307) to convert natural language into executable pandas code, validates the code for security, and runs it in a sandboxed environment with timeout protection.

The system automatically generates intelligent example questions based on the uploaded file's column types. For instance, if you upload a sales spreadsheet with columns like "Units Sold" and "Segment", it will suggest questions like "What is the total Units Sold by Segment?" The generated code handles edge cases like column names with spaces, and results are displayed in interactive tables using AG Grid.

Users can view their query history, see the generated pandas code alongside the results, and work with multiple sheets within the same Excel file. The system includes caching for frequently accessed sheets and query result optimization.

### Image Generation
The image generation feature integrates with Stability AI to create images from text prompts. Users can specify style preferences, image dimensions, and quality settings. Generated images are stored with metadata and can be retrieved from a personal gallery. The system uses background tasks to handle the generation process asynchronously, providing real-time status updates.

### Claude-Powered Chat
The chat system provides a Claude-like interface where users can have multi-turn conversations with AI. It supports document context, allowing the AI to answer questions based on uploaded documents. Chat threads are persisted, letting users return to previous conversations. The system integrates with both Anthropic's Claude and Google's Gemini models.

Messages are displayed in a clean, modern interface with markdown rendering, code syntax highlighting, and proper formatting. Users can create multiple chat threads, organize conversations, and the system maintains context across the conversation.

### User Management & Admin Tools
Admins get a comprehensive dashboard for managing users, assigning roles, and monitoring system activity. The admin interface shows user statistics, recent registrations, and role distributions. Superadmins have additional privileges for system configuration and user role management.

The system includes complete user profile management where users can update their information, change passwords, manage security settings, and customize preferences. All user actions are tracked and audit-ready.

## Technical Architecture

### Backend Stack
The backend is built with FastAPI 0.104+ running on Python 3.11+. It uses PostgreSQL 17 with SQLAlchemy for data persistence, including async support for better performance. The architecture follows Clean Architecture principles with distinct layers:

- **Domain Layer**: Core entities, value objects, and business rules
- **Application Layer**: Use cases and business logic orchestration  
- **Infrastructure Layer**: Database implementations, external API integrations (Anthropic, Stability AI, Google AI)
- **Presentation Layer**: FastAPI routes and API schemas

Key backend technologies include Alembic for database migrations, Redis for caching and background tasks, and comprehensive test coverage using pytest with async support. The Excel processing uses pandas, openpyxl, and includes a custom code validator with sandboxing.

### Frontend Stack
The frontend uses React 18 with Vite for fast development and optimized builds. It's styled with Tailwind CSS for a modern, responsive design. State management uses React Context API, and routing is handled by React Router v6.

Major UI components include AG Grid Community for data tables in the Excel Q&A system, React Markdown for rendering chat messages, React Hook Form for form handling, and React Hot Toast for notifications. The interface is clean and professional, designed to feel like a modern SaaS application.

### Development Environment
The project uses Docker Compose for easy local development, with services for PostgreSQL, Redis, and PgAdmin. All dependencies are version-pinned for consistency. The backend includes type hints throughout and uses mypy for type checking. The frontend has ESLint configured with React-specific rules.

## Project Structure

```
├── backend/                    # FastAPI application
│   ├── src/
│   │   ├── domain/            # Business entities and rules
│   │   ├── application/       # Use cases and services
│   │   ├── infrastructure/    # External integrations
│   │   └── presentation/      # API routes
│   ├── tests/                 # Backend tests
│   └── alembic/               # Database migrations
├── frontend/                  # React application
│   └── src/
│       ├── components/        # React components
│       ├── pages/             # Page components
│       ├── contexts/          # Context providers
│       └── services/          # API service layer
├── docs/                      # Documentation
├── scripts/                   # Utility scripts
└── tests/                     # Integration tests
```

## Getting Started

### Prerequisites
- Python 3.11 or higher
- Node.js 18 or higher
- PostgreSQL 17
- Redis
- Docker and Docker Compose (recommended)

### Environment Setup

You'll need API keys for the AI features:
- **ANTHROPIC_API_KEY**: For Excel Q&A and Claude chat
- **STABILITY_API_KEY**: For image generation
- **GOOGLE_API_KEY**: For Gemini chat support

Create a `backend/.env` file with your configuration:

```env
DATABASE_URL=postgresql+asyncpg://auth_user:auth_password@localhost:5433/auth_db
JWT_SECRET_KEY=your-secret-key-here
ANTHROPIC_API_KEY=your-anthropic-key
STABILITY_API_KEY=your-stability-key
GOOGLE_API_KEY=your-google-key
```

### Quick Start with Docker

```bash
# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec backend alembic upgrade head

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Manual Setup

Backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn src.main:app --reload
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

## API Documentation

The API is fully documented with interactive Swagger UI at `http://localhost:8000/docs`. Key endpoint groups include:

- **Authentication** (`/api/v1/auth`): Register, login, token refresh, password reset
- **Users** (`/api/v1/users`): Profile management, password changes
- **Excel** (`/api/v1/excel`): Document upload, query submission, sheet operations
- **Images** (`/api/v1/images`): Image generation, gallery, task status
- **Chat** (`/api/v1/chat`): Thread management, message operations
- **Admin** (`/api/v1/admin`): User management, role assignment

## Testing

The project includes comprehensive tests:

```bash
# Backend tests
cd backend
pytest tests/

# Run end-to-end Excel Q&A test
python tests/e2e_excel_qa_test.py

# Frontend tests
cd frontend
npm test
```

## Security Considerations

The system implements multiple security layers:

1. **Password hashing** using Argon2 with appropriate cost factors
2. **JWT tokens** with short expiration (30 minutes) and secure refresh mechanism
3. **Code validation** for Excel queries to prevent arbitrary code execution
4. **Sandboxed execution** with 5-second timeout for query processing
5. **Input validation** using Pydantic models across all endpoints
6. **SQL injection prevention** through SQLAlchemy ORM
7. **CORS configuration** to restrict API access
8. **Role-based authorization** checked on every protected endpoint

## Deployment

For production deployment:

1. Use environment variables for all secrets
2. Enable HTTPS with valid SSL certificates
3. Configure PostgreSQL with connection pooling
4. Set up Redis for production with persistence
5. Build the frontend with `npm run build`
6. Serve frontend through a CDN or reverse proxy
7. Configure logging and monitoring
8. Set up automated backups for PostgreSQL
9. Enable rate limiting on the API
10. Review and adjust JWT expiration times

The system is designed to scale horizontally. The stateless API can run multiple instances behind a load balancer, and the database supports read replicas for scaling reads.

## Contributing

Contributions are welcome. Please ensure:
- Code follows existing patterns and architecture
- Tests are included for new features
- Documentation is updated
- Type hints are used in Python code
- ESLint rules are followed for frontend code

## License

MIT License - see LICENSE file for details.

---

Built with FastAPI, React, PostgreSQL, Claude AI, and modern web technologies.
