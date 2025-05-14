import React from 'react';
import {
  Box,
  Typography,
  List,
  ListItem,
  ListItemText,
  Chip,
  Collapse,
  IconButton,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';

const TestResults = ({ results }) => {
  const [expanded, setExpanded] = React.useState(true);

  const handleExpandClick = () => {
    setExpanded(!expanded);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'passed':
        return 'success';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'passed':
        return <CheckCircleIcon color="success" />;
      case 'failed':
        return <ErrorIcon color="error" />;
      default:
        return null;
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          测试结果
        </Typography>
        <IconButton onClick={handleExpandClick}>
          {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
        </IconButton>
      </Box>
      <Collapse in={expanded}>
        <List>
          {results.map((result, index) => (
            <ListItem
              key={index}
              sx={{
                border: '1px solid',
                borderColor: 'divider',
                borderRadius: 1,
                mb: 1,
              }}
            >
              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="subtitle1">
                      测试用例 {index + 1}
                    </Typography>
                    <Chip
                      icon={getStatusIcon(result.status)}
                      label={result.status === 'passed' ? '通过' : '失败'}
                      color={getStatusColor(result.status)}
                      size="small"
                    />
                  </Box>
                }
                secondary={
                  <Box sx={{ mt: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      输入：
                    </Typography>
                    <Typography
                      component="pre"
                      sx={{
                        bgcolor: 'grey.100',
                        p: 1,
                        borderRadius: 1,
                        overflow: 'auto',
                      }}
                    >
                      {JSON.stringify(result.input, null, 2)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                      预期输出：
                    </Typography>
                    <Typography
                      component="pre"
                      sx={{
                        bgcolor: 'grey.100',
                        p: 1,
                        borderRadius: 1,
                        overflow: 'auto',
                      }}
                    >
                      {JSON.stringify(result.expected, null, 2)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                      实际输出：
                    </Typography>
                    <Typography
                      component="pre"
                      sx={{
                        bgcolor: 'grey.100',
                        p: 1,
                        borderRadius: 1,
                        overflow: 'auto',
                      }}
                    >
                      {JSON.stringify(result.actual, null, 2)}
                    </Typography>
                    {result.error && (
                      <>
                        <Typography variant="body2" color="error" sx={{ mt: 1 }}>
                          错误信息：
                        </Typography>
                        <Typography
                          component="pre"
                          sx={{
                            bgcolor: 'error.light',
                            color: 'error.contrastText',
                            p: 1,
                            borderRadius: 1,
                            overflow: 'auto',
                          }}
                        >
                          {result.error}
                        </Typography>
                      </>
                    )}
                  </Box>
                }
              />
            </ListItem>
          ))}
        </List>
      </Collapse>
    </Box>
  );
};

export default TestResults; 
