import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  Avatar,
  Fade,
  useTheme,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  Button,
  Chip,
} from '@mui/material';
import SendRoundedIcon from '@mui/icons-material/SendRounded';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import { styled } from '@mui/material/styles';

// Styled components
const shouldForwardProp = prop => prop !== 'isUser';

const MessageContainer = styled('div', { shouldForwardProp })(({ theme, isUser }) => ({
  display: 'flex',
  alignItems: 'flex-start',
  marginBottom: theme.spacing(2),
  justifyContent: isUser ? 'flex-end' : 'flex-start',
  width: '100%',
}));

const MessageBubble = styled(Paper, { shouldForwardProp })(({ theme, isUser }) => ({
  padding: theme.spacing(1.5, 2),
  borderRadius: theme.shape.borderRadius * 2,
  maxWidth: '70%',
  minWidth: '200px',
  backgroundColor: isUser ? theme.palette.primary.main : theme.palette.grey[50],
  color: isUser ? theme.palette.primary.contrastText : theme.palette.text.primary,
  boxShadow: 'none',
}));

const MessageGroup = styled('div', { shouldForwardProp })(({ theme, isUser }) => ({
  display: 'flex',
  alignItems: 'flex-end',
  gap: theme.spacing(1),
  flexDirection: 'row',
  width: '100%',
  justifyContent: isUser ? 'flex-end' : 'flex-start',
}));

const MessageContent = styled('div', { shouldForwardProp })(({ theme, isUser }) => ({
  display: 'flex',
  flexDirection: 'column',
  alignItems: isUser ? 'flex-end' : 'flex-start',
  flex: '0 1 auto',
  maxWidth: '70%',
}));

const StyledTextField = styled(TextField)(({ theme }) => ({
  '& .MuiOutlinedInput-root': {
    borderRadius: 30,
    backgroundColor: theme.palette.background.paper,
    '&.Mui-focused': {
      boxShadow: `0 0 0 2px ${theme.palette.primary.main}`,
    },
    '& fieldset': {
      borderColor: 'transparent',
      transition: theme.transitions.create(['border-color', 'box-shadow']),
    },
    '&:hover fieldset': {
      borderColor: theme.palette.primary.main,
    },
  },
}));

const SendButton = styled(IconButton)(({ theme }) => ({
  backgroundColor: theme.palette.primary.main,
  color: theme.palette.primary.contrastText,
  '&:hover': {
    backgroundColor: theme.palette.primary.dark,
    transform: 'scale(1.05)',
  },
  transition: theme.transitions.create(['background-color', 'transform'], {
    duration: theme.transitions.duration.shorter,
  }),
  width: 40,
  height: 40,
}));

const AssistantAvatar = styled(Avatar)(({ theme }) => ({
  backgroundColor: theme.palette.secondary.main,
  width: 32,
  height: 32,
  fontSize: '0.875rem',
}));

const UserAvatar = styled(Avatar)(({ theme }) => ({
  backgroundColor: theme.palette.primary.main,
  width: 32,
  height: 32,
  fontSize: '0.875rem',
}));

const ChatContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  flexDirection: 'column',
  height: '100%',
  backgroundColor: theme.palette.background.default,
  borderRadius: theme.shape.borderRadius,
  overflow: 'hidden',
}));

const MessageList = styled(Box)(({ theme }) => ({
  flexGrow: 1,
  overflowY: 'auto',
  padding: theme.spacing(2),
  display: 'flex',
  flexDirection: 'column',
  gap: theme.spacing(2),
}));

const InputContainer = styled(Box)(({ theme }) => ({
  padding: theme.spacing(2),
  borderTop: `1px solid ${theme.palette.divider}`,
  backgroundColor: theme.palette.background.paper,
}));

const TypingIndicator = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(1),
  padding: theme.spacing(1, 2),
  borderRadius: 20,
  backgroundColor: theme.palette.background.paper,
  width: 'fit-content',
  marginBottom: theme.spacing(2),
}));

function Chatbot() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [files, setFiles] = useState([]);
  const [attachmentIds, setAttachmentIds] = useState([]);
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);
  const theme = useTheme();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleFileUpload = async (event) => {
    const newFiles = Array.from(event.target.files);
    setFiles(prevFiles => [...prevFiles, ...newFiles]);
    
    const formData = new FormData();
    for (const file of newFiles) {
      formData.append('files', file);
    }
    
    try {
      const response = await fetch('http://localhost:8000/api/chat/upload', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error('Failed to upload files');
      }
      
      const newIds = await response.json();
      setAttachmentIds(prev => [...prev, ...newIds]);
    } catch (error) {
      console.error('Error uploading files:', error);
    }
  };

  const handleRemoveFile = (index) => {
    setFiles(files.filter((_, i) => i !== index));
    setAttachmentIds(attachmentIds.filter((_, i) => i !== index));
  };

  const handleSend = async () => {
    if (!input.trim() && files.length === 0) return;

    // Wait for all files to be uploaded before sending the message
    if (files.length > attachmentIds.length) {
      console.log('Waiting for files to finish uploading...');
      return;
    }

    const userMessage = {
      text: input.trim() || "Please analyze the attached document.",
      isUser: true,
      timestamp: new Date(),
      attachments: files.map(f => f.name),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    try {
      const response = await fetch('http://localhost:8000/api/chat/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage.text,
          context: [],
          attachment_ids: attachmentIds,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to get response from AI');
      }

      const data = await response.json();
      
      const assistantMessage = {
        text: data.response,
        isUser: false,
        timestamp: new Date(),
        processedAttachments: data.processed_attachments,
      };

      setMessages(prev => [...prev, assistantMessage]);
      
      // Clear files and attachment IDs after successful message
      setFiles([]);
      setAttachmentIds([]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        text: error.message,
        isUser: false,
        timestamp: new Date(),
        isError: true,
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  return (
    <ChatContainer>
      <MessageList>
        {messages.length === 0 && (
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center',
            height: '100%',
            opacity: 0.7
          }}>
            <Typography variant="body1" color="text.secondary">
              Ask me anything about biotech regulations and compliance!
            </Typography>
          </Box>
        )}
        {messages.map((message, index) => (
          <Fade in timeout={500} key={index}>
            <MessageContainer isUser={message.isUser}>
              <MessageGroup isUser={message.isUser}>
                {message.isUser ? (
                  <>
                    <MessageContent isUser={message.isUser}>
                      <MessageBubble 
                        isUser={message.isUser}
                        sx={message.isError ? {
                          backgroundColor: theme.palette.error.light,
                          color: theme.palette.error.contrastText,
                        } : {}}
                      >
                        <Typography variant="body1">{message.text}</Typography>
                      </MessageBubble>
                      {message.attachments && (
                        <Box sx={{ mt: 1, mr: 2 }}>
                          <Typography variant="caption" color="text.secondary">
                            Attachments: {message.attachments.join(', ')}
                          </Typography>
                        </Box>
                      )}
                      {message.sources && (
                        <Box sx={{ mt: 1, mr: 2 }}>
                          <Typography variant="caption" color="text.secondary">
                            Sources:
                          </Typography>
                          {message.sources.map((source, idx) => (
                            <Typography 
                              key={idx} 
                              variant="caption" 
                              color="text.secondary" 
                              sx={{ 
                                display: 'block',
                                ml: 1,
                                fontSize: '0.75rem',
                                textAlign: 'right',
                                '&::before': {
                                  content: '"•"',
                                  marginRight: '4px',
                                }
                              }}
                            >
                              {source.content}
                            </Typography>
                          ))}
                        </Box>
                      )}
                    </MessageContent>
                    <UserAvatar>U</UserAvatar>
                  </>
                ) : (
                  <>
                    <AssistantAvatar>AI</AssistantAvatar>
                    <MessageContent isUser={message.isUser}>
                      <MessageBubble 
                        isUser={message.isUser}
                        sx={message.isError ? {
                          backgroundColor: theme.palette.error.light,
                          color: theme.palette.error.contrastText,
                        } : {}}
                      >
                        <Typography variant="body1">{message.text}</Typography>
                      </MessageBubble>
                      {message.attachments && (
                        <Box sx={{ mt: 1, ml: 2 }}>
                          <Typography variant="caption" color="text.secondary">
                            Attachments: {message.attachments.join(', ')}
                          </Typography>
                        </Box>
                      )}
                      {message.sources && (
                        <Box sx={{ mt: 1, ml: 2 }}>
                          <Typography variant="caption" color="text.secondary">
                            Sources:
                          </Typography>
                          {message.sources.map((source, idx) => (
                            <Typography 
                              key={idx} 
                              variant="caption" 
                              color="text.secondary" 
                              sx={{ 
                                display: 'block',
                                ml: 1,
                                fontSize: '0.75rem',
                                textAlign: 'left',
                                '&::before': {
                                  content: '"•"',
                                  marginRight: '4px',
                                }
                              }}
                            >
                              {source.content}
                            </Typography>
                          ))}
                        </Box>
                      )}
                      {message.processedAttachments && (
                        <Box sx={{ mt: 1, ml: 2 }}>
                          <Typography variant="caption" color="text.secondary">
                            Processed files: {message.processedAttachments.join(', ')}
                          </Typography>
                        </Box>
                      )}
                    </MessageContent>
                  </>
                )}
              </MessageGroup>
            </MessageContainer>
          </Fade>
        ))}
        {isTyping && (
          <Fade in timeout={500}>
            <TypingIndicator>
              <CircularProgress size={16} />
              <Typography variant="caption" color="text.secondary">
                Assistant is typing...
              </Typography>
            </TypingIndicator>
          </Fade>
        )}
        <div ref={messagesEndRef} />
      </MessageList>
      <InputContainer>
        {files.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Attached Files:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {files.map((file, index) => (
                <Chip
                  key={index}
                  label={file.name}
                  onDelete={() => handleRemoveFile(index)}
                  size="small"
                />
              ))}
            </Box>
          </Box>
        )}
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          <input
            type="file"
            multiple
            onChange={handleFileUpload}
            style={{ display: 'none' }}
            ref={fileInputRef}
          />
          <IconButton
            color="primary"
            onClick={() => fileInputRef.current?.click()}
          >
            <AttachFileIcon />
          </IconButton>
          <StyledTextField
            fullWidth
            placeholder="Type your message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            multiline
            maxRows={4}
            size="small"
          />
          <SendButton
            onClick={handleSend}
            disabled={!input.trim() && files.length === 0}
            size="small"
          >
            <SendRoundedIcon fontSize="small" />
          </SendButton>
        </Box>
      </InputContainer>
    </ChatContainer>
  );
}

export default Chatbot;
