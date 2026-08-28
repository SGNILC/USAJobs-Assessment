// src/api.js or inside a React component
export async function verifyLabel(formData) {
  // 1. Vite reads the environment variable at build time
  const API_URL = import.meta.env.VITE_API_URL;

  // 2. Fetch sends the request to your Hugging Face backend
  const res = await fetch(`${API_URL}/api/v1/verify`, {
    method: "POST",
    body: formData,
  });

  return await res.json();
}