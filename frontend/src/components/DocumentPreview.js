import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Paper,
} from '@mui/material';

const DocumentPreview = ({ open, onClose, document }) => {
  const [preview, setPreview] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (document?.id) {
      setLoading(true);
      setError(null);
      // Fetch document preview
      fetch(`http://localhost:8000/user-documents/${document.id}/preview`)
        .then((response) => {
          if (!response.ok) throw new Error('Failed to load preview');
          return response.text();
        })
        .then((data) => {
          setPreview(data);
          setLoading(false);
        })
        .catch((error) => {
          console.error('Error fetching preview:', error);
          setError('Failed to load document preview');
          setLoading(false);
        });
    }
  }, [document]);

  if (!document) return null;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Typography variant="h6">{document.title}</Typography>
        {document.description && (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            {document.description}
          </Typography>
        )}
        <Typography variant="caption" display="block" sx={{ mt: 1 }}>
          Uploaded on {new Date(document.upload_date).toLocaleString()}
        </Typography>
      </DialogTitle>
      <DialogContent>
        <Paper 
          elevation={0} 
          sx={{ 
            p: 2, 
            bgcolor: 'grey.50', 
            minHeight: 300,
            maxHeight: '60vh',
            overflow: 'auto'
          }}
        >
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300 }}>
              <Typography>Loading preview...</Typography>
            </Box>
          ) : error ? (
            <Box sx={{ p: 2, textAlign: 'center' }}>
              <Typography color="error">{error}</Typography>
            </Box>
          ) : !preview ? (
            <Box sx={{ p: 2, textAlign: 'center' }}>
              <Typography color="text.secondary">
                No preview available for this document
              </Typography>
            </Box>
          ) : (
            <Typography
              component="pre"
              sx={{
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
                fontFamily: 'monospace',
                fontSize: '0.875rem',
                lineHeight: 1.5,
              }}
            >
              {preview}
            </Typography>
          )}
        </Paper>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};

export default DocumentPreview;
