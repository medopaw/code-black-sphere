import React from 'react';
import { Box, Typography, Collapse, IconButton } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ReactMarkdown from 'react-markdown';

const ProblemDescription = ({ description }) => {
  const [expanded, setExpanded] = React.useState(true);

  const handleExpandClick = () => {
    setExpanded(!expanded);
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          题目描述
        </Typography>
        <IconButton onClick={handleExpandClick}>
          {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
        </IconButton>
      </Box>
      <Collapse in={expanded}>
        <Box sx={{ 
          '& .markdown-body': {
            fontFamily: 'inherit',
            fontSize: 'inherit',
            lineHeight: 'inherit',
          }
        }}>
          <ReactMarkdown>{description}</ReactMarkdown>
        </Box>
      </Collapse>
    </Box>
  );
};

export default ProblemDescription; 
