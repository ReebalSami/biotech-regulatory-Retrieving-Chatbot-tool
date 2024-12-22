# Biotech Regulatory Tool

A comprehensive tool for biotech companies to navigate regulatory requirements and compliance guidelines.

## Features

- Interactive Questionnaire for regulatory assessment
- AI-powered Chatbot for regulatory guidance
- Regulatory Document Management
- Smart Search functionality
- GPT-4 Integration for intelligent responses
- Customized compliance recommendations

## Prerequisites

- Python 3.8+
- Node.js 16+
- OpenAI API Key

## Quick Start

1. Clone the repository:
```bash
git clone [repository-url]
cd biotech_regulatory_tool
```

2. Set up the backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

4. Set up the frontend:
```bash
cd ../frontend
npm install
```

5. Start the development servers:
```bash
# In backend directory
uvicorn app.main:app --reload

# In frontend directory
npm start
```

## Project Structure

```
biotech_regulatory_tool/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/
│   │   ├── services/
│   │   └── models/
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   └── App.js
│   └── package.json
└── README.md
```

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed development guidelines.

## Latest Updates

- Enhanced chatbot UI with iMessage-style interface
- Improved error handling for API interactions
- Updated styling and user experience
- Integrated GPT-4 for more accurate responses
- Added comprehensive documentation

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
