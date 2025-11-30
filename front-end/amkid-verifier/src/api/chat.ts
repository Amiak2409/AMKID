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

// 🔐 КЛЮЧ ДЛЯ ТОКЕНА В localStorage
const AUTH_TOKEN_KEY = "amkid_token";

export interface AuthTokenResponse {
  access_token: string;
  token_type: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface SignupRequest {
  name?: string;
  email: string;
  password: string;
}

// ====== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ТОКЕНА ======

export function getAuthToken(): string | null {
  try {
    return localStorage.getItem(AUTH_TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setAuthToken(token: string | null): void {
  try {
    if (token) {
      localStorage.setItem(AUTH_TOKEN_KEY, token);
    } else {
      localStorage.removeItem(AUTH_TOKEN_KEY);
    }
  } catch {
    // в SSR или приватном режиме может упасть — игнорируем
  }
}

export function logout(): void {
  setAuthToken(null);
}

// ====== AUTH: LOGIN / SIGNUP ======

/**
 * Логин. Отправляем email как username,
 * потому что на бэке модель User имеет только username.
 */
export async function login(
  payload: LoginRequest,
): Promise<AuthTokenResponse> {
  const response = await fetch(`${API_BASE_URL}/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      username: payload.email,
      password: payload.password,
    }),
  });

  const text = await response.text().catch(() => "");

  if (!response.ok) {
    let message = text || `Error ${response.status}`;
    try {
      const data = JSON.parse(text);
      if (data?.detail) {
        message =
          typeof data.detail === "string"
            ? data.detail
            : JSON.stringify(data.detail);
      }
    } catch {
      // просто оставляем message как есть
    }
    throw new Error(message);
  }

  const data: AuthTokenResponse = text
    ? JSON.parse(text)
    : { access_token: "", token_type: "" };

  if (!data.access_token) {
    throw new Error("No access token in response");
  }

  // сохраняем токен сразу
  setAuthToken(data.access_token);
  return data;
}

/**
 * Регистрация. Точно так же: email идёт как username.
 * Бэк сразу возвращает access_token.
 */
export async function signup(
  payload: SignupRequest,
): Promise<AuthTokenResponse> {
  const response = await fetch(`${API_BASE_URL}/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      username: payload.email,
      password: payload.password,
    }),
  });

  const text = await response.text().catch(() => "");

  if (!response.ok) {
    let message = text || `Error ${response.status}`;
    try {
      const data = JSON.parse(text);
      if (data?.detail) {
        message =
          typeof data.detail === "string"
            ? data.detail
            : JSON.stringify(data.detail);
      }
    } catch {
      // оставляем message
    }
    throw new Error(message);
  }

  const data: AuthTokenResponse = text
    ? JSON.parse(text)
    : { access_token: "", token_type: "" };

  if (!data.access_token) {
    throw new Error("No access token in response");
  }

  setAuthToken(data.access_token);
  return data;
}

// ====== ТИПЫ ДЛЯ ИСТОРИИ НА БЭКЕНДЕ ======

export interface ServerHistoryEntry {
  id: string;
  question: string;
  raw_response: string;
  created_at: string;
  kind?: "text" | "image";
}

// ====== РАБОТА С ИСТОРИЕЙ НА БЭКЕНДЕ ======

export async function fetchHistory(): Promise<ServerHistoryEntry[]> {
  const token = getAuthToken();
  if (!token) {
    return [];
  }

  const response = await fetch(`${API_BASE_URL}/history`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  });

  const text = await response.text().catch(() => "");

  if (!response.ok) {
    let message = text || `Error ${response.status}`;
    try {
      const data = JSON.parse(text);
      if (data?.detail) {
        message =
          typeof data.detail === "string"
            ? data.detail
            : JSON.stringify(data.detail);
      }
    } catch {
      // ignore
    }
    throw new Error(message);
  }

  if (!text) return [];

  try {
    const data = JSON.parse(text);
    if (Array.isArray(data)) {
      return data as ServerHistoryEntry[];
    }
    return [];
  } catch {
    return [];
  }
}

export async function deleteHistoryItem(id: string): Promise<void> {
  const token = getAuthToken();
  if (!token) return;

  const response = await fetch(
    `${API_BASE_URL}/history/${encodeURIComponent(id)}`,
    {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    },
  );

  if (!response.ok) {
    const text = await response.text().catch(() => "");
    let message = text || `Error ${response.status}`;
    try {
      const data = JSON.parse(text);
      if (data?.detail) {
        message =
          typeof data.detail === "string"
            ? data.detail
            : JSON.stringify(data.detail);
      }
    } catch {
      // ignore
    }
    throw new Error(message);
  }
}

export async function clearServerHistory(): Promise<void> {
  const token = getAuthToken();
  if (!token) return;

  const response = await fetch(`${API_BASE_URL}/history`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const text = await response.text().catch(() => "");
    let message = text || `Error ${response.status}`;
    try {
      const data = JSON.parse(text);
      if (data?.detail) {
        message =
          typeof data.detail === "string"
            ? data.detail
            : JSON.stringify(data.detail);
      }
    } catch {
      // ignore
    }
    throw new Error(message);
  }
}

// ====== АНАЛИЗ ТЕКСТА ======

export async function sendChatMessage(
  payload: ChatRequest,
): Promise<ChatResponse> {
  const token = getAuthToken();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}/analyze-text`, {
    method: "POST",
    headers,
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

  // по умолчанию — весь JSON ответа
  return { reply: JSON.stringify(data, null, 2) };
}

// ====== АНАЛИЗ ИЗОБРАЖЕНИЯ ======

export async function sendImageMessage(
  file: File,
): Promise<ImageChatResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const token = getAuthToken();

  const headers: HeadersInit = {};
  if (token) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}/analyze-image`, {
    method: "POST",
    body: formData,
    headers,
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
