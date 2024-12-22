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
} from '@mui/material';
import SendRoundedIcon from '@mui/icons-material/SendRounded';
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
  const messagesEndRef = useRef(null);
  const theme = useTheme();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = {
      text: input.trim(),
      isUser: true,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: userMessage.text,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response from AI');
      }

      const data = await response.json();
      
      const assistantMessage = {
        text: data.response,
        isUser: false,
        timestamp: new Date(),
        sources: data.sources,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        text: "I apologize, but I'm having trouble connecting to the server. Please try again later.",
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
              <CircularProgress size={16} thickness={6} />
              <Typography variant="caption" color="text.secondary">
                Assistant is typing...
              </Typography>
            </TypingIndicator>
          </Fade>
        )}
        <div ref={messagesEndRef} />
      </MessageList>
      <InputContainer>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
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
            disabled={!input.trim() || isTyping}
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
