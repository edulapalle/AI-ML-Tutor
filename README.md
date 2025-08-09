# AI Study Assistant

This repository contains an AI bootcamp capstone project that demonstrates a secure, personalized AI study assistant with authentication and RAG (Retrieval-Augmented Generation) capabilities.

## Project Details

- **Project Type**: AI Bootcamp Capstone Project
- **Date**: August 2025
- **Author**: Santosh Edulapalle

## Description

This project implements a comprehensive AI study assistant specifically designed for Machine Learning and AI education. It combines secure user authentication, personalized learning experiences, and RAG (Retrieval-Augmented Generation) capabilities. The application features:

- **Secure Authentication**: User registration and login with Supabase
- **ML/AI Focused Learning**: Specialized curriculum covering 11 key ML/AI topics
- **Personalized Study Methods**: Three distinct study approaches (theory, testing, hands-on)
- **Study Tracking**: Progress monitoring and goal management
- **RAG Integration**: AI-powered question answering with document retrieval
- **Modern UI**: Clean, responsive interface optimized for ML/AI learning

## Features

### 🔐 Authentication & User Management
- Secure user registration with comprehensive study information
- JWT-based authentication with session management
- User profile management with study preferences
- Password hashing and secure token handling

### 🎯 Personalized Learning
- Study level assessment (beginner, intermediate, advanced)
- ML/AI topic specialization with 11 focused areas:
  - ML Foundations
  - Supervised Learning
  - Unsupervised Learning
  - Model Evaluation
  - Data Prep & Features (EDA)
  - Optimization
  - Interpretability & Ethics
  - Deep Learning Basics
  - LLM & Generative AI
  - Practical ML
  - Production ML
- Study method preferences:
  - Study Only (concepts and theory)
  - Study and Test (with quizzes and assessments)
  - Study and Live Example Demo Build (hands-on projects)
- Current goals and progress monitoring
- Machine learning curriculum alignment

### 🤖 AI-Powered Assistance
- RAG (Retrieval-Augmented Generation) integration
- Personalized responses based on user profile
- Document retrieval and context-aware answers
- Study session tracking and analytics

### 📊 Study Management
- Learning goals tracking
- Progress monitoring
- Study session history
- Topic proficiency tracking
- Study materials organization

## Getting Started

### Prerequisites

1. Python 3.8 or higher
2. Supabase account and project
3. OpenAI API key
4. Milvus/Zilliz account (optional, for RAG features)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd rag-vercel-example
   ```

2. **Create and activate virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   # Install uv for package management
   pip install uv
   
   # Install project dependencies
   uv pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Copy example environment file
   cp env.example .env
   
   # Edit the .env file with your actual credentials
   # IMPORTANT: Never commit your .env file to version control!
   ```

5. **Configure your .env file**
   ```env
   # OpenAI Configuration (required)
   OPENAI_API_KEY=your_openai_api_key_here
   
   # Supabase Configuration (required for authentication)
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_ANON_KEY=your_supabase_anon_key_here
   SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here
   
   # JWT Configuration (required for authentication)
   JWT_SECRET_KEY=your_jwt_secret_key_here_change_in_production
   
   # Milvus/Zilliz Configuration (optional - for RAG features)
   MILVUS_URI=your_milvus_uri_here
   MILVUS_TOKEN=your_milvus_token_here
   COLLECTION_NAME=youtube_creator_videos
   
   # Server Configuration (optional)
   HOST=0.0.0.0
   PORT=8000
   
   # Security Configuration (optional)
   CORS_ORIGINS=http://localhost:3000,http://localhost:8000
   SESSION_SECRET=your_session_secret_here_change_in_production
   ```

6. **Set up Supabase database**
   - Create a new Supabase project
   - Run the SQL commands from `database_schema.sql` in your Supabase SQL editor
   - Configure Row Level Security (RLS) policies as defined in the schema

7. **Run the application**
   ```bash
   python index.py
   ```

8. **Access the application**
   - Open your browser and navigate to `http://localhost:8000`
   - You'll be redirected to the login page
   - Register a new account or log in with existing credentials

## Database Schema

The application uses Supabase with the following main tables:

- **users**: User profiles and study preferences
- **study_sessions**: Learning session tracking
- **chat_history**: Conversation history
- **learning_goals**: User-defined learning objectives
- **study_materials**: User's study resources
- **progress_tracking**: Learning progress monitoring

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/validate` - Token validation
- `GET /api/auth/profile` - User profile
- `POST /api/auth/logout` - User logout

### Chat & Learning
- `POST /api/chat` - AI chat with RAG (requires authentication)
- `GET /api/reranking-config` - Reranking configuration
- `POST /api/add-document` - Add documents to RAG system

### Pages
- `GET /login` - Login page
- `GET /register` - Registration page
- `GET /dashboard` - Main dashboard (requires authentication)

## Security Features

- **Password Hashing**: Bcrypt-based password encryption
- **JWT Tokens**: Secure session management
- **Row Level Security**: Database-level access control
- **Input Validation**: Comprehensive form validation
- **CORS Protection**: Cross-origin request security
- **Environment Variables**: Secure configuration management

## Technologies Used

### Backend
- **FastAPI**: Modern Python web framework
- **Supabase**: PostgreSQL database with real-time features
- **OpenAI**: AI language model integration
- **JWT**: Secure authentication tokens
- **Pydantic**: Data validation and serialization

### Frontend
- **HTML5/CSS3**: Modern, responsive design
- **JavaScript**: Interactive user interface
- **Font Awesome**: Icon library
- **Jinja2**: Template engine

### DevOps
- **Vercel**: Deployment platform
- **uv**: Fast Python package manager
- **Docker**: Containerization (optional)

## Project Structure

```
rag-vercel-example/
├── index.py                 # Main FastAPI application
├── auth_models.py          # Authentication data models
├── auth_service.py         # Authentication business logic
├── requirements.txt        # Python dependencies
├── database_schema.sql     # Database schema
├── env.example             # Environment variables template
├── templates/              # HTML templates
│   ├── login.html          # Login page
│   ├── register.html       # Registration page
│   └── index.html          # Main dashboard
├── static/                 # Static assets
│   ├── css/
│   │   ├── auth.css        # Authentication styles
│   │   └── style.css       # Main styles
│   └── js/
│       ├── auth.js         # Authentication logic
│       └── chat.js         # Chat functionality
└── README.md              # Project documentation
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is created as part of an AI bootcamp capstone project.

## Support

For support and questions, please refer to the project documentation or create an issue in the repository. 