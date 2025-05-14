import { request } from './request';

export const getSettings = async () => {
  const response = await request.get('/api/settings');
  return response.data;
};

export const updateSetting = async (key, value) => {
  const response = await request.put('/api/settings', {
    key,
    value
  });
  return response.data;
}; 
