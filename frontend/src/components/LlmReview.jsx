import React from 'react';
import {
  Box,
  Typography,
  Collapse,
  IconButton,
  Paper,
  Divider,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ReactMarkdown from 'react-markdown';

const LlmReview = ({ review }) => {
  const [expanded, setExpanded] = React.useState(true);

  const handleExpandClick = () => {
    setExpanded(!expanded);
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          AI 代码评估
        </Typography>
        <IconButton onClick={handleExpandClick}>
          {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
        </IconButton>
      </Box>
      <Collapse in={expanded}>
        <Paper sx={{ p: 2 }}>
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle1" color="primary" gutterBottom>
              代码质量评分
            </Typography>
            <Typography variant="h4" color="primary" sx={{ mb: 1 }}>
              {review.score}/100
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {review.scoreDescription}
            </Typography>
          </Box>

          <Divider sx={{ my: 2 }} />

          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle1" color="primary" gutterBottom>
              代码分析
            </Typography>
            <Box sx={{ 
              '& .markdown-body': {
                fontFamily: 'inherit',
                fontSize: 'inherit',
                lineHeight: 'inherit',
              }
            }}>
              <ReactMarkdown>{review.analysis}</ReactMarkdown>
            </Box>
          </Box>

          <Divider sx={{ my: 2 }} />

          <Box>
            <Typography variant="subtitle1" color="primary" gutterBottom>
              改进建议
            </Typography>
            <Box sx={{ 
              '& .markdown-body': {
                fontFamily: 'inherit',
                fontSize: 'inherit',
                lineHeight: 'inherit',
              }
            }}>
              <ReactMarkdown>{review.suggestions}</ReactMarkdown>
            </Box>
          </Box>
        </Paper>
      </Collapse>
    </Box>
  );
};

export default LlmReview; 
