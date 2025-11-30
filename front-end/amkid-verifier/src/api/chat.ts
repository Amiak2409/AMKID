// src/api/chat.ts

export interface ChatRequest {
  text: string;
}

export interface ChatResponse {
  reply: string;
}

export interface ImageChatResponse {
  reply: string;
}

const API_BASE_URL =
  import.meta.env.VITE_API_URL ?? "http://localhost:8000";

// ТЕКСТ
export async function sendChatMessage(payload: ChatRequest): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/analyze-text`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    // FastAPI ждёт "content", а не "text"
    body: JSON.stringify({ content: payload.text }),
  });

  if (!response.ok) {
    const errText = await response.text().catch(() => "");
    throw new Error(errText || `Error ${response.status}`);
  }

  const data = await response.json();

  if (typeof data.reply === "string") {
    return { reply: data.reply };
  }

  return { reply: JSON.stringify(data, null, 2) };
}

// 📷 ИЗОБРАЖЕНИЕ
export async function sendImageMessage(file: File): Promise<ImageChatResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/analyze-image`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errText = await response.text().catch(() => "");
    throw new Error(errText || `Error ${response.status}`);
  }

  const data = await response.json();

  // если бэк тоже отдаёт поле reply
  if (typeof data.reply === "string") {
    return { reply: data.reply };
  }

  return { reply: JSON.stringify(data, null, 2) };
}
