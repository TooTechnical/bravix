import axios from 'axios';
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

export async function getScore(payload){
  const res = await axios.post(`${API_BASE}/api/score`, payload);
  return res.data;
}

export async function postCsv(file){
  const form = new FormData();
  form.append('file', file);
  const res = await axios.post(`${API_BASE}/api/score-from-csv`, form, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return res.data;
}
