import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemButton,
  TextField,
  CircularProgress,
  Typography,
  Box,
} from '@mui/material';
import { getProblems } from '../services/problemService';

const ProblemSelectionDialog = ({ open, onClose, onSelect }) => {
  const [problems, setProblems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    const fetchProblems = async () => {
      if (open) {
        try {
          setLoading(true);
          setError(null);
          const data = await getProblems();
          setProblems(data);
        } catch (err) {
          setError('加载题目列表失败');
          console.error('Error fetching problems:', err);
        } finally {
          setLoading(false);
        }
      }
    };

    fetchProblems();
  }, [open]);

  const handleSearchChange = (event) => {
    setSearchTerm(event.target.value);
  };

  const handleProblemSelect = (problem) => {
    onSelect(problem);
    onClose();
  };

  const filteredProblems = problems.filter((problem) =>
    problem.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: { height: '80vh' }
      }}
    >
      <DialogTitle>选择题目</DialogTitle>
      <DialogContent dividers>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="搜索题目..."
          value={searchTerm}
          onChange={handleSearchChange}
          sx={{ mb: 2 }}
        />
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress />
          </Box>
        ) : error ? (
          <Typography color="error" sx={{ p: 2 }}>
            {error}
          </Typography>
        ) : (
          <List sx={{ width: '100%', bgcolor: 'background.paper' }}>
            {filteredProblems.length === 0 ? (
              <ListItem>
                <ListItemText primary="没有找到匹配的题目" />
              </ListItem>
            ) : (
              filteredProblems.map((problem) => (
                <ListItem key={problem.id} disablePadding>
                  <ListItemButton onClick={() => handleProblemSelect(problem)}>
                    <ListItemText
                      primary={problem.title}
                      secondary={
                        <Typography
                          variant="body2"
                          color="text.secondary"
                          sx={{
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            display: '-webkit-box',
                            WebkitLineClamp: 2,
                            WebkitBoxOrient: 'vertical',
                          }}
                        >
                          {problem.description}
                        </Typography>
                      }
                    />
                  </ListItemButton>
                </ListItem>
              ))
            )}
          </List>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>取消</Button>
      </DialogActions>
    </Dialog>
  );
};

export default ProblemSelectionDialog; 
