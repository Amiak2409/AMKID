// src/api/chat.ts

export interface ChatRequest {
  text: string;
}

export interface ChatResponse {
  reply: string;
}

const API_BASE_URL =
  import.meta.env.VITE_API_URL ?? "http://localhost:8000";

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

  // твой TextAnalyzeResponse возвращает что-то вроде data.reply
  if (typeof data.reply === "string") {
    return { reply: data.reply };
  }

  return { reply: JSON.stringify(data, null, 2) };
}
