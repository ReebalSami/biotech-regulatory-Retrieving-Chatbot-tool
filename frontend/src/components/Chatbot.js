import React, { useState, useRef, useEffect } from 'react';
import SendRoundedIcon from '@mui/icons-material/SendRounded';
import AttachFileIcon from '@mui/icons-material/AttachFile';

function Chatbot({ guidelines, questionnaireData, isLoadingGuidelines }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [files, setFiles] = useState([]);
  const [attachmentIds, setAttachmentIds] = useState([]);
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Initial welcome message
  useEffect(() => {
    if (messages.length === 0) {
      const initialMessage = {
        text: [
          "✨ Welcome to the Future of Biotech Innovation! ✨",
          "",
          "I'm your AI Navigator in the biotech regulatory landscape, ready to empower your groundbreaking ideas! 🧬",
          "",
          "Together, we'll:",
          "🚀 Transform your innovative concepts into compliant realities",
          "🎯 Navigate regulatory requirements with precision",
          "💡 Unlock the potential of your biotech venture",
          "",
          "Start by completing our smart questionnaire, and I'll craft a personalized regulatory roadmap just for you!",
          "",
          "Ready to revolutionize biotech? Let's begin! 🌟"
        ].join('\n'),
        isUser: false,
        timestamp: new Date(),
      };
      setMessages([initialMessage]);
    }
  }, []);

  // Update context when questionnaire is submitted and guidelines are loaded
  useEffect(() => {
    if (questionnaireData && !isLoadingGuidelines && guidelines.length > 0 && messages.length <= 1) {
      const contextMessage = {
        text: [
          `🎯 Perfect! I'm now equipped with insights about your ${questionnaireData.productType || 'biotech product'}!`,
          "",
          questionnaireData.productDescription ? 
            `Your vision of ${questionnaireData.productDescription} is fascinating, and I've analyzed all applicable regulations to help you succeed.` :
            "I've analyzed all applicable regulations to help you succeed.",
          "",
          "Here's what makes your project unique:",
          "",
          ...guidelines.map((g, i) => `${i + 1}. ${g.title}`),
          "",
          "I'm your dedicated partner in bringing this innovation to life! Ask me anything about:",
          "• Regulatory requirements specific to your product",
          "• Compliance strategies",
          "• Next steps in your journey",
          "",
          "Let's make your biotech vision a reality! What would you like to explore first? 🚀"
        ].join('\n'),
        isUser: false,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, contextMessage]);
    } else if (questionnaireData && isLoadingGuidelines && messages.length <= 1) {
      const loadingMessage = {
        text: [
          "🔄 Analyzing your innovative project...",
          "",
          "I'm processing your questionnaire responses and crafting a personalized regulatory strategy.",
          "This will only take a moment! ✨"
        ].join('\n'),
        isUser: false,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, loadingMessage]);
    }
  }, [questionnaireData, guidelines, isLoadingGuidelines]);

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
          context: [
            ...(questionnaireData ? [`Product Information: ${JSON.stringify(questionnaireData)}`] : []),
            ...(guidelines.length > 0 ? [`Regulatory Guidelines: ${JSON.stringify(guidelines)}`] : []),
          ],
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
    <div className="chat-container">
      <div className="chat-messages">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`message-group ${message.isUser ? 'user' : 'assistant'}`}
          >
            <div className={`avatar ${message.isUser ? 'user' : 'assistant'}`}>
              {message.isUser ? 'U' : 'AI'}
            </div>
            <div className={`message ${message.isUser ? 'user' : 'assistant'}`}>
              <div className="message-content">
                {message.text.split('\n').map((line, i) => (
                  <React.Fragment key={i}>
                    {line}
                    <br />
                  </React.Fragment>
                ))}
              </div>
              {message.attachments && message.attachments.length > 0 && (
                <div className="message-attachments">
                  📎 {message.attachments.join(', ')}
                </div>
              )}
              {message.processedAttachments && message.processedAttachments.length > 0 && (
                <div className="message-attachments">
                  ✅ {message.processedAttachments.join(', ')}
                </div>
              )}
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="message-group assistant">
            <div className="avatar assistant">AI</div>
            <div className="message assistant">
              <div className="typing-indicator">
                AI is thinking<span>.</span><span>.</span><span>.</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-container">
        <input
          type="file"
          multiple
          onChange={handleFileUpload}
          ref={fileInputRef}
          style={{ display: 'none' }}
        />
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask me anything about biotech regulations..."
          className="modern-input"
        />
        <div className="chat-actions">
          <button
            className="modern-button secondary"
            onClick={() => fileInputRef.current?.click()}
          >
            <AttachFileIcon /> Attach
          </button>
          <button
            className="modern-button"
            onClick={handleSend}
            disabled={!input.trim() && files.length === 0}
          >
            <SendRoundedIcon /> Send
          </button>
        </div>

        {files.length > 0 && (
          <div className="file-preview">
            {files.map((file, index) => (
              <div key={index} className="file-item">
                📎 {file.name}
                <button
                  className="remove-file"
                  onClick={() => handleRemoveFile(index)}
                  aria-label="Remove file"
                >
                  <span className="close-icon">×</span>
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default Chatbot;
