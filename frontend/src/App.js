import React, { useState } from 'react';
import { Box, Container, Tab, Tabs, ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import Questionnaire from './components/Questionnaire';
import RegulatoryDisplay from './components/RegulatoryDisplay';
import Chatbot from './components/Chatbot';

// Create theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#007AFF',
      light: '#5856D6',
      dark: '#0055FF',
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: '#5856D6',
      light: '#34C759',
      dark: '#248A3D',
    },
    background: {
      default: '#F2F2F7',
      paper: '#FFFFFF',
    },
    text: {
      primary: '#1C1C1E',
      secondary: '#6C6C70',
    },
    divider: '#E5E5EA',
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
    subtitle1: {
      letterSpacing: 0,
    },
    subtitle2: {
      letterSpacing: 0,
    },
    body1: {
      letterSpacing: 0,
    },
    body2: {
      letterSpacing: 0,
    },
    button: {
      letterSpacing: 0,
      textTransform: 'none',
      fontWeight: 600,
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '8px 16px',
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            transform: 'translateY(-1px)',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
          },
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
          fontSize: '0.9375rem',
          minWidth: 120,
          padding: '12px 16px',
          transition: 'all 0.2s ease-in-out',
          '&.Mui-selected': {
            color: '#007AFF',
          },
          '&:hover': {
            backgroundColor: 'rgba(0, 122, 255, 0.04)',
          },
        },
      },
    },
    MuiTabs: {
      styleOverrides: {
        indicator: {
          height: 3,
          borderRadius: '3px 3px 0 0',
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
        <Box sx={{ height: '100%', pt: 2 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function App() {
  const [value, setValue] = useState(0);
  const [guidelines, setGuidelines] = useState([]);

  const handleChange = (event, newValue) => {
    setValue(newValue);
  };

  const handleQuestionnaireSubmit = (guidelines) => {
    setGuidelines(guidelines);
    setValue(1); // Switch to RegulatoryDisplay tab
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ 
        minHeight: '100vh',
        backgroundColor: 'background.default',
        pt: 3,
        pb: 3
      }}>
        <Container maxWidth="lg" sx={{ height: '100%' }}>
          <Box sx={{ 
            bgcolor: 'background.paper',
            borderRadius: 4,
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
            overflow: 'hidden',
            height: 'calc(100vh - 48px)'
          }}>
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
              <Tabs 
                value={value} 
                onChange={handleChange} 
                aria-label="app tabs"
                variant="fullWidth"
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
                  label="AI Assistant" 
                  id="tab-2" 
                  aria-controls="tabpanel-2"
                />
              </Tabs>
            </Box>
            <TabPanel value={value} index={0}>
              <Questionnaire onSubmit={handleQuestionnaireSubmit} />
            </TabPanel>
            <TabPanel value={value} index={1}>
              <RegulatoryDisplay guidelines={guidelines} />
            </TabPanel>
            <TabPanel value={value} index={2}>
              <Chatbot />
            </TabPanel>
          </Box>
        </Container>
      </Box>
    </ThemeProvider>
  );
}

export default App;
