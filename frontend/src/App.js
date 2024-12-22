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

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container maxWidth="xl" sx={{ height: '100vh', py: 2 }}>
        <Box sx={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={tabValue} onChange={handleTabChange} aria-label="app navigation">
              <Tab label="Chat Assistant" />
              <Tab label="Product Classification" />
              <Tab label="Regulatory Guidelines" />
            </Tabs>
          </Box>

          <Box sx={{ flex: 1, mt: 2, overflow: 'hidden' }}>
            <TabPanel value={tabValue} index={0}>
              <Chatbot
                messages={messages}
                setMessages={setMessages}
                questionnaireData={questionnaireData}
              />
            </TabPanel>
            <TabPanel value={tabValue} index={1}>
              <Questionnaire
                onSubmit={setQuestionnaireData}
                setActiveTab={setTabValue}
              />
            </TabPanel>
            <TabPanel value={tabValue} index={2}>
              <RegulatoryDisplay />
            </TabPanel>
          </Box>
        </Box>
      </Container>
    </ThemeProvider>
  );
}

export default App;
