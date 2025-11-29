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
  const [isEditing, setIsEditing] = useState(false);

  const { text: assistantText, start: startTyping } = useTypewriter(170);

  // Что сейчас показываем в инпуте
  const displayValue = hasSubmitted
    ? (isEditing ? welcomeInput : submittedQuestion ?? "")
    : welcomeInput;

  // Отправка текста на бэкенд
  const sendConversationTurn = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;

    // Сначала очищаем текст, чтобы панель поняла, что мы в "loading"
    startTyping("");

    const response = await sendChatMessage({ text: trimmed });
    // сюда уже прилетает JSON-строка, которую потом парсит ResponsePanel
    startTyping(response.reply);
  };

  // Сабмит: и первый раз, и при редактировании
  const handleWelcomeSubmit = (event: React.FormEvent) => {
    event.preventDefault();

    const trimmed = welcomeInput.trim();
    if (!trimmed) return;

    if (!hasSubmitted) {
      setHasSubmitted(true);
    }

    setSubmittedQuestion(trimmed);
    setIsEditing(false);

    // плавно перезапускаем панель
    setShowResponseBlock(false);

    setTimeout(() => {
      setShowResponseBlock(true);
      void sendConversationTurn(trimmed);
    }, 550);

    // значение в инпуте можно очистить — сверху всё равно используется submittedQuestion
    setWelcomeInput("");
  };

  // Старт режима редактирования (иконка пера)
  const handleStartEdit = () => {
    if (!submittedQuestion) return;
    setIsEditing(true);
    setWelcomeInput(submittedQuestion);
  };

  // Полный сброс — новая сессия (кнопка "+ New message")
  const handleNewMessage = () => {
    setHasSubmitted(false);
    setSubmittedQuestion(null);
    setWelcomeInput("");
    setShowResponseBlock(false);
    setIsEditing(false);
    startTyping(""); // очистить ответ
  };

  return (
    <div className="app-root">
      <GradientBackground />

      {/* ВЕРХНЕЕ МЕНЮ */}
      <header className="top-nav">
        <div className="top-nav__group">
          <button
            type="button"
            className="nav-pill nav-pill--ghost"
            onClick={() => {
              console.log("Language switch clicked");
            }}
          >
            <span className="nav-pill__icon" aria-hidden="true">
              🌐
            </span>
            <span className="nav-pill__label">EN</span>
          </button>

          <button
            type="button"
            className="nav-pill nav-pill--ghost"
            onClick={() => {
              console.log("Log in clicked");
            }}
          >
            Log in
          </button>

          <button
            type="button"
            className="nav-pill nav-pill--primary"
            onClick={() => {
              console.log("Sign up clicked");
            }}
          >
            Sign up
          </button>
        </div>
      </header>

      <WelcomeSection
        value={displayValue}
        hasSubmitted={hasSubmitted}
        isEditing={isEditing}
        onChange={(e) => setWelcomeInput(e.target.value)}
        onSubmit={handleWelcomeSubmit}
        onStartEdit={handleStartEdit}
      />

      <ResponsePanel
        show={showResponseBlock}
        assistantText={assistantText}
        onNewMessage={handleNewMessage}
      />
    </div>
  );
};

export default App;
