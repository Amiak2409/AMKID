export interface ChatRequest {
  text?: string;
  imageCount?: number;
}

export interface ChatResponse {
  reply: string;
}

/**
 * Placeholder API client for future backend integration.
 * For now it just resolves with a static placeholder reply after a short delay.
 */
export async function sendChatMessage(_: ChatRequest): Promise<ChatResponse> {
  // Fake network latency
  await new Promise((resolve) => setTimeout(resolve, 400));

  return {
  reply:
    "Thanks for your message. I’m preparing a mock analysis of your text across several dimensions: " +
    "sentiment (overall emotional tone), toxicity, sexism and potential safety signals. " +
    "In the full version of this app, this panel will display real model outputs with scores, labels " +
    "and confidence levels for each category, together with short, human-readable explanations. " +
    "\n\n" +
    "You’ll be able to see how positive, neutral or negative your text sounds, which specific phrases " +
    "may be perceived as aggressive or harmful, and where subtle biased or sexist patterns might appear. " +
    "Instead of just showing raw numbers, the system will break the analysis down into simple insights, " +
    "so you can quickly understand what is happening and why the model made a certain decision. " +
    "\n\n" +
    "The final version will also highlight risky or ambiguous fragments directly in your text, " +
    "drawing attention to places that might trigger content filters or violate platform guidelines. " +
    "For each detected issue, the assistant will suggest alternative phrasings that keep your original " +
    "meaning but make the message clearer, safer and more inclusive. " +
    "\n\n" +
    "Over time, this panel can evolve into a small dashboard for your writing: tracking how your style " +
    "changes, which types of risks appear most often, and how your overall sentiment profile shifts " +
    "across different messages. You’ll be able to compare multiple drafts, experiment with tone and " +
    "formality, and instantly see how these changes influence the analysis. " +
    "\n\n" +
    "Right now, you are seeing only a static placeholder preview, but the interaction flow will stay the same: " +
    "you enter text, the system processes it, and this space becomes a focused, distraction-free summary " +
    "of what the model has understood from your writing. Think of it as a live, AI-powered report page " +
    "designed specifically for your message, not a generic chat history. " +
    "\n\n" +
    "In short, this area is reserved for a future version of the assistant that behaves less like a chatbot " +
    "and more like an analytical tool: precise, visual and centered around your text rather than the conversation.",
};
}
