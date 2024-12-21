import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Modal,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Alert,
  Snackbar,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Preview as PreviewIcon,
} from '@mui/icons-material';
import DocumentPreview from './DocumentPreview';

const DocumentManager = () => {
  const [documents, setDocuments] = useState([]);
  const [openUpload, setOpenUpload] = useState(false);
  const [previewDocument, setPreviewDocument] = useState(null);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const uploadButtonRef = useRef(null);

  // Form state
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    file: null,
  });

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const response = await fetch('http://localhost:8000/user-documents');
      if (!response.ok) throw new Error('Failed to fetch documents');
      const data = await response.json();
      setDocuments(data);
    } catch (error) {
      setError('Failed to load documents');
    }
  };

  const handleUpload = async () => {
    try {
      if (!formData.file) {
        setError('Please select a file to upload');
        return;
      }

      // Check file size (max 10MB)
      if (formData.file.size > 10 * 1024 * 1024) {
        setError('File size must be less than 10MB');
        return;
      }

      // Check file type
      const allowedTypes = ['.pdf', '.doc', '.docx', '.txt'];
      const fileExtension = formData.file.name.toLowerCase().slice(formData.file.name.lastIndexOf('.'));
      if (!allowedTypes.includes(fileExtension)) {
        setError('Only PDF, Word, and text files are allowed');
        return;
      }

      const uploadData = new FormData();
      uploadData.append('file', formData.file);
      uploadData.append('title', formData.title || formData.file.name);
      uploadData.append('description', formData.description || '');

      const response = await fetch('http://localhost:8000/user-documents/upload', {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
        },
        body: uploadData,
        mode: 'cors',
      });
      
      const responseText = await response.text();
      
      if (!response.ok) {
        let errorMessage;
        try {
          const errorData = JSON.parse(responseText);
          errorMessage = errorData.detail || 'Upload failed';
        } catch {
          errorMessage = responseText || 'Upload failed';
        }
        throw new Error(errorMessage);
      }

      const result = JSON.parse(responseText);

      // Reset form and close dialog
      setFormData({ title: '', description: '', file: null });
      setOpenUpload(false);
      
      // Fetch updated documents
      await fetchDocuments();

      // Return focus to the main upload button before showing success message
      if (uploadButtonRef.current) {
        uploadButtonRef.current.focus();
        // Small delay before showing success to ensure focus is set
        setTimeout(() => {
          setSuccess('Document uploaded successfully');
        }, 100);
      }
    } catch (error) {
      console.error('Upload error:', error);
      setError('Failed to upload document: ' + error.message);
    }
  };

  const handleDelete = async (documentId) => {
    if (!window.confirm('Are you sure you want to delete this document?')) {
      return;
    }

    try {
      const response = await fetch(`http://localhost:8000/user-documents/${documentId}`, {
        method: 'DELETE',
      });

      if (!response.ok) throw new Error('Delete failed');

      setSuccess('Document deleted successfully');
      fetchDocuments();
    } catch (error) {
      setError('Failed to delete document');
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h5" gutterBottom>
            Your Documents
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Upload documents to enhance the chatbot's responses with your specific context
          </Typography>
        </Box>
        <Button
          ref={uploadButtonRef}
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setOpenUpload(true)}
          aria-label="upload document"
          aria-haspopup="dialog"
          sx={{
            '&:focus-visible': {
              outline: '2px solid #1976d2',
              outlineOffset: '2px'
            }
          }}
        >
          Upload Document
        </Button>
      </Box>

      {documents.length === 0 ? (
        <Paper sx={{ p: 3, textAlign: 'center', bgcolor: 'grey.50' }}>
          <Typography color="text.secondary">
            No documents uploaded yet. Upload documents to get more relevant responses from the chatbot.
          </Typography>
        </Paper>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Title</TableCell>
                <TableCell>Description</TableCell>
                <TableCell>Upload Date</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {documents.map((doc) => (
                <TableRow key={doc.id}>
                  <TableCell>{doc.title}</TableCell>
                  <TableCell>{doc.description || '-'}</TableCell>
                  <TableCell>
                    {new Date(doc.upload_date).toLocaleDateString()}
                  </TableCell>
                  <TableCell align="right">
                    <IconButton
                      onClick={() => setPreviewDocument(doc)}
                      color="primary"
                      title="Preview"
                    >
                      <PreviewIcon />
                    </IconButton>
                    <IconButton
                      onClick={() => handleDelete(doc.id)}
                      color="error"
                      title="Delete"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Upload Modal */}
      <Modal
        open={openUpload}
        onClose={() => {
          setOpenUpload(false);
          setFormData({ title: '', description: '', file: null });
          if (uploadButtonRef.current) {
            uploadButtonRef.current.focus();
          }
        }}
        aria-labelledby="upload-modal-title"
        keepMounted={false}
      >
        <Box
          sx={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: 400,
            bgcolor: 'background.paper',
            borderRadius: 1,
            boxShadow: 24,
            p: 4,
          }}
          component="form"
          onSubmit={(e) => {
            e.preventDefault();
            handleUpload();
          }}
        >
          <Typography id="upload-modal-title" variant="h6" component="h2" gutterBottom>
            Upload Supporting Document
          </Typography>
          
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Upload documents to provide additional context for your conversation with the chatbot.
            These documents will be used to better understand your specific case.
          </Typography>
          
          <TextField
            fullWidth
            label="Title"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            sx={{ mb: 2 }}
            id="document-title"
            aria-label="Document title"
          />
          
          <TextField
            fullWidth
            label="Description"
            multiline
            rows={3}
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            sx={{ mb: 2 }}
            id="document-description"
            aria-label="Document description"
          />
          
          <input
            type="file"
            accept=".pdf,.doc,.docx,.txt"
            onChange={(e) => setFormData({ ...formData, file: e.target.files[0] })}
            style={{ marginBottom: '16px', display: 'block' }}
            id="document-file"
            aria-label="Choose document file"
          />
          
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1, mt: 2 }}>
            <Button
              onClick={() => {
                setOpenUpload(false);
                setFormData({ title: '', description: '', file: null });
                if (uploadButtonRef.current) {
                  uploadButtonRef.current.focus();
                }
              }}
              aria-label="Cancel upload"
            >
              Cancel
            </Button>
            <Button
              variant="contained"
              disabled={!formData.file}
              type="submit"
              aria-label="Upload document"
            >
              Upload
            </Button>
          </Box>
        </Box>
      </Modal>

      {/* Document Preview Dialog */}
      <DocumentPreview
        open={!!previewDocument}
        onClose={() => setPreviewDocument(null)}
        document={previewDocument}
      />

      {/* Notifications */}
      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
      >
        <Alert 
          onClose={() => setError(null)} 
          severity="error" 
          sx={{ width: '100%' }}
          variant="filled"
        >
          {error}
        </Alert>
      </Snackbar>
      <Snackbar
        open={!!success}
        autoHideDuration={4000}
        onClose={() => setSuccess(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
        sx={{
          '& .MuiSnackbar-root': {
            position: 'relative'
          }
        }}
      >
        <Alert 
          onClose={() => {
            setSuccess(null);
            // Return focus to upload button when alert closes
            if (uploadButtonRef.current) {
              uploadButtonRef.current.focus();
            }
          }}
          severity="success"
          sx={{ width: '100%' }}
          variant="filled"
        >
          {success}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default DocumentManager;
