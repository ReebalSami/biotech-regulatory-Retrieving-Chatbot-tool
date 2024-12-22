import React, { useState } from 'react';
import { Box, Container, Tab, Tabs, ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import Chatbot from './components/Chatbot';
import Questionnaire from './components/Questionnaire';
import RegulatoryDisplay from './components/RegulatoryDisplay';

// Create theme
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

function TabPanel(props) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
      style={{ height: '100%' }}
    >
      {value === index && (
        <Box sx={{ height: '100%' }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function App() {
  const [tabValue, setTabValue] = useState(0);
  const [messages, setMessages] = useState([]);
  const [questionnaireData, setQuestionnaireData] = useState(null);
  const [guidelines, setGuidelines] = useState([]);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleQuestionnaireSubmit = async (formData) => {
    try {
      const response = await fetch('http://localhost:8000/questionnaire', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch guidelines');
      }

      const data = await response.json();
      setGuidelines(data.guidelines || []);
      setQuestionnaireData(formData);
      setTabValue(1); // Switch to the Regulatory Guidelines tab
    } catch (error) {
      console.error('Error fetching guidelines:', error);
      // You might want to show an error message to the user here
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container maxWidth="xl" sx={{ height: '100vh', py: 2 }}>
        <Box sx={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={tabValue} onChange={handleTabChange} aria-label="app navigation">
              <Tab label="Product Classification" />
              <Tab label="Regulatory Guidelines" />
              <Tab label="Chat Assistant" />
            </Tabs>
          </Box>

          <Box sx={{ flex: 1, mt: 2, overflow: 'hidden' }}>
            <TabPanel value={tabValue} index={0}>
              <Questionnaire onSubmit={handleQuestionnaireSubmit} />
            </TabPanel>
            <TabPanel value={tabValue} index={1}>
              <RegulatoryDisplay guidelines={guidelines} />
            </TabPanel>
            <TabPanel value={tabValue} index={2}>
              <Chatbot
                messages={messages}
                setMessages={setMessages}
                questionnaireData={questionnaireData}
                guidelines={guidelines}
              />
            </TabPanel>
          </Box>
        </Box>
      </Container>
    </ThemeProvider>
  );
}

export default App;
