import React, { useState } from "react";
import { sendChatMessage } from "./api/chat";
import { useTypewriter } from "./hooks/useTypewriter";
import { GradientBackground } from "./components/GradientBackground";
import { WelcomeSection } from "./components/WelcomeSection";
import { ResponsePanel } from "./components/ResponcePanel";

const App: React.FC = () => {
  const [welcomeInput, setWelcomeInput] = useState("");
  const [hasSubmitted, setHasSubmitted] = useState(false);
  const [submittedQuestion, setSubmittedQuestion] = useState<string | null>(null);
  const [showResponseBlock, setShowResponseBlock] = useState(false);

  const { text: assistantText, start: startTyping } = useTypewriter(170);

  const displayValue = hasSubmitted ? submittedQuestion ?? "" : welcomeInput;

  const sendConversationTurn = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;

    const response = await sendChatMessage({ text: trimmed });
    startTyping(response.reply);
  };

  const handleWelcomeSubmit = (event: React.FormEvent) => {
    event.preventDefault();

    const trimmed = welcomeInput.trim();
    if (!trimmed || hasSubmitted) return;

    setHasSubmitted(true);
    setSubmittedQuestion(trimmed);
    setWelcomeInput("");

    setTimeout(() => {
      setShowResponseBlock(true);
      void sendConversationTurn(trimmed);
    }, 550);
  };

  return (
    <div className="app-root">
      <GradientBackground />

      <WelcomeSection
        value={displayValue}
        hasSubmitted={hasSubmitted}
        onChange={(e) => setWelcomeInput(e.target.value)}
        onSubmit={handleWelcomeSubmit}
      />

      <ResponsePanel show={showResponseBlock} assistantText={assistantText} />
    </div>
  );
};

export default App;
