export interface ChatRequest {
  text: string;
}

export interface ChatResponse {
  reply: string;
}

export async function sendChatMessage(_: ChatRequest): Promise<ChatResponse> {
  await new Promise((resolve) => setTimeout(resolve, 400));

  return {
    reply:
      "Thanks for your message. I’m preparing a mock analysis showing sentiment, tone, potential risks (toxicity / sexism / safety) and suggestions on how to rephrase your text so it stays safe and clear while keeping your style. In the real version, this panel will highlight risky fragments, explain why they can be a problem, and propose friendly, non-toxic alternatives.",
  };
}
