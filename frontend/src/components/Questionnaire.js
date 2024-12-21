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
} from '@mui/material';

const Questionnaire = ({ onSubmit }) => {
  const [formData, setFormData] = useState({
    intended_purpose: '',
    life_threatening: false,
    user_type: '',
    requires_sterilization: false,
    body_contact_duration: '',
  });

  const handleChange = (event) => {
    const { name, value, checked } = event.target;
    setFormData(prev => ({
      ...prev,
      [name]: event.target.type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    onSubmit(formData);
  };

  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>
        Product Information Questionnaire
      </Typography>

      <form onSubmit={handleSubmit}>
        <FormControl fullWidth sx={{ mb: 2 }}>
          <InputLabel>Intended Purpose</InputLabel>
          <Select
            name="intended_purpose"
            value={formData.intended_purpose}
            onChange={handleChange}
            required
          >
            <MenuItem value="Diagnostic">Diagnostic</MenuItem>
            <MenuItem value="Therapeutic">Therapeutic</MenuItem>
            <MenuItem value="Monitoring">Monitoring</MenuItem>
            <MenuItem value="Surgical">Surgical</MenuItem>
            <MenuItem value="Implantable">Implantable</MenuItem>
          </Select>
        </FormControl>

        <FormControlLabel
          control={
            <Switch
              name="life_threatening"
              checked={formData.life_threatening}
              onChange={handleChange}
            />
          }
          label="Used in life-threatening scenarios"
          sx={{ mb: 2 }}
        />

        <FormControl fullWidth sx={{ mb: 2 }}>
          <InputLabel>User Type</InputLabel>
          <Select
            name="user_type"
            value={formData.user_type}
            onChange={handleChange}
            required
          >
            <MenuItem value="Healthcare Professionals">Healthcare Professionals</MenuItem>
            <MenuItem value="Patients">Patients</MenuItem>
            <MenuItem value="Both">Both</MenuItem>
          </Select>
        </FormControl>

        <FormControlLabel
          control={
            <Switch
              name="requires_sterilization"
              checked={formData.requires_sterilization}
              onChange={handleChange}
            />
          }
          label="Requires sterilization before use"
          sx={{ mb: 2 }}
        />

        <TextField
          fullWidth
          label="Duration of Body Contact"
          name="body_contact_duration"
          value={formData.body_contact_duration}
          onChange={handleChange}
          required
          sx={{ mb: 3 }}
        />

        <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
          <Button
            type="submit"
            variant="contained"
            color="primary"
            size="large"
          >
            Submit
          </Button>
        </Box>
      </form>
    </Paper>
  );
};

export default Questionnaire;
