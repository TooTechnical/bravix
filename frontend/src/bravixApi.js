// src/bravixApi.js

// 🌐 Dynamic backend selection — prefers Vercel, falls back to local
const API_BASE =
  import.meta.env.VITE_API_URL && import.meta.env.VITE_API_URL.trim() !== ""
    ? `${import.meta.env.VITE_API_URL}/api`
    : "https://bravix-api.vercel.app/api"; // ✅ Default to Vercel backend

// 🔐 Secure API Key (matches FastAPI's key)
const API_KEY =
  import.meta.env.VITE_API_KEY && import.meta.env.VITE_API_KEY.trim() !== ""
    ? import.meta.env.VITE_API_KEY
    : "BRAVIX-DEMO-SECURE-KEY-2025";

// 🧩 Utility: handle response safely
async function handleResponse(res, context) {
  if (!res.ok) {
    const errorText = await res.text();
    console.error(`❌ ${context} failed:`, errorText);
    throw new Error(`${context} failed (${res.status})`);
  }
  const data = await res.json();
  console.log(`✅ ${context} response:`, data);
  return data;
}

// 📤 Upload file (PDF, CSV, XLSX, DOCX)
export async function uploadFile(file) {
  if (!file) throw new Error("No file provided for upload.");

  const formData = new FormData();
  formData.append("file", file);

  const endpoint = `${API_BASE}/upload`;
  console.log("📤 Uploading file to:", endpoint);

  try {
    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "x-api-key": API_KEY },
      body: formData,
    });
    return await handleResponse(res, "File upload");
  } catch (err) {
    console.error("🚨 Upload error:", err.message);
    throw err;
  }
}

// 🧠 Analyze parsed data with GPT-based AI and indicators
export async function analyzeData(parsedData, rawText = "") {
  if (!parsedData || typeof parsedData !== "object") {
    throw new Error("Invalid parsed data for AI analysis.");
  }

  const endpoint = `${API_BASE}/analyze`;
  console.log("🧠 Sending data for AI analysis to:", endpoint);

  const payload = {
    ...parsedData,
    raw_text: rawText || parsedData?.raw_text || "",
  };

  try {
    const res = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": API_KEY,
      },
      body: JSON.stringify(payload),
    });
    return await handleResponse(res, "AI analysis");
  } catch (err) {
    console.error("🚨 AI analysis error:", err.message);
    throw err;
  }
}

// 🔍 Optional health check (to verify backend is alive)
export async function checkHealth() {
  const endpoint = `${API_BASE.replace("/api", "")}/health`;
  console.log("🔍 Checking backend health:", endpoint);
  try {
    const res = await fetch(endpoint);
    const data = await res.json();
    console.log("💚 Backend health:", data);
    return data;
  } catch (err) {
    console.warn("⚠️ Health check failed:", err.message);
    return { status: "offline", error: err.message };
  }
}
