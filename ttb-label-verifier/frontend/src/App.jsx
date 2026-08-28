// src/api.js or inside a React component
export async function verifyLabel(formData) {
  const API_URL = import.meta.env.VITE_API_BASE_URL ?? import.meta.env.VITE_API_URL ?? "";

  const res = await fetch(`${API_URL}/api/v1/verify`, {
    method: "POST",
    body: formData,
  });

  return await res.json();
}