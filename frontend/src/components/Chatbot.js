import React, { useState, useRef, useEffect, memo } from 'react';
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
  CircularProgress,
  alpha,
  Stack,
} from '@mui/material';
import {
  Send as SendIcon,
  AttachFile as AttachFileIcon,
  Close as CloseIcon
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

// Custom styled components
const StyledPaper = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  borderRadius: theme.shape.borderRadius * 2,
  backgroundColor: alpha(theme.palette.background.paper, 0.8),
  backdropFilter: 'blur(20px)',
  border: '1px solid',
  borderColor: alpha(theme.palette.divider, 0.1),
  height: '80vh',
  display: 'flex',
  flexDirection: 'column',
  transition: 'all 0.3s ease-in-out',
  '&:hover': {
    transform: 'translateY(-2px)',
    boxShadow: '0 8px 30px rgba(0,0,0,0.12)',
  },
}));

const MessageBubble = styled('div')(({ theme, isUser }) => ({
  backgroundColor: isUser ? alpha(theme.palette.primary.main, 0.1) : alpha(theme.palette.background.paper, 0.5),
  color: theme.palette.text.primary,
  padding: theme.spacing(2, 3),
  borderRadius: theme.shape.borderRadius * 2,
  maxWidth: '80%',
  wordBreak: 'break-word',
  marginLeft: isUser ? 'auto' : 0,
  marginRight: isUser ? 0 : 'auto',
  position: 'relative',
  boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
  transition: 'all 0.2s ease-in-out',
  '&:hover': {
    transform: 'translateY(-1px)',
    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
  },
  '&::before': {
    content: '""',
    position: 'absolute',
    bottom: 0,
    [isUser ? 'right' : 'left']: -8,
    borderStyle: 'solid',
    borderWidth: '8px 8px 0 8px',
    borderColor: `${isUser ? alpha(theme.palette.primary.main, 0.1) : alpha(theme.palette.background.paper, 0.5)} transparent transparent transparent`,
    transform: isUser ? 'none' : 'scaleX(-1)',
  },
}));

const StyledTextField = styled(TextField)(({ theme }) => ({
  '& .MuiOutlinedInput-root': {
    backgroundColor: alpha(theme.palette.background.paper, 0.8),
    borderRadius: theme.shape.borderRadius * 2,
    padding: theme.spacing(1, 2),
    transition: 'all 0.2s ease-in-out',
    '&.Mui-focused': {
      backgroundColor: theme.palette.background.paper,
      boxShadow: `0 0 0 2px ${alpha(theme.palette.primary.main, 0.2)}`,
      transform: 'translateY(-1px)',
    },
    '&:hover': {
      backgroundColor: theme.palette.background.paper,
    },
  },
}));

const StyledIconButton = styled(IconButton)(({ theme }) => ({
  backgroundColor: theme.palette.primary.main,
  color: theme.palette.common.white,
  '&:hover': {
    backgroundColor: theme.palette.primary.dark,
    transform: 'translateY(-1px)',
  },
  '&:disabled': {
    backgroundColor: alpha(theme.palette.primary.main, 0.5),
  },
  width: 40,
  height: 40,
  marginLeft: theme.spacing(1),
  transition: 'all 0.2s ease-in-out',
}));

const StyledChip = styled(Chip)(({ theme }) => ({
  borderRadius: theme.shape.borderRadius,
  backgroundColor: alpha(theme.palette.primary.main, 0.1),
  color: theme.palette.primary.main,
  margin: theme.spacing(0.5),
  transition: 'all 0.2s ease-in-out',
  '&:hover': {
    backgroundColor: alpha(theme.palette.primary.main, 0.2),
    transform: 'translateY(-1px)',
  },
  '& .MuiChip-label': {
    padding: '4px 12px',
  },
  '& .MuiChip-deleteIcon': {
    color: theme.palette.primary.main,
    '&:hover': {
      color: theme.palette.primary.dark,
    },
  },
}));

const Message = memo(({ message, handleRemoveFile }) => (
  <ListItem
    sx={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'stretch',
      py: 2,
    }}
  >
    <Stack spacing={1} width="100%">
      <MessageBubble isUser={message.role === 'user'}>
        <Typography variant="body1">
          {message.content}
        </Typography>
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{ display: 'block', mt: 1, textAlign: message.role === 'user' ? 'right' : 'left' }}
        >
          {new Date(message.timestamp).toLocaleTimeString()}
        </Typography>
      </MessageBubble>
      {message.attachments?.length > 0 && (
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
          {message.attachments.map((file, fileIndex) => (
            <StyledChip
              key={fileIndex}
              label={file.name}
              onDelete={() => handleRemoveFile(fileIndex)}
              deleteIcon={<CloseIcon />}
            />
          ))}
        </Box>
      )}
    </Stack>
  </ListItem>
));

const ChatInput = memo(({ input, setInput, loading, handleSend, handleKeyPress, handleFileSelect, fileInputRef }) => (
  <Box sx={{ position: 'relative' }}>
    <StyledTextField
      fullWidth
      multiline
      maxRows={4}
      value={input}
      onChange={(e) => setInput(e.target.value)}
      onKeyPress={handleKeyPress}
      placeholder="Type your message..."
      disabled={loading}
      InputProps={{
        endAdornment: (
          <IconButton
            onClick={() => fileInputRef.current?.click()}
            disabled={loading}
            sx={{ mr: 1 }}
          >
            <AttachFileIcon />
          </IconButton>
        ),
      }}
    />
    <StyledIconButton
      onClick={handleSend}
      disabled={loading}
    >
      {loading ? <CircularProgress size={24} color="inherit" /> : <SendIcon />}
    </StyledIconButton>
  </Box>
));

const Chatbot = ({ questionnaireData, guidelines }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [attachments, setAttachments] = useState([]);
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (messages.length === 0) {
      setMessages([{
        role: 'assistant',
        content: 'Hi! I can help you understand regulatory requirements for your biotech product. How can I assist you today?',
        timestamp: new Date()
      }]);
    }
  }, []);

  useEffect(() => {
    const scrollToBottom = () => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() && attachments.length === 0) return;

    const newMessage = {
      role: 'user',
      content: input,
      attachments: [...attachments],
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, newMessage]);
    setInput('');
    setAttachments([]);
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append('message', input);
      attachments.forEach(file => formData.append('files', file));

      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Failed to get response');

      const data = await response.json();
      
      // Add a small delay for a more natural conversation flow
      setTimeout(() => {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.response,
          timestamp: new Date(),
        }]);
        setLoading(false);
      }, 500);
      
    } catch (err) {
      setError('Failed to send message. Please try again.');
      console.error('Chat error:', err);
      setLoading(false);
    }
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  const handleFileSelect = (event) => {
    const files = Array.from(event.target.files);
    setAttachments(prev => [...prev, ...files]);
    event.target.value = null;
  };

  const handleRemoveFile = (index) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  };

  return (
    <StyledPaper elevation={0}>
      <Box sx={{ flex: 1, overflow: 'auto', mb: 2, px: 2 }}>
        <List>
          {messages.map((message, index) => (
            <Message
              key={index}
              message={message}
              handleRemoveFile={handleRemoveFile}
            />
          ))}
        </List>
        <div ref={messagesEndRef} />
      </Box>

      <Box sx={{ p: 2 }}>
        {attachments.length > 0 && (
          <Box sx={{ 
            display: 'flex', 
            flexWrap: 'wrap', 
            gap: 1, 
            mb: 2,
            p: 2,
            backgroundColor: alpha('#FFFFFF', 0.5),
            borderRadius: 2,
          }}>
            {attachments.map((file, index) => (
              <StyledChip
                key={index}
                label={file.name}
                onDelete={() => handleRemoveFile(index)}
                deleteIcon={<CloseIcon />}
              />
            ))}
          </Box>
        )}

        <ChatInput
          input={input}
          setInput={setInput}
          loading={loading}
          handleSend={handleSend}
          handleKeyPress={handleKeyPress}
          handleFileSelect={handleFileSelect}
          fileInputRef={fileInputRef}
        />
      </Box>

      <input
        type="file"
        ref={fileInputRef}
        style={{ display: 'none' }}
        onChange={handleFileSelect}
        multiple
      />

      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={() => setError(null)} severity="error" sx={{ width: '100%' }}>
          {error}
        </Alert>
      </Snackbar>
    </StyledPaper>
  );
};

export default memo(Chatbot);
