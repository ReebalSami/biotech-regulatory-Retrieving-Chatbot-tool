import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Divider,
  Alert,
  Snackbar,
  Chip,
  CircularProgress
} from '@mui/material';
import {
  Send as SendIcon,
  AttachFile as AttachFileIcon,
  Close as CloseIcon
} from '@mui/icons-material';

const Chatbot = ({ questionnaireData }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [chatId] = useState(() => crypto.randomUUID());
  const [attachments, setAttachments] = useState([]);
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);

  // Initialize chat with welcome message
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([{
        role: 'system',
        content: 'Welcome! I can help you understand regulatory requirements for your biotech product. You can:\n\n' +
                '1. Fill out the questionnaire to get personalized guidance\n' +
                '2. Upload relevant documents for more specific answers (optional)\n' +
                '3. Ask questions about regulations and compliance\n\n' +
                'How can I assist you today?',
        timestamp: new Date()
      }]);
    }
  }, [messages.length]);

  // Add questionnaire data to chat when available
  useEffect(() => {
    if (questionnaireData && Object.keys(questionnaireData).length > 0) {
      const hasSummary = messages.some(msg => 
        msg.role === 'system' && 
        msg.content.includes('Thank you for providing your information')
      );

      if (!hasSummary) {
        setMessages(prev => [...prev, {
          role: 'system',
          content: `Thank you for providing your information. I understand that:\n\n` +
                  `• Your product purpose: ${questionnaireData.intended_purpose}\n` +
                  `• Life-threatening use: ${questionnaireData.life_threatening ? 'Yes' : 'No'}\n` +
                  `• Intended users: ${questionnaireData.user_type}\n` +
                  `• Requires sterilization: ${questionnaireData.requires_sterilization ? 'Yes' : 'No'}\n` +
                  `• Body contact duration: ${questionnaireData.body_contact_duration}\n\n` +
                  `What would you like to know about the regulatory requirements for your product?`,
          timestamp: new Date()
        }]);
      }
    }
  }, [questionnaireData, messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleAttachFile = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Check file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      setError('File size must be less than 10MB');
      return;
    }

    // Check file type
    const allowedTypes = ['.pdf', '.doc', '.docx', '.txt'];
    const fileExtension = file.name.toLowerCase().slice(file.name.lastIndexOf('.'));
    if (!allowedTypes.includes(fileExtension)) {
      setError('Only PDF, Word, and text files are allowed');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('chat_id', chatId);

      const response = await fetch('http://localhost:8000/chat/attachments/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to upload file');
      }

      const data = await response.json();
      setAttachments(prev => [...prev, {
        id: data.document_id,
        filename: data.filename,
        uploadDate: new Date(data.upload_date)
      }]);

      // Add system message about attachment
      setMessages(prev => [...prev, {
        role: 'system',
        content: `File "${file.name}" attached successfully. I'll consider this document in our conversation.`,
        timestamp: new Date()
      }]);
    } catch (error) {
      setError('Failed to upload file: ' + error.message);
    }
  };

  const handleRemoveAttachment = async (attachmentId) => {
    try {
      const response = await fetch(`http://localhost:8000/chat/attachments/${attachmentId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to remove attachment');
      }

      setAttachments(prev => prev.filter(att => att.id !== attachmentId));
      
      // Add system message about removal
      setMessages(prev => [...prev, {
        role: 'system',
        content: 'Attachment removed from the conversation.',
        timestamp: new Date()
      }]);
    } catch (error) {
      setError('Failed to remove attachment: ' + error.message);
    }
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = {
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: input,
          chat_id: chatId,
          context_size: 3
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response');
      }

      const data = await response.json();
      
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.response,
        sources: data.sources,
        timestamp: new Date()
      }]);
    } catch (error) {
      setError('Failed to get response: ' + error.message);
      setMessages(prev => [...prev, {
        role: 'system',
        content: 'Sorry, I encountered an error while processing your request. Please try again.',
        timestamp: new Date()
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Paper elevation={3} sx={{ flex: 1, p: 2, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        {/* Messages Area */}
        <Box sx={{ flex: 1, overflow: 'auto', mb: 2 }}>
          <List>
            {messages.map((message, index) => (
              <React.Fragment key={index}>
                <ListItem alignItems="flex-start" sx={{
                  flexDirection: 'column',
                  backgroundColor: message.role === 'user' ? 'primary.light' : 'background.paper',
                  borderRadius: 1,
                  mb: 1
                }}>
                  <ListItemText
                    primary={
                      <Typography variant="subtitle2" sx={{ color: message.role === 'user' ? 'common.white' : 'text.primary' }}>
                        {message.role === 'user' ? 'You' : message.role === 'system' ? 'System' : 'Assistant'}
                        {message.timestamp && (
                          <Typography component="span" variant="caption" sx={{ ml: 1, opacity: 0.7 }}>
                            {message.timestamp.toLocaleTimeString()}
                          </Typography>
                        )}
                      </Typography>
                    }
                    secondary={
                      <Typography
                        component="div"
                        variant="body2"
                        sx={{ 
                          mt: 1,
                          color: message.role === 'user' ? 'common.white' : 'text.primary',
                          whiteSpace: 'pre-wrap'
                        }}
                      >
                        {message.content}
                      </Typography>
                    }
                  />
                  {message.sources && message.sources.length > 0 && (
                    <Box sx={{ mt: 1, width: '100%' }}>
                      <Typography variant="caption" color="text.secondary">
                        Sources:
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                        {message.sources.map((source, idx) => (
                          <Chip
                            key={idx}
                            label={source.title}
                            size="small"
                            variant="outlined"
                            sx={{ 
                              backgroundColor: 'background.paper',
                              '& .MuiChip-label': {
                                color: 'text.primary'
                              }
                            }}
                          />
                        ))}
                      </Box>
                    </Box>
                  )}
                </ListItem>
                {index < messages.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
          <div ref={messagesEndRef} />
        </Box>

        {/* Attachments Area */}
        {attachments.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Attached Documents:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 0.5 }}>
              {attachments.map((attachment) => (
                <Chip
                  key={attachment.id}
                  label={attachment.filename}
                  onDelete={() => handleRemoveAttachment(attachment.id)}
                  size="small"
                  variant="outlined"
                />
              ))}
            </Box>
          </Box>
        )}

        {/* Input Area */}
        <Box sx={{ display: 'flex', gap: 1 }}>
          <input
            type="file"
            ref={fileInputRef}
            style={{ display: 'none' }}
            onChange={handleAttachFile}
            accept=".pdf,.doc,.docx,.txt"
          />
          <IconButton
            onClick={() => fileInputRef.current?.click()}
            disabled={loading}
            size="small"
          >
            <AttachFileIcon />
          </IconButton>
          <TextField
            fullWidth
            multiline
            maxRows={4}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            disabled={loading}
            size="small"
          />
          <IconButton
            onClick={handleSend}
            disabled={loading || !input.trim()}
            color="primary"
            size="small"
          >
            {loading ? <CircularProgress size={24} /> : <SendIcon />}
          </IconButton>
        </Box>
      </Paper>

      {/* Error Snackbar */}
      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          severity="error"
          action={
            <IconButton
              size="small"
              aria-label="close"
              color="inherit"
              onClick={() => setError(null)}
            >
              <CloseIcon fontSize="small" />
            </IconButton>
          }
        >
          {error}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Chatbot;
