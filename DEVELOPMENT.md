# Development Guide

## Environment Setup

### Backend

1. **Python Environment**
   - Use Python 3.8 or higher
   - Create and activate a virtual environment:
     ```bash
     python -m venv venv
     source venv/bin/activate  # On Windows: .\venv\Scripts\activate
     ```

2. **Dependencies**
   - Install requirements:
     ```bash
     pip install -r requirements.txt
     ```
   - Key dependencies:
     - FastAPI for API framework
     - LangChain for AI integration
     - OpenAI for GPT-4 access
     - python-dotenv for environment management

3. **Environment Variables**
   - Copy `.env.example` to `.env`
   - Required variables:
     ```
     OPENAI_API_KEY=your_api_key
     ```

### Frontend

1. **Node.js Environment**
   - Use Node.js 16 or higher
   - Install dependencies:
     ```bash
     npm install
     ```

2. **Key Dependencies**
   - React 18
   - Material-UI v5
   - Emotion for styled components
   - Axios for API calls

## Development Workflow

### Running the Application

1. **Backend**
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```
   - API will be available at http://localhost:8000
   - Swagger docs at http://localhost:8000/docs

2. **Frontend**
   ```bash
   cd frontend
   npm start
   ```
   - Application will run at http://localhost:3000

### Code Structure

#### Backend

```
backend/
├── app/
│   ├── main.py           # Application entry point
│   ├── routers/          # API route handlers
│   │   ├── chat.py       # Chat endpoints
│   │   └── documents.py  # Document management
│   ├── services/         # Business logic
│   │   ├── chatgpt.py    # GPT integration
│   │   └── document.py   # Document processing
│   └── models/          # Data models
└── tests/              # Test files
```

#### Frontend

```
frontend/
├── src/
│   ├── components/       # React components
│   │   ├── Chatbot.js   # Chat interface
│   │   └── Questionnaire.js
│   ├── services/        # API services
│   └── App.js          # Main component
```

## Component Guidelines

### Frontend Components

1. **Styling**
   - Use Material-UI's styled components
   - Follow the theme configuration
   - Maintain consistent spacing
   - Use responsive design patterns

2. **State Management**
   - Use React hooks effectively
   - Implement proper error handling
   - Optimize re-renders

### Backend Services

1. **API Design**
   - RESTful endpoints
   - Proper error handling
   - Input validation
   - Clear response structures

2. **AI Integration**
   - Efficient token usage
   - Proper error handling for API calls
   - Clear response processing

## Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## Code Style

### Python (Backend)
- Follow PEP 8 guidelines
- Use type hints
- Document functions and classes

### JavaScript (Frontend)
- Use ESLint configuration
- Follow React best practices
- Document complex logic

## Git Workflow

1. **Branch Naming**
   - feature/feature-name
   - fix/bug-description
   - update/component-name

2. **Commit Messages**
   - Clear and descriptive
   - Present tense
   - Reference issues when applicable

3. **Pull Requests**
   - Detailed description
   - List of changes
   - Testing notes

## Deployment

### Backend
1. Install production dependencies
2. Set up environment variables
3. Run with production server (e.g., Gunicorn)

### Frontend
1. Build production bundle:
   ```bash
   npm run build
   ```
2. Serve static files

## Troubleshooting

### Common Issues

1. **OpenAI API Issues**
   - Check API key validity
   - Verify rate limits
   - Check error responses

2. **Frontend Development**
   - Clear npm cache if needed
   - Check for dependency conflicts
   - Verify API endpoint configuration

3. **Backend Development**
   - Check virtual environment activation
   - Verify package versions
   - Monitor API responses
