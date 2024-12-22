import React, { useState } from 'react';
import {
  Paper,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  Button,
  Box,
  TextField,
  Stack,
  alpha,
} from '@mui/material';
import { styled } from '@mui/material/styles';

// Custom styled components
const StyledPaper = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(4),
  borderRadius: theme.shape.borderRadius * 2,
  backgroundColor: alpha(theme.palette.background.paper, 0.8),
  backdropFilter: 'blur(20px)',
  border: '1px solid',
  borderColor: alpha(theme.palette.divider, 0.1),
}));

const StyledFormControl = styled(FormControl)(({ theme }) => ({
  '& .MuiInputLabel-root': {
    '&.Mui-focused, &.MuiFormLabel-filled': {
      backgroundColor: theme.palette.background.paper,
      padding: '0 8px',
      marginLeft: -4,
    },
  },
  '& .MuiOutlinedInput-root': {
    transition: 'all 0.2s ease-in-out',
    '&:hover': {
      backgroundColor: alpha(theme.palette.background.paper, 0.9),
    },
    '&.Mui-focused': {
      backgroundColor: theme.palette.background.paper,
      boxShadow: `0 0 0 2px ${alpha(theme.palette.primary.main, 0.2)}`,
    },
  },
}));

const StyledSwitch = styled(Switch)(({ theme }) => ({
  '& .MuiSwitch-switchBase.Mui-checked': {
    color: theme.palette.primary.main,
    '&:hover': {
      backgroundColor: alpha(theme.palette.primary.main, 0.08),
    },
  },
  '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
    backgroundColor: theme.palette.primary.main,
  },
}));

const StyledButton = styled(Button)(({ theme }) => ({
  borderRadius: theme.shape.borderRadius,
  padding: '12px 24px',
  fontSize: '1rem',
  fontWeight: 600,
  textTransform: 'none',
  boxShadow: 'none',
  '&:hover': {
    boxShadow: 'none',
  },
}));

const Questionnaire = ({ onSubmit }) => {
  const [formData, setFormData] = useState({
    intended_purpose: '',
    life_threatening: false,
    user_type: '',
    requires_sterilization: false,
    body_contact_duration: '',
  });

  const handleChange = (name, value) => {
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    onSubmit(formData);
  };

  return (
    <StyledPaper elevation={0}>
      <Typography variant="h5" gutterBottom sx={{ mb: 4, color: 'text.primary' }}>
        Product Information Questionnaire
      </Typography>

      <form onSubmit={handleSubmit}>
        <Stack spacing={3}>
          <StyledFormControl fullWidth margin="normal">
            <InputLabel id="intended-purpose-label">Intended Purpose</InputLabel>
            <Select
              labelId="intended-purpose-label"
              id="intended-purpose"
              value={formData.intended_purpose}
              label="Intended Purpose"
              onChange={(e) => handleChange('intended_purpose', e.target.value)}
            >
              <MenuItem value="diagnostic">Diagnostic Device</MenuItem>
              <MenuItem value="therapeutic">Therapeutic Device</MenuItem>
              <MenuItem value="monitoring">Monitoring Device</MenuItem>
            </Select>
          </StyledFormControl>

          <StyledFormControl fullWidth margin="normal">
            <InputLabel id="user-type-label">Intended Users</InputLabel>
            <Select
              labelId="user-type-label"
              id="user-type"
              value={formData.user_type}
              label="Intended Users"
              onChange={(e) => handleChange('user_type', e.target.value)}
            >
              <MenuItem value="healthcare_professional">Healthcare Professional</MenuItem>
              <MenuItem value="patient">Patient</MenuItem>
              <MenuItem value="both">Both</MenuItem>
            </Select>
          </StyledFormControl>

          <StyledFormControl fullWidth margin="normal">
            <InputLabel id="body-contact-duration-label">Body Contact Duration</InputLabel>
            <Select
              labelId="body-contact-duration-label"
              id="body-contact-duration"
              value={formData.body_contact_duration}
              label="Body Contact Duration"
              onChange={(e) => handleChange('body_contact_duration', e.target.value)}
            >
              <MenuItem value="temporary">Temporary (≤ 60 minutes)</MenuItem>
              <MenuItem value="short_term">Short Term (≤ 30 days)</MenuItem>
              <MenuItem value="long_term">Long Term (> 30 days)</MenuItem>
            </Select>
          </StyledFormControl>

          <Box sx={{ 
            display: 'flex', 
            flexDirection: 'column', 
            gap: 2,
            backgroundColor: alpha('#FFFFFF', 0.5),
            borderRadius: 2,
            p: 2
          }}>
            <FormControlLabel
              control={
                <StyledSwitch
                  name="life_threatening"
                  checked={formData.life_threatening}
                  onChange={(e) => handleChange('life_threatening', e.target.checked)}
                />
              }
              label="Life-threatening Use"
            />

            <FormControlLabel
              control={
                <StyledSwitch
                  name="requires_sterilization"
                  checked={formData.requires_sterilization}
                  onChange={(e) => handleChange('requires_sterilization', e.target.checked)}
                />
              }
              label="Requires Sterilization"
            />
          </Box>

          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
            <StyledButton
              type="submit"
              variant="contained"
              color="primary"
              size="large"
            >
              Find Applicable Guidelines
            </StyledButton>
          </Box>
        </Stack>
      </form>
    </StyledPaper>
  );
};

export default Questionnaire;
