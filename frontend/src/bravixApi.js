// src/bravixApi.js

// ✅ Use Render backend by default, fallback to local for dev
const API_BASE =
  import.meta.env.VITE_API_URL && import.meta.env.VITE_API_URL.trim() !== ""
    ? `${import.meta.env.VITE_API_URL}/api`
    : "https://bravix.onrender.com/api"; // <-- live backend default

// ✅ Secure header key (matches FastAPI's API_KEY)
const API_KEY =
  import.meta.env.VITE_API_KEY && import.meta.env.VITE_API_KEY.trim() !== ""
    ? import.meta.env.VITE_API_KEY
    : "BRAVIX-DEMO-SECURE-KEY-2025";

// 📁 Upload file (PDF, CSV, XLSX, DOCX)
export async function uploadFile(file) {
  const formData = new FormData();
  formData.append("file", file);

  console.log("📤 Uploading file to:", `${API_BASE}/upload`);

  const res = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    headers: {
      "x-api-key": API_KEY,
    },
    body: formData,
  });

  if (!res.ok) {
    const errorText = await res.text();
    console.error("❌ File upload failed:", errorText);
    throw new Error("File upload failed");
  }

  const data = await res.json();
  console.log("✅ File upload response:", data);
  return data;
}

// 🧮 Analyze parsed data with ChatGPT + indicators
export async function analyzeData(parsedData, rawText = "") {
  console.log("🧠 Sending data for AI analysis to:", `${API_BASE}/analyze`);

  const res = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": API_KEY,
    },
    body: JSON.stringify({
      ...parsedData,
      raw_text: rawText || parsedData?.raw_text || "",
    }),
  });

  if (!res.ok) {
    const errorText = await res.text();
    console.error("❌ AI analysis failed:", errorText);
    throw new Error("AI analysis failed");
  }

  const data = await res.json();
  console.log("✅ AI analysis response:", data);
  return data;
}
