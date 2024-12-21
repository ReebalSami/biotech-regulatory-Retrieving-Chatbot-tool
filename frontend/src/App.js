import React, { useState, useEffect } from 'react';
import { 
  Container, 
  CssBaseline, 
  ThemeProvider, 
  createTheme,
  Box,
  Tabs,
  Tab
} from '@mui/material';
import Questionnaire from './components/Questionnaire';
import RegulatoryDisplay from './components/RegulatoryDisplay';
import Chatbot from './components/Chatbot';
import DocumentManager from './components/DocumentManager';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  const [currentTab, setCurrentTab] = useState(0);
  const [questionnaireData, setQuestionnaireData] = useState(null);
  const [guidelines, setGuidelines] = useState([]);
  const [chatMessages, setChatMessages] = useState([]);
  const [documents, setDocuments] = useState([]);

  // Fetch documents
  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        const response = await fetch('http://localhost:8000/user-documents', {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
          },
        });
        if (response.ok) {
          const data = await response.json();
          setDocuments(data);
        } else {
          console.error('Error fetching documents:', response.statusText);
        }
      } catch (error) {
        console.error('Error fetching documents:', error);
      }
    };

    fetchDocuments();
  }, []);

  // Update chat messages when questionnaire is submitted
  useEffect(() => {
    if (questionnaireData && Object.keys(questionnaireData).length > 0) {
      // Only update if we don't already have a questionnaire summary message
      const hasSummary = chatMessages.some(msg => 
        msg.type === 'system' && 
        msg.content.includes('Thank you for providing your information')
      );

      if (!hasSummary) {
        setChatMessages([{
          type: 'system',
          content: `Thank you for providing your information. I understand that:\n\n` +
                  `• Your product purpose: ${questionnaireData.intended_purpose}\n` +
                  `• Life-threatening use: ${questionnaireData.life_threatening ? 'Yes' : 'No'}\n` +
                  `• Intended users: ${questionnaireData.user_type}\n` +
                  `• Requires sterilization: ${questionnaireData.requires_sterilization ? 'Yes' : 'No'}\n` +
                  `• Body contact duration: ${questionnaireData.body_contact_duration}\n\n` +
                  `${documents.length > 0 
                    ? `I will also consider your ${documents.length} uploaded document(s) when providing answers.` 
                    : 'You can upload relevant documents to get more specific answers (optional).'}\n\n` +
                  `What would you like to know about the regulatory requirements for your product?`,
          timestamp: new Date().toISOString(),
        }]);
      }
    } else if (chatMessages.length === 0) {
      setChatMessages([{
        type: 'system',
        content: 'Welcome! I can help you understand regulatory requirements for your biotech product. You can:\n\n' +
                '1. Fill out the questionnaire to get personalized guidance\n' +
                '2. Upload relevant documents for more specific answers (optional)\n' +
                '3. Ask questions about regulations and compliance\n\n' +
                'How can I assist you today?',
        timestamp: new Date().toISOString()
      }]);
    }
  }, [questionnaireData, documents, chatMessages]);

  const handleTabChange = (event, newValue) => {
    setCurrentTab(newValue);
  };

  const handleQuestionnaireSubmit = async (data) => {
    setQuestionnaireData(data);
    setCurrentTab(3); // Switch to chat tab
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container maxWidth="lg">
        <Box sx={{ width: '100%', mt: 4 }}>
          <Tabs
            value={currentTab}
            onChange={handleTabChange}
            centered
            TabIndicatorProps={{
              'aria-hidden': 'false'
            }}
            sx={{
              '& .MuiTabs-flexContainer': {
                outline: 'none'
              }
            }}
          >
            <Tab 
              label="Questionnaire" 
              id="tab-0"
              aria-controls="tabpanel-0"
            />
            <Tab 
              label="Regulatory Guidelines" 
              id="tab-1"
              aria-controls="tabpanel-1"
            />
            <Tab 
              label="Documents" 
              id="tab-2"
              aria-controls="tabpanel-2"
            />
            <Tab 
              label="Chat Assistant" 
              id="tab-3"
              aria-controls="tabpanel-3"
            />
          </Tabs>

          <Box 
            sx={{ mt: 3 }}
            role="tabpanel"
            id={`tabpanel-${currentTab}`}
            aria-labelledby={`tab-${currentTab}`}
          >
            {currentTab === 0 && (
              <Questionnaire onSubmit={handleQuestionnaireSubmit} />
            )}
            {currentTab === 1 && (
              <RegulatoryDisplay guidelines={guidelines} />
            )}
            {currentTab === 2 && (
              <DocumentManager />
            )}
            {currentTab === 3 && (
              <Chatbot 
                questionnaireData={questionnaireData}
                messages={chatMessages}
                setMessages={setChatMessages}
                documents={documents}
              />
            )}
          </Box>
        </Box>
      </Container>
    </ThemeProvider>
  );
}

export default App;
