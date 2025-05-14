import { create } from 'zustand';

const useStore = create((set) => ({
  // 候选人相关状态
  currentCandidate: null,
  candidates: [],
  setCurrentCandidate: (candidate) => set({ currentCandidate: candidate }),
  setCandidates: (candidates) => set({ candidates }),

  // 题目相关状态
  problems: [],
  setProblems: (problems) => set({ problems }),

  // Tab 相关状态
  tabs: [],
  activeTabId: null,
  setTabs: (tabs) => set({ tabs }),
  setActiveTabId: (tabId) => set({ activeTabId: tabId }),
  addTab: (tab) => set((state) => ({ 
    tabs: [...state.tabs, tab],
    activeTabId: tab.id 
  })),
  removeTab: (tabId) => set((state) => ({
    tabs: state.tabs.filter(tab => tab.id !== tabId),
    activeTabId: state.activeTabId === tabId 
      ? (state.tabs.length > 1 ? state.tabs[0].id : null)
      : state.activeTabId
  })),

  // 代码编辑器状态
  editorStates: {},
  setEditorState: (tabId, state) => set((store) => ({
    editorStates: {
      ...store.editorStates,
      [tabId]: state
    }
  })),

  // 加载状态
  loading: {
    candidates: false,
    problems: false,
    submission: false,
    llmReview: false
  },
  setLoading: (key, value) => set((state) => ({
    loading: {
      ...state.loading,
      [key]: value
    }
  })),

  // 错误状态
  error: null,
  setError: (error) => set({ error })
}));

export default useStore; 
