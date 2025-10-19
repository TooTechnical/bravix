// src/bravixApi.js
const API_BASE = "http://127.0.0.1:8000/api"; // local backend
const API_KEY = "BRAVIX-DEMO-SECURE-KEY-2025"; // must match backend key

// 📁 Upload file (PDF, CSV, XLSX, DOCX)
export async function uploadFile(file) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    headers: {
      "x-api-key": API_KEY
    },
    body: formData,
  });

  if (!res.ok) throw new Error("File upload failed");
  return await res.json();
}

// 🧮 Analyze parsed data with ChatGPT + indicators
export async function analyzeData(parsedData, rawText = "") {
  const res = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": API_KEY,
    },
    body: JSON.stringify({ ...parsedData, raw_text: rawText }),
  });

  if (!res.ok) throw new Error("AI analysis failed");
  return await res.json();
}
