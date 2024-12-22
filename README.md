# Biotech Regulatory Compliance Tool

A comprehensive tool for biotech companies to streamline regulatory compliance for product market implementation.

## Features

- Interactive questionnaire for product information gathering
- Intelligent document retrieval system for regulatory guidelines
- AI-powered chatbot for regulatory compliance assistance
- Modern, user-friendly interface

## Tech Stack

### Backend
- FastAPI
- LangChain
- ChromaDB for document storage and retrieval
- OpenAI GPT-4 integration

### Frontend
- React.js
- Material-UI
- Axios for API communication

## Prerequisites

- Python 3.10+
- Node.js 18+
- OpenAI API key
- MongoDB database

## Quick Start

1. Clone the repository:
```bash
git clone <repository-url>
cd biotech_regulatory_tool
```

2. Install all dependencies using Make:
```bash
make install
```

3. Configure environment variables:
Create a `.env` file in the backend directory with the following:
```
OPENAI_API_KEY=your_openai_api_key
MONGODB_URI=your_mongodb_uri
DATABASE_NAME=your_database_name
```

4. Start both servers with a single command:
```bash
make run
```

This will start both the backend server (on port 8000) and the frontend server (on port 3000).

## Manual Installation

If you prefer to install manually or if Make is not available:

1. Set up the backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

2. Set up the frontend:
```bash
cd frontend
npm install
```

3. Start the servers manually:
- Backend: `cd backend && source venv/bin/activate && python -m uvicorn app.main:app --reload`
- Frontend: `cd frontend && npm start`

## Running the Application

1. Start the backend server:
```bash
cd backend
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
uvicorn app.main:app --reload
```

2. Start the frontend development server:
```bash
cd frontend
npm start
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Project Structure

```
biotech_regulatory_tool/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── chatbot.py
│   │   └── document_retrieval.py
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Questionnaire.js
│   │   │   ├── RegulatoryDisplay.js
│   │   │   └── Chatbot.js
│   │   ├── App.js
│   │   └── index.js
│   └── package.json
└── README.md
```

## Development

### Adding New Regulatory Documents
1. Place your regulatory documents in the appropriate format in the backend storage
2. Update the document indexing system as needed
3. Ensure proper tagging and metadata for efficient retrieval

### Testing
- Backend tests can be run using pytest
- Frontend tests can be run using `npm test`

## Security Considerations
- All sensitive data should be properly encrypted
- API keys should be stored securely in environment variables
- Regular security audits should be performed

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Cleaning Up

To remove all generated files and virtual environments:
```bash
make clean
```

## License
[Your chosen license]
