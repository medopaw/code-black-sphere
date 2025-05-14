import React, { useState, useEffect } from 'react';
import { Box, Tabs, Tab, IconButton } from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import CloseIcon from '@mui/icons-material/Close';
import ProblemTab from './ProblemTab';
import ProblemSelectionDialog from './ProblemSelectionDialog';
import { getCandidateTabs, addCandidateTab, removeCandidateTab } from '../services/problemService';

const TabContainer = ({ candidateId, onTabChange }) => {
  const [tabs, setTabs] = useState([]);
  const [activeTab, setActiveTab] = useState(0);
  const [dialogOpen, setDialogOpen] = useState(false);

  useEffect(() => {
    const fetchTabs = async () => {
      if (candidateId) {
        try {
          const data = await getCandidateTabs(candidateId);
          setTabs(data);
          if (data.length > 0) {
            setActiveTab(0);
          }
        } catch (error) {
          console.error('Error fetching candidate tabs:', error);
        }
      }
    };

    fetchTabs();
  }, [candidateId]);

  const handleAddTab = () => {
    setDialogOpen(true);
  };

  const handleCloseTab = async (event, tabIndex) => {
    event.stopPropagation();
    const tabToRemove = tabs[tabIndex];
    
    try {
      await removeCandidateTab(candidateId, tabToRemove.problemId);
      const newTabs = tabs.filter((_, index) => index !== tabIndex);
      setTabs(newTabs);
      
      // 如果关闭的是当前激活的 tab，需要更新激活的 tab
      if (tabIndex === activeTab) {
        setActiveTab(Math.min(activeTab, newTabs.length - 1));
      } else if (tabIndex < activeTab) {
        setActiveTab(activeTab - 1);
      }
    } catch (error) {
      console.error('Error removing tab:', error);
    }
  };

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
    if (onTabChange) {
      onTabChange(tabs[newValue]);
    }
  };

  const handleProblemSelect = async (problem) => {
    try {
      await addCandidateTab(candidateId, problem.id);
      const newTab = {
        problemId: problem.id,
        title: problem.title,
      };
      setTabs([...tabs, newTab]);
      setActiveTab(tabs.length);
    } catch (error) {
      console.error('Error adding new tab:', error);
    }
  };

  return (
    <Box sx={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ borderBottom: 1, borderColor: 'divider', display: 'flex', alignItems: 'center' }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          variant="scrollable"
          scrollButtons="auto"
          sx={{ flexGrow: 1 }}
        >
          {tabs.map((tab, index) => (
            <Tab
              key={index}
              label={
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  {tab.title}
                  {tabs.length > 1 && (
                    <IconButton
                      size="small"
                      onClick={(e) => handleCloseTab(e, index)}
                      sx={{ ml: 1 }}
                    >
                      <CloseIcon fontSize="small" />
                    </IconButton>
                  )}
                </Box>
              }
            />
          ))}
        </Tabs>
        <IconButton onClick={handleAddTab} sx={{ ml: 1 }}>
          <AddIcon />
        </IconButton>
      </Box>
      <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
        {tabs.map((tab, index) => (
          <Box
            key={index}
            sx={{
              display: index === activeTab ? 'block' : 'none',
              height: '100%'
            }}
          >
            <ProblemTab
              candidateId={candidateId}
              problemId={tab.problemId}
            />
          </Box>
        ))}
      </Box>
      <ProblemSelectionDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onSelect={handleProblemSelect}
      />
    </Box>
  );
};

export default TabContainer; 
