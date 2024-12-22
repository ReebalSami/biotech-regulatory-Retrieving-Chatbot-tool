import React, { useState } from 'react';
import { Box, Container, Tab, Tabs, ThemeProvider, createTheme, CssBaseline, alpha } from '@mui/material';
import Chatbot from './components/Chatbot';
import Questionnaire from './components/Questionnaire';
import RegulatoryDisplay from './components/RegulatoryDisplay';

// Create theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#007AFF',
      light: '#5856D6',
      dark: '#0055FF',
    },
    secondary: {
      main: '#5856D6',
    },
    background: {
      default: '#F2F2F7',
      paper: '#FFFFFF',
    },
    text: {
      primary: '#1C1C1E',
      secondary: '#6C6C70',
    },
  },
  shape: {
    borderRadius: 12,
  },
  typography: {
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
    h1: {
      fontWeight: 700,
      letterSpacing: '-0.025em',
    },
    h2: {
      fontWeight: 700,
      letterSpacing: '-0.025em',
    },
    h3: {
      fontWeight: 600,
      letterSpacing: '-0.025em',
    },
    h4: {
      fontWeight: 600,
      letterSpacing: '-0.025em',
    },
    h5: {
      fontWeight: 600,
      letterSpacing: '-0.025em',
    },
    h6: {
      fontWeight: 600,
      letterSpacing: '-0.025em',
    },
    body1: {
      letterSpacing: '-0.015em',
    },
    body2: {
      letterSpacing: '-0.015em',
    },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          background: 'linear-gradient(135deg, #F2F2F7 0%, #E5E5EA 100%)',
          minHeight: '100vh',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          boxShadow: '0 2px 20px rgba(0,0,0,0.05)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
          padding: '8px 16px',
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            transform: 'translateY(-1px)',
          },
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
          fontSize: '1rem',
          minWidth: 100,
          transition: 'all 0.2s ease-in-out',
          '&.Mui-selected': {
            color: '#007AFF',
          },
        },
      },
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
      setQuestionnaireData(formData);
      setGuidelines(data.guidelines);
      setTabValue(1); // Switch to guidelines tab
    } catch (error) {
      console.error('Error fetching guidelines:', error);
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box
        sx={{
          minHeight: '100vh',
          backgroundColor: 'background.default',
          pt: 4,
          pb: 8,
        }}
      >
        <Container maxWidth="lg">
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              gap: 3,
              height: 'calc(100vh - 100px)',
            }}
          >
            <Box sx={{ borderBottom: 0 }}>
              <Tabs
                value={tabValue}
                onChange={handleTabChange}
                centered
                sx={{
                  '& .MuiTabs-flexContainer': {
                    gap: 2,
                  },
                }}
              >
                <Tab label="Questionnaire" />
                <Tab label="Guidelines" />
                <Tab label="Chat Assistant" />
              </Tabs>
            </Box>

            <TabPanel value={tabValue} index={0}>
              <Questionnaire onSubmit={handleQuestionnaireSubmit} />
            </TabPanel>
            <TabPanel value={tabValue} index={1}>
              <RegulatoryDisplay guidelines={guidelines} questionnaireData={questionnaireData} />
            </TabPanel>
            <TabPanel value={tabValue} index={2}>
              <Chatbot messages={messages} setMessages={setMessages} />
            </TabPanel>
          </Box>
        </Container>
      </Box>
    </ThemeProvider>
  );
}

export default App;
