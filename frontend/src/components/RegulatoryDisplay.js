import React from 'react';
import {
  Paper,
  Typography,
  List,
  ListItem,
  Divider,
  Box,
  Chip,
} from '@mui/material';

const RegulatoryDisplay = ({ guidelines }) => {
  if (!guidelines || guidelines.length === 0) {
    return (
      <Paper elevation={3} sx={{ p: 3 }}>
        <Typography variant="h6" color="text.secondary">
          No regulatory guidelines available yet. Please complete the questionnaire first.
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>
        Relevant Regulatory Guidelines
      </Typography>

      <List>
        {guidelines.map((guideline, index) => (
          <React.Fragment key={index}>
            <ListItem alignItems="flex-start">
              <Box sx={{ width: '100%' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <Typography variant="h6" component="div">
                    {guideline.title}
                  </Typography>
                  <Chip
                    label={`Relevance: ${(guideline.relevance_score * 100).toFixed(0)}%`}
                    color="primary"
                    size="small"
                  />
                </Box>
                <Typography component="div" variant="body2" color="text.secondary">
                  {guideline.content}
                </Typography>
                <Typography component="div" variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                  Reference: {guideline.reference}
                </Typography>
              </Box>
            </ListItem>
            {index < guidelines.length - 1 && <Divider />}
          </React.Fragment>
        ))}
      </List>
    </Paper>
  );
};

export default RegulatoryDisplay;
