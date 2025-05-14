import { useState } from 'react';
import {
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
} from '@mui/material';
import useStore from '../store/useStore';
import { candidateApi } from '../services/api';

function CandidateSelector() {
  const { candidates, currentCandidate, setCandidates, setCurrentCandidate, setLoading, setError } = useStore();
  const [open, setOpen] = useState(false);
  const [newCandidateName, setNewCandidateName] = useState('');

  // 处理新建候选人
  const handleCreateCandidate = async () => {
    if (!newCandidateName.trim()) return;

    try {
      setLoading('candidates', true);
      const response = await candidateApi.create({ name: newCandidateName.trim() });
      setCandidates([...candidates, response.data.candidate]);
      setCurrentCandidate(response.data.candidate);
      setNewCandidateName('');
      setOpen(false);
    } catch (error) {
      setError('创建候选人失败');
      console.error('Error creating candidate:', error);
    } finally {
      setLoading('candidates', false);
    }
  };

  return (
    <Box sx={{ minWidth: 200, display: 'flex', alignItems: 'center', gap: 2 }}>
      <FormControl fullWidth>
        <InputLabel id="candidate-select-label">选择候选人</InputLabel>
        <Select
          labelId="candidate-select-label"
          id="candidate-select"
          value={currentCandidate?.id || ''}
          label="选择候选人"
          onChange={(e) => {
            const candidate = candidates.find(c => c.id === e.target.value);
            setCurrentCandidate(candidate);
          }}
        >
          {candidates.map((candidate) => (
            <MenuItem key={candidate.id} value={candidate.id}>
              {candidate.name}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
      <Button
        variant="contained"
        onClick={() => setOpen(true)}
        sx={{ whiteSpace: 'nowrap' }}
      >
        新建候选人
      </Button>

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

export default CandidateSelector; 
