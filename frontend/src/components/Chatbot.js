import React, { useState, useRef, useEffect } from 'react';
import {
  Paper,
  Typography,
  TextField,
  Button,
  Box,
  List,
  ListItem,
  ListItemText,
  Chip,
  Divider,
  CircularProgress,
  Alert,
  Snackbar,
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import SaveIcon from '@mui/icons-material/Save';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

const Chatbot = ({ questionnaireData, messages, setMessages, documents }) => {
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  // Fetch documents
  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        const response = await fetch('http://localhost:8000/user-documents');
        if (response.ok) {
          const data = await response.json();
          // setDocuments(data);
        }
      } catch (error) {
        console.error('Error fetching documents:', error);
      }
    };

    fetchDocuments();
    // Poll for document updates every 5 seconds
    const interval = setInterval(fetchDocuments, 5000);
    return () => clearInterval(interval);
  }, []);

  // Effect for questionnaire data and document updates
  useEffect(() => {
    if (!messages.length && (!questionnaireData || Object.keys(questionnaireData).length === 0)) {
      // Show welcome message only on first load when no questionnaire data
      setMessages([
        {
          type: 'system',
          content: 'Welcome! I can help you understand regulatory requirements for your biotech product. You can:\n\n' +
                  '1. Fill out the questionnaire to get personalized guidance\n' +
                  '2. Upload relevant documents for more specific answers (optional)\n' +
                  '3. Ask questions about regulations and compliance\n\n' +
                  'How can I assist you today?',
          timestamp: new Date().toISOString()
        }
      ]);
      return;
    }

    if (questionnaireData && Object.keys(questionnaireData).length > 0) {
      const currentQuestionnaireStr = JSON.stringify(questionnaireData);
      const prevQuestionnaire = messages.find(message => message.type === 'system' && message.content.includes('Thank you for providing your information.'));

      if (!prevQuestionnaire) {
        // Clear previous messages when questionnaire is updated
        setMessages([{
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
    }
  }, [questionnaireData, documents, messages]);

  // Auto-scroll effect
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleSend = async () => {
    if (!newMessage.trim()) return;

    const userMessage = {
      type: 'user',
      content: newMessage,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setNewMessage('');
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: newMessage,
          questionnaire_data: questionnaireData,
          has_uploaded_documents: documents.length > 0
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response');
      }

      const data = await response.json();
      
      // Format sources if they exist
      const formattedSources = data.sources?.map(source => {
        if (typeof source === 'string') {
          return { content: source };
        }
        return source;
      }) || [];

      const botMessage = {
        type: 'bot',
        content: data.response,
        timestamp: new Date().toISOString(),
        sources: formattedSources,
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      setError('Failed to get response from the chatbot');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveChat = async () => {
    try {
      setIsLoading(true);
      
      // Create a temporary div for PDF content
      const pdfContent = document.createElement('div');
      pdfContent.style.padding = '20px';
      pdfContent.style.fontFamily = 'Arial';
      
      // Add title and date
      const header = document.createElement('div');
      header.innerHTML = `
        <h1 style="color: #1976d2; margin-bottom: 10px;">Regulatory Compliance Chat Report</h1>
        <p style="color: #666; margin-bottom: 20px;">Generated on ${new Date().toLocaleString()}</p>
      `;
      pdfContent.appendChild(header);

      // Add questionnaire data if available
      if (questionnaireData && Object.keys(questionnaireData).length > 0) {
        const questionnaireSection = document.createElement('div');
        questionnaireSection.innerHTML = `
          <h2 style="color: #1976d2; margin-top: 20px;">Product Information</h2>
          <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
            <p><strong>Product Purpose:</strong> ${questionnaireData.intended_purpose || 'Not specified'}</p>
            <p><strong>Life-threatening Use:</strong> ${questionnaireData.life_threatening ? 'Yes' : 'No'}</p>
            <p><strong>User Type:</strong> ${questionnaireData.user_type || 'Not specified'}</p>
            <p><strong>Requires Sterilization:</strong> ${questionnaireData.requires_sterilization ? 'Yes' : 'No'}</p>
            <p><strong>Body Contact Duration:</strong> ${questionnaireData.body_contact_duration || 'Not specified'}</p>
          </div>
        `;
        pdfContent.appendChild(questionnaireSection);
      }

      // Add chat messages
      const chatSection = document.createElement('div');
      chatSection.innerHTML = '<h2 style="color: #1976d2; margin-top: 20px;">Conversation History</h2>';
      
      messages.forEach((message, index) => {
        const messageDiv = document.createElement('div');
        messageDiv.style.marginBottom = '15px';
        
        // Message header with type and timestamp
        const messageType = message.type.charAt(0).toUpperCase() + message.type.slice(1);
        messageDiv.innerHTML = `
          <div style="margin-bottom: 5px; color: #666;">
            <strong>${messageType}</strong> - ${new Date(message.timestamp).toLocaleString()}
          </div>
        `;

        // Message content
        const contentDiv = document.createElement('div');
        contentDiv.style.padding = '10px';
        contentDiv.style.borderRadius = '5px';
        contentDiv.style.backgroundColor = 
          message.type === 'user' ? '#e3f2fd' :
          message.type === 'system' ? '#fff3e0' :
          message.type === 'error' ? '#ffebee' : '#ffffff';
        contentDiv.innerHTML = `<p style="margin: 0;">${message.content}</p>`;
        messageDiv.appendChild(contentDiv);

        // Add sources if available
        if (message.sources && message.sources.length > 0) {
          const sourcesDiv = document.createElement('div');
          sourcesDiv.style.marginTop = '10px';
          sourcesDiv.style.paddingLeft = '15px';
          sourcesDiv.innerHTML = '<p style="color: #666; margin-bottom: 5px;"><strong>Sources:</strong></p>';
          
          message.sources.forEach(source => {
            sourcesDiv.innerHTML += `
              <div style="background-color: #ffffff; padding: 10px; border: 1px solid #e0e0e0; border-radius: 5px; margin-bottom: 5px;">
                <p style="margin: 0; font-weight: bold;">${source.title || 'Untitled Document'}</p>
                <p style="margin: 5px 0; font-style: italic;">${source.content}</p>
                ${source.jurisdiction ? `<span style="background-color: #e3f2fd; padding: 3px 8px; border-radius: 12px; font-size: 0.8em;">${source.jurisdiction}</span>` : ''}
              </div>
            `;
          });
          messageDiv.appendChild(sourcesDiv);
        }

        chatSection.appendChild(messageDiv);
      });
      
      pdfContent.appendChild(chatSection);
      document.body.appendChild(pdfContent);

      // Convert to PDF
      const pdf = new jsPDF('p', 'pt', 'a4');
      const scale = 2; // Increase quality
      
      // Function to add pages
      const addPage = async (element, pdf) => {
        const canvas = await html2canvas(element, {
          scale: scale,
          useCORS: true,
          logging: false
        });
        
        const imgData = canvas.toDataURL('image/jpeg', 1.0);
        const pdfWidth = pdf.internal.pageSize.getWidth();
        const pdfHeight = pdf.internal.pageSize.getHeight();
        const imgWidth = canvas.width / scale;
        const imgHeight = canvas.height / scale;
        
        let heightLeft = imgHeight;
        let position = 0;
        let page = 1;

        pdf.addImage(imgData, 'JPEG', 0, position, pdfWidth, (imgHeight * pdfWidth) / imgWidth);
        heightLeft -= pdfHeight;

        while (heightLeft >= 0) {
          position = -pdfHeight * page;
          pdf.addPage();
          pdf.addImage(imgData, 'JPEG', 0, position, pdfWidth, (imgHeight * pdfWidth) / imgWidth);
          heightLeft -= pdfHeight;
          page++;
        }
      };

      await addPage(pdfContent, pdf);
      
      // Save the PDF
      pdf.save(`regulatory-chat-report-${new Date().toISOString().split('T')[0]}.pdf`);
      
      // Clean up
      document.body.removeChild(pdfContent);
      setIsLoading(false);
    } catch (error) {
      console.error('Error generating PDF:', error);
      setError('Failed to generate PDF report');
      setIsLoading(false);
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  return (
    <Paper elevation={3} sx={{ p: 3, height: '80vh', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ 
        flex: 1, 
        overflowY: 'auto', 
        mb: 2,
        display: 'flex',
        flexDirection: 'column',
        gap: 2
      }}>
        {messages.map((message, index) => (
          <Box
            key={index}
            sx={{
              display: 'flex',
              justifyContent: message.type === 'user' ? 'flex-end' : 'flex-start',
              mb: 1
            }}
          >
            <Paper
              elevation={1}
              sx={{
                p: 2,
                maxWidth: '80%',
                backgroundColor: message.type === 'user' 
                  ? 'primary.main'
                  : message.type === 'system' || message.type === 'bot'
                    ? 'grey.100'
                    : 'secondary.light',
                color: message.type === 'user' ? 'white' : 'text.primary',
                borderRadius: 2,
                ...(message.type === 'user' 
                  ? { 
                      borderTopRightRadius: 0,
                      ml: 'auto'
                    }
                  : {
                      borderTopLeftRadius: 0,
                      mr: 'auto'
                    })
              }}
            >
              <Typography
                component="div"
                sx={{
                  whiteSpace: 'pre-wrap',
                  '& ul, & ol': {
                    pl: 2,
                    mb: 0
                  }
                }}
              >
                {message.content}
              </Typography>
              {message.sources && (
                <Box sx={{ mt: 1, pt: 1, borderTop: 1, borderColor: 'divider' }}>
                  <Typography variant="caption" color="text.secondary">
                    Sources:
                  </Typography>
                  <Box sx={{ mt: 0.5 }}>
                    {message.sources.map((source, idx) => (
                      <Box 
                        key={idx} 
                        sx={{ 
                          mb: 1,
                          p: 1,
                          backgroundColor: 'rgba(0, 0, 0, 0.03)',
                          borderRadius: 1,
                          '&:last-child': { mb: 0 }
                        }}
                      >
                        {source.title && (
                          <Typography variant="caption" sx={{ fontWeight: 'bold', display: 'block' }}>
                            {source.title}
                          </Typography>
                        )}
                        {source.content && (
                          <Typography variant="caption" sx={{ display: 'block', mt: 0.5 }}>
                            {source.content}
                          </Typography>
                        )}
                        {source.jurisdiction && (
                          <Chip
                            label={source.jurisdiction}
                            size="small"
                            sx={{ mt: 0.5 }}
                            variant="outlined"
                          />
                        )}
                      </Box>
                    ))}
                  </Box>
                </Box>
              )}
              <Typography 
                variant="caption" 
                sx={{ 
                  display: 'block',
                  mt: 0.5,
                  color: message.type === 'user' ? 'rgba(255,255,255,0.7)' : 'text.secondary'
                }}
              >
                {new Date(message.timestamp).toLocaleTimeString()}
              </Typography>
            </Paper>
          </Box>
        ))}
        {isLoading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}>
            <CircularProgress size={24} />
          </Box>
        )}
        <div ref={messagesEndRef} />
      </Box>

      <Box sx={{ 
        display: 'flex', 
        gap: 1,
        mt: 'auto',
        borderTop: 1,
        borderColor: 'divider',
        pt: 2
      }}>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Type your message..."
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
          multiline
          maxRows={4}
          size="small"
        />
        <Button
          variant="contained"
          color="primary"
          onClick={handleSend}
          disabled={isLoading || !newMessage.trim()}
          sx={{ minWidth: 100 }}
        >
          Send
        </Button>
      </Box>

      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      </Snackbar>
    </Paper>
  );
};

export default Chatbot;
