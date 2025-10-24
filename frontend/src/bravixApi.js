// src/bravixApi.js
// Bravix Frontend API Utility
// Handles communication with FastAPI backend (Vercel or local)

// 🌐 Dynamic backend selection (Vercel → local fallback)
const API_BASE =
  import.meta.env.VITE_API_URL && import.meta.env.VITE_API_URL.trim() !== ""
    ? `${import.meta.env.VITE_API_URL}/api`
    : "https://braivix.vercel.app/api"; // ✅ Default to deployed backend

// 🔐 Secure header key (must match backend’s FastAPI API key)
const API_KEY =
  import.meta.env.VITE_API_KEY && import.meta.env.VITE_API_KEY.trim() !== ""
    ? import.meta.env.VITE_API_KEY
    : "BRAVIX-DEMO-SECURE-KEY-2025";

// 🧩 Helper – unified fetch response handler
async function handleResponse(res, context) {
  if (!res.ok) {
    const text = await res.text();
    console.error(`❌ ${context} failed (${res.status}):`, text);
    throw new Error(`${context} failed (${res.status})`);
  }
  const json = await res.json();
  console.log(`✅ ${context} response:`, json);
  return json;
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

// 🧠 Analyze parsed data with GPT (financial indicators + AI insight)
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

// 🔍 Health check (verifies backend availability)
export async function checkHealth() {
  const endpoint = `${API_BASE.replace("/api", "")}/api/test-connection`;
  console.log("🔍 Checking backend health:", endpoint);

  try {
    const res = await fetch(endpoint);
    const data = await res.json();
    console.log("💚 Backend health check result:", data);
    return data;
  } catch (err) {
    console.warn("⚠️ Health check failed:", err.message);
    return { status: "offline", error: err.message };
  }
}

// 🧭 Debug info (optional – helps ensure correct API target)
console.log("🌍 Active API base:", API_BASE);
