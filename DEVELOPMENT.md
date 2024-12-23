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
├── data/
│   └── user_attachments/ # Uploaded files storage
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
│   ├── styles/          # CSS modules
│   │   └── modern.css   # Global styles
│   └── App.js          # Main component
```

## Development Guidelines

### Mobile-First Development

1. **Responsive Design**
   - Use relative units (rem, em, %) over fixed pixels
   - Implement mobile-first media queries
   - Test on various screen sizes
   - Ensure touch targets are at least 44x44px

2. **Performance**
   - Optimize images and assets
   - Implement lazy loading
   - Minimize bundle size
   - Use code splitting

3. **UI/UX Guidelines**
   - Clear visual hierarchy
   - Adequate spacing for touch targets
   - Visible feedback on interactions
   - Smooth animations (max 300ms)

### CSS Best Practices

1. **Organization**
   - Use CSS modules or styled-components
   - Follow BEM naming convention
   - Group related styles
   - Maintain consistent spacing

2. **Variables**
   ```css
   :root {
     /* Colors */
     --primary-color: #4a90e2;
     --accent-color: #7c4dff;
     
     /* Spacing */
     --spacing-xs: 0.25rem;
     --spacing-sm: 0.5rem;
     --spacing-md: 1rem;
     --spacing-lg: 1.5rem;
     --spacing-xl: 2rem;
     
     /* Typography */
     --font-xs: 0.75rem;
     --font-sm: 0.875rem;
     --font-base: 1rem;
     --font-lg: 1.25rem;
     --font-xl: 1.5rem;
   }
   ```

### Component Guidelines

1. **Structure**
   - Keep components focused and small
   - Use functional components with hooks
   - Implement proper prop validation
   - Document component props

2. **State Management**
   - Use React hooks effectively
   - Implement proper error boundaries
   - Handle loading states
   - Maintain clean data flow

### Testing

1. **Frontend**
   - Unit tests for components
   - Integration tests for user flows
   - E2E tests for critical paths
   - Accessibility testing

2. **Backend**
   - Unit tests for services
   - API endpoint testing
   - Integration tests
   - Performance testing

### Git Workflow

1. **Branches**
   - main: production-ready code
   - develop: integration branch
   - feature/*: new features
   - fix/*: bug fixes

2. **Commits**
   - Use conventional commits
   - Include ticket numbers
   - Keep commits focused
   - Write clear messages

### Deployment

1. **Staging**
   - Test in staging environment
   - Verify all features
   - Check mobile responsiveness
   - Test with real data

2. **Production**
   - Use proper CI/CD pipeline
   - Implement monitoring
   - Set up error tracking
   - Monitor performance

## Documentation

- Keep documentation up to date
- Document all API endpoints
- Include setup instructions
- Maintain changelog

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
