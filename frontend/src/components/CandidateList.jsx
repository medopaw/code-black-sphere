import { useState, useEffect } from 'react';
import {
  List,
  ListItem,
  ListItemText,
  ListItemButton,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  Typography,
  Divider,
} from '@mui/material';
import { Add as AddIcon, Delete as DeleteIcon } from '@mui/icons-material';
import useStore from '../store/useStore';
import { candidateApi } from '../services/api';

function CandidateList() {
  const { candidates, currentCandidate, setCandidates, setCurrentCandidate, setLoading, setError } = useStore();
  const [open, setOpen] = useState(false);
  const [newCandidateName, setNewCandidateName] = useState('');

  // 加载候选人列表
  useEffect(() => {
    const fetchCandidates = async () => {
      try {
        setLoading('candidates', true);
        const response = await candidateApi.getAll();
        setCandidates(response.data.candidates);
      } catch (error) {
        setError('加载候选人列表失败');
        console.error('Error fetching candidates:', error);
      } finally {
        setLoading('candidates', false);
      }
    };

    fetchCandidates();
  }, [setCandidates, setLoading, setError]);

  // 处理新建候选人
  const handleCreateCandidate = async () => {
    if (!newCandidateName.trim()) return;

    try {
      setLoading('candidates', true);
      const response = await candidateApi.create({ name: newCandidateName.trim() });
      setCandidates([...candidates, response.data.candidate]);
      setNewCandidateName('');
      setOpen(false);
    } catch (error) {
      setError('创建候选人失败');
      console.error('Error creating candidate:', error);
    } finally {
      setLoading('candidates', false);
    }
  };

  // 处理删除候选人
  const handleDeleteCandidate = async (candidateId) => {
    if (!window.confirm('确定要删除这个候选人吗？')) return;

    try {
      setLoading('candidates', true);
      await candidateApi.delete(candidateId);
      setCandidates(candidates.filter(c => c.id !== candidateId));
      if (currentCandidate?.id === candidateId) {
        setCurrentCandidate(null);
      }
    } catch (error) {
      setError('删除候选人失败');
      console.error('Error deleting candidate:', error);
    } finally {
      setLoading('candidates', false);
    }
  };

  return (
    <Box sx={{ width: '100%', maxWidth: 360, bgcolor: 'background.paper' }}>
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography variant="h6" component="div">
          候选人列表
        </Typography>
        <IconButton onClick={() => setOpen(true)} color="primary">
          <AddIcon />
        </IconButton>
      </Box>
      <Divider />
      <List>
        {candidates.map((candidate) => (
          <ListItem
            key={candidate.id}
            secondaryAction={
              <IconButton
                edge="end"
                aria-label="delete"
                onClick={() => handleDeleteCandidate(candidate.id)}
              >
                <DeleteIcon />
              </IconButton>
            }
            disablePadding
          >
            <ListItemButton
              selected={currentCandidate?.id === candidate.id}
              onClick={() => setCurrentCandidate(candidate)}
            >
              <ListItemText primary={candidate.name} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      {/* 新建候选人对话框 */}
      <Dialog open={open} onClose={() => setOpen(false)}>
        <DialogTitle>新建候选人</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="候选人姓名"
            type="text"
            fullWidth
            variant="outlined"
            value={newCandidateName}
            onChange={(e) => setNewCandidateName(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>取消</Button>
          <Button onClick={handleCreateCandidate} variant="contained">
            创建
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default CandidateList; 
