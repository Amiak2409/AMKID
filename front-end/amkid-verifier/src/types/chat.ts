export type Role = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: Role;
  text?: string;
  images?: string[];
  createdAt: number;
}
