import React, { useEffect, useRef, useState } from "react";
import { sendChatMessage } from "./api/client";

const App: React.FC = () => {
  // Состояние приветственного поля (единственный вопрос)
  const [welcomeInput, setWelcomeInput] = useState("");
  const [hasSubmitted, setHasSubmitted] = useState(false);
  const [submittedQuestion, setSubmittedQuestion] = useState<string | null>(null);

  // Появление блока ответа
  const [showResponseBlock, setShowResponseBlock] = useState(false);

  // Текст ассистента (один блок, не чат)
  const [assistantText, setAssistantText] = useState("");

  // Эффект печати
  const typingIntervalRef = useRef<number | null>(null);

  // Чистим таймер при размонтировании
  useEffect(() => {
    return () => {
      if (typingIntervalRef.current !== null) {
        window.clearInterval(typingIntervalRef.current);
      }
    };
  }, []);

  const startTyping = (fullText: string) => {
    // Останавливаем предыдущий цикл печати, если есть
    if (typingIntervalRef.current !== null) {
      window.clearInterval(typingIntervalRef.current);
      typingIntervalRef.current = null;
    }

    const words = fullText.split(" ").filter(Boolean);
    let index = 0;
    let currentText = "";

    // перед началом печати очищаем блок
    setAssistantText("");

    typingIntervalRef.current = window.setInterval(() => {
      if (index >= words.length) {
        if (typingIntervalRef.current !== null) {
          window.clearInterval(typingIntervalRef.current);
          typingIntervalRef.current = null;
        }
        return;
      }

      currentText = index === 0 ? words[0] : `${currentText} ${words[index]}`;
      index += 1;

      setAssistantText(currentText);
    }, 170); // медленно и "премиально"
  };

  const sendConversationTurn = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;

    // Запрашиваем мок-ответ (без добавления сообщения пользователя в UI)
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

    // Даём полю время "уехать" вверх, затем показываем блок ответа и запускаем мок-анализ
    setTimeout(() => {
      setShowResponseBlock(true);
      sendConversationTurn(trimmed);
    }, 550); // синхронизировано с CSS-анимацией
  };

  // Что показывать в инпуте: до submit — ввод, после — зафиксированный вопрос
  const displayValue = hasSubmitted ? submittedQuestion ?? "" : welcomeInput;

  return (
    <div className="app-root">
      {/* ВЕРХНЕЕ ПОЛЕ ВВОДА (glassmorphism, отдельный блок) */}
      <div className={`question-shell ${hasSubmitted ? "question-shell--pinned" : ""}`}>
        <div className="question-inner">
          {!hasSubmitted && (
            <>
              <div className="hero-pill">Safety &amp; Sentiment Prototype</div>
              <h1 className="hero-title">Welcome</h1>
            </>
          )}

          <form className="hero-form" onSubmit={handleWelcomeSubmit}>
            <input
              type="text"
              className="hero-input hero-input--glass"
              placeholder={hasSubmitted ? "" : "Type anything to begin…"}
              value={displayValue}
              readOnly={hasSubmitted} // после первого вопроса поле только для просмотра
              onChange={
                hasSubmitted
                  ? undefined
                  : (e: React.ChangeEvent<HTMLInputElement>) =>
                      setWelcomeInput(e.target.value)
              }
            />
            {!hasSubmitted && (
              <button type="submit" className="hero-button">
                Start
              </button>
            )}
          </form>
        </div>
      </div>

      {/* ЦЕНТРАЛЬНЫЙ БЛОК ОТВЕТА (glassmorphism, только текст системы) */}
      <div className={`chat-shell ${showResponseBlock ? "chat-shell--visible" : ""}`}>
        <div className="chat-container chat-container--glass">
          <div className="chat-header">
            <div className="chat-header-title">Assistant response</div>
            <div className="chat-header-subtitle">
              Mock analysis only – real models will plug in here later.
            </div>
          </div>

          <main className="chat-main">
            <div className="chat-result">
              {assistantText && <p className="chat-result-text">{assistantText}</p>}
            </div>
          </main>
        </div>
      </div>
    </div>
  );
};

export default App;
