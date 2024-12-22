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
const MessageContainer = styled(Box)(({ theme, isUser }) => ({
  display: 'flex',
  justifyContent: isUser ? 'flex-end' : 'flex-start',
  marginBottom: theme.spacing(2),
}));

const MessageBubble = styled(Paper)(({ theme, isUser }) => ({
  padding: theme.spacing(1.5, 2),
  maxWidth: '70%',
  borderRadius: isUser ? '20px 20px 4px 20px' : '20px 20px 20px 4px',
  backgroundColor: isUser ? theme.palette.primary.main : theme.palette.background.paper,
  color: isUser ? theme.palette.primary.contrastText : theme.palette.text.primary,
  boxShadow: theme.shadows[1],
  position: 'relative',
  '&::before': {
    content: '""',
    position: 'absolute',
    bottom: 0,
    [isUser ? 'right' : 'left']: -8,
    borderStyle: 'solid',
    borderWidth: '8px 8px 0 0',
    borderColor: `${isUser ? theme.palette.primary.main : theme.palette.background.paper} transparent transparent transparent`,
  },
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
  backgroundColor: theme.palette.secondary.light,
  width: 32,
  height: 32,
  marginRight: theme.spacing(1),
  boxShadow: theme.shadows[1],
}));

const UserAvatar = styled(Avatar)(({ theme }) => ({
  backgroundColor: theme.palette.primary.main,
  width: 32,
  height: 32,
  marginLeft: theme.spacing(1),
  boxShadow: theme.shadows[1],
}));

const ChatContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  flexDirection: 'column',
  height: '100%',
  backgroundColor: theme.palette.background.default,
  borderRadius: theme.shape.borderRadius * 2,
  overflow: 'hidden',
}));

const MessageList = styled(Box)(({ theme }) => ({
  flexGrow: 1,
  overflow: 'auto',
  padding: theme.spacing(3),
  scrollBehavior: 'smooth',
  '&::-webkit-scrollbar': {
    width: 6,
  },
  '&::-webkit-scrollbar-track': {
    background: 'transparent',
  },
  '&::-webkit-scrollbar-thumb': {
    background: theme.palette.divider,
    borderRadius: 3,
  },
}));

const InputContainer = styled(Box)(({ theme }) => ({
  padding: theme.spacing(2),
  borderTop: `1px solid ${theme.palette.divider}`,
  backgroundColor: theme.palette.background.paper,
  backdropFilter: 'blur(10px)',
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
      // Simulate API call with timeout
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const assistantMessage = {
        text: "I'm here to help you with regulatory compliance. What would you like to know?",
        isUser: false,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
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
        {messages.map((message, index) => (
          <Fade in timeout={500} key={index}>
            <MessageContainer isUser={message.isUser}>
              {!message.isUser && <AssistantAvatar>AI</AssistantAvatar>}
              <MessageBubble isUser={message.isUser}>
                <Typography variant="body1">{message.text}</Typography>
              </MessageBubble>
              {message.isUser && <UserAvatar>U</UserAvatar>}
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
