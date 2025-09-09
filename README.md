# User Authentication System

A production-ready full-stack authentication system built with FastAPI and React, featuring JWT authentication, OAuth integration, and a Claude-like dashboard interface.

## 🏗️ Architecture

### Backend (FastAPI)
- **API Framework**: FastAPI with async/await support
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT tokens with bcrypt password hashing
- **OAuth**: Google, Facebook, LinkedIn integration
- **Architecture**: Clean Architecture with separation of concerns

### Frontend (React)
- **Framework**: React 18 with Vite
- **Styling**: Tailwind CSS
- **Routing**: React Router v6
- **State Management**: React Context API
- **UI**: Claude-like dashboard interface

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Docker & Docker Compose (for easy database setup)

### 1. Clone and Setup Environment

```bash
git clone <repository-url>
cd "User Authentication Systems"
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your configuration
```

### 3. Database Setup

```bash
# Option 1: Using Docker (Recommended)
docker-compose up -d postgres redis

# Option 2: Manual PostgreSQL installation
# Install PostgreSQL and create database 'auth_db'
```

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 5. Run the Application

```bash
# Terminal 1: Backend
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

## 📁 Project Structure

```
User Authentication Systems/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API routes
│   │   ├── core/            # Configuration & security
│   │   ├── models/          # Database models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   ├── repositories/    # Data access layer
│   │   └── middleware/      # Custom middleware
│   ├── alembic/            # Database migrations
│   ├── tests/              # Backend tests
│   ├── requirements.txt    # Python dependencies
│   └── main.py            # FastAPI application
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/         # Page components
│   │   ├── contexts/      # React contexts
│   │   ├── services/      # API services
│   │   ├── hooks/         # Custom hooks
│   │   └── utils/         # Utility functions
│   ├── package.json       # Node dependencies
│   └── vite.config.js    # Vite configuration
├── Assets/                # Project documentation
├── docker-compose.yml    # Development services
└── README.md             # This file
```

## 🛠️ Development Milestones

### ✅ Project Structure Setup
- [x] Backend structure with clean architecture
- [x] Frontend structure with modern React setup
- [x] Docker configuration for development
- [x] Environment configuration

### 🏗️ Milestone 1: Foundation & Database Setup
- [ ] PostgreSQL database models
- [ ] FastAPI basic endpoints
- [ ] React routing and components
- [ ] Environment configuration

### 🔐 Milestone 2: Authentication System
- [ ] JWT authentication implementation
- [ ] Password hashing with bcrypt
- [ ] Login/Register forms
- [ ] Protected routes

### 🎨 Milestone 3: Dashboard & UI
- [ ] Claude-like dashboard interface
- [ ] User profile management
- [ ] Responsive design
- [ ] Error handling

### 🌐 Milestone 4: Social Authentication
- [ ] OAuth 2.0 implementation
- [ ] Google, Facebook, LinkedIn login
- [ ] Account linking system
- [ ] Social profile integration

## 🔧 Technologies Used

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM with async support
- **Alembic** - Database migrations
- **PostgreSQL** - Primary database
- **Redis** - Caching and sessions
- **Pydantic** - Data validation
- **Passlib + bcrypt** - Password hashing
- **Python-JOSE** - JWT token handling
- **FastAPI-Mail** - Email functionality

### Frontend
- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **React Router v6** - Client-side routing
- **Tailwind CSS** - Utility-first CSS
- **Axios** - HTTP client
- **React Hook Form** - Form handling
- **React Hot Toast** - Notifications
- **Heroicons** - Icon library

### DevOps & Tools
- **Docker** - Containerization
- **Git** - Version control
- **ESLint** - Code linting
- **Prettier** - Code formatting
- **PyTest** - Backend testing
- **Jest** - Frontend testing

## 🔒 Security Features

- **Password Security**: bcrypt hashing with 12+ rounds
- **JWT Authentication**: Secure token-based auth
- **Input Validation**: Comprehensive data validation
- **CORS Configuration**: Proper cross-origin settings
- **SQL Injection Prevention**: Parameterized queries
- **XSS Protection**: Input sanitization
- **OAuth 2.0**: Secure third-party authentication

## 📊 Performance Targets

- **Authentication Response**: < 200ms
- **Database Queries**: < 50ms
- **Frontend Load Time**: < 3 seconds
- **Lighthouse Score**: > 90

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 🚀 Deployment

### Environment Variables
Make sure to set all required environment variables in production:

```bash
# Security
SECRET_KEY=your-production-secret-key
DATABASE_URL=your-production-database-url

# OAuth Credentials
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
# ... other OAuth credentials

# Email Configuration
SMTP_HOST=your-smtp-host
SMTP_USERNAME=your-smtp-username
SMTP_PASSWORD=your-smtp-password
```

### Production Checklist
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] SSL certificates configured
- [ ] CORS origins updated
- [ ] Rate limiting enabled
- [ ] Monitoring setup

## 📝 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For questions or issues, please:
1. Check the documentation
2. Search existing issues
3. Create a new issue with details

---

**Built with ❤️ using FastAPI and React**
