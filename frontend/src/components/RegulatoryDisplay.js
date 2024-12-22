import React from 'react';
import {
  Paper,
  Typography,
  List,
  ListItem,
  Divider,
  Box,
  Chip,
  alpha,
  Stack,
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

const StyledListItem = styled(ListItem)(({ theme }) => ({
  backgroundColor: alpha(theme.palette.background.paper, 0.5),
  borderRadius: theme.shape.borderRadius,
  marginBottom: theme.spacing(2),
  padding: theme.spacing(3),
  transition: theme.transitions.create(['background-color', 'box-shadow']),
  '&:hover': {
    backgroundColor: theme.palette.background.paper,
    boxShadow: `0 4px 20px ${alpha(theme.palette.common.black, 0.05)}`,
  },
}));

const StyledChip = styled(Chip)(({ theme }) => ({
  borderRadius: theme.shape.borderRadius,
  fontWeight: 600,
  backgroundColor: alpha(theme.palette.primary.main, 0.1),
  color: theme.palette.primary.main,
  '& .MuiChip-label': {
    padding: '4px 12px',
  },
}));

const RegulatoryDisplay = ({ guidelines, questionnaireData }) => {
  if (!guidelines || guidelines.length === 0) {
    return (
      <StyledPaper elevation={0}>
        <Box sx={{ 
          display: 'flex', 
          flexDirection: 'column', 
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: 400,
          textAlign: 'center',
          gap: 2
        }}>
          <Typography variant="h6" color="text.secondary">
            No regulatory guidelines available yet
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Please complete the questionnaire to view applicable guidelines
          </Typography>
        </Box>
      </StyledPaper>
    );
  }

  return (
    <StyledPaper elevation={0}>
      <Stack spacing={4}>
        {questionnaireData && (
          <Box>
            <Typography variant="h5" gutterBottom color="text.primary">
              Product Profile
            </Typography>
            <Box sx={{ 
              backgroundColor: alpha('#FFFFFF', 0.5),
              borderRadius: 2,
              p: 2,
              display: 'flex',
              flexWrap: 'wrap',
              gap: 1
            }}>
              <StyledChip label={`Purpose: ${questionnaireData.intended_purpose}`} />
              <StyledChip label={`Users: ${questionnaireData.user_type}`} />
              <StyledChip label={`Duration: ${questionnaireData.body_contact_duration}`} />
              {questionnaireData.life_threatening && (
                <StyledChip label="Life-threatening Use" />
              )}
              {questionnaireData.requires_sterilization && (
                <StyledChip label="Requires Sterilization" />
              )}
            </Box>
          </Box>
        )}

        <Box>
          <Typography variant="h5" gutterBottom color="text.primary">
            Applicable Guidelines
          </Typography>
          <List disablePadding>
            {guidelines.map((guideline, index) => (
              <StyledListItem key={index} disablePadding>
                <Box sx={{ width: '100%' }}>
                  <Box sx={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'space-between',
                    mb: 2 
                  }}>
                    <Typography variant="h6" component="div" sx={{ fontWeight: 600 }}>
                      {guideline.title}
                    </Typography>
                    <StyledChip
                      label={`${(guideline.relevance_score * 100).toFixed(0)}% Match`}
                      size="small"
                    />
                  </Box>
                  <Typography 
                    variant="body1" 
                    color="text.secondary"
                    sx={{ 
                      mb: 2,
                      lineHeight: 1.6
                    }}
                  >
                    {guideline.content}
                  </Typography>
                  <Typography 
                    variant="caption" 
                    color="text.secondary"
                    sx={{ 
                      display: 'block',
                      fontStyle: 'italic'
                    }}
                  >
                    Source: {guideline.reference}
                  </Typography>
                </Box>
              </StyledListItem>
            ))}
          </List>
        </Box>
      </Stack>
    </StyledPaper>
  );
};

export default RegulatoryDisplay;
