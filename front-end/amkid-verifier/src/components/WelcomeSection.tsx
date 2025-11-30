// WelcomeSection.tsx
import React, { useRef, useLayoutEffect } from "react";

interface WelcomeSectionProps {
  value: string;
  hasSubmitted: boolean;
  isEditing: boolean;
  onChange: (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => void;
  onSubmit: (event: React.FormEvent) => void;
  onStartEdit: () => void;

  // ГОЛОС
  onToggleVoice?: () => void;
  isListening?: boolean;
  isSpeechAvailable?: boolean;
  currentLangCode?: "ru-RU" | "en-US";
}

export const WelcomeSection: React.FC<WelcomeSectionProps> = ({
  value,
  hasSubmitted,
  isEditing,
  onChange,
  onSubmit,
  onStartEdit,
  onToggleVoice,
  isListening,
  isSpeechAvailable,
  currentLangCode,
}) => {
  // 🎙 Микрофон показываем только до первого сабмита
  const showVoiceButton = Boolean(onToggleVoice) && !hasSubmitted;

  // textarea используется только ПОСЛЕ сабмита (когда блок наверху)
  const textAreaRef = useRef<HTMLTextAreaElement | null>(null);
  const formRef = useRef<HTMLFormElement | null>(null);

  // 🔁 Авто-высота textarea после отправки: до ~3 строк, дальше scroll
  useLayoutEffect(() => {
    if (!hasSubmitted) return;
    const el = textAreaRef.current;
    if (!el) return;

    // Сбрасываем и считаем реальную высоту
    el.style.height = "auto";

    const maxHeight = 90; // ~3 строки при твоём font-size/line-height
    const scrollHeight = el.scrollHeight;
    const newHeight = Math.min(scrollHeight, maxHeight);

    el.style.height = `${newHeight}px`;
    el.style.overflowY = scrollHeight > maxHeight ? "auto" : "hidden";
  }, [hasSubmitted, value]);

  // ⌨️ В режиме редактирования наверху:
  // Enter (без Shift) = отправка, Shift+Enter при желании можно включить позже
  const handleKeyDown: React.KeyboardEventHandler<HTMLTextAreaElement> = (
    event,
  ) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (formRef.current) {
        formRef.current.requestSubmit();
      }
    }
  };

  return (
    <div className={`question-shell ${hasSubmitted ? "question-shell--pinned" : ""}`}>
      <div className="question-inner">
        {!hasSubmitted && (
          <h1 className="hero-title hero-title--brand">welcome from AMKID</h1>
        )}

        <form
          className="hero-form"
          onSubmit={onSubmit}
          ref={formRef}
        >
          <div className="hero-input-container">
            {/* 
              ДО отправки: обычный однострочный <input>,
              текст идёт в одну строку и прокручивается горизонтально
            */}
            {!hasSubmitted && (
              <input
                type="text"
                className="hero-input"
                placeholder="Type anything to begin…"
                value={value}
                readOnly={false}
                onChange={onChange}
              />
            )}

            {/* 
              ПОСЛЕ отправки (когда блок наверху): textarea,
              фиксированная ширина, высота зависит от контента (до 3 строк)
            */}
            {hasSubmitted && (
              <textarea
                ref={textAreaRef}
                className={`hero-input ${
                  hasSubmitted && isEditing ? "hero-input--editing" : ""
                }`}
                placeholder=""
                value={value}
                readOnly={!isEditing}
                onChange={isEditing ? onChange : undefined}
                onKeyDown={isEditing ? handleKeyDown : undefined}
                rows={1} // стартуем с одной строки, дальше растим через useLayoutEffect
              />
            )}

            {/* КНОПКА РЕДАКТА ПОСЛЕ ОТПРАВКИ */}
            {hasSubmitted && !isEditing && (
              <button
                type="button"
                className="edit-pill"
                onClick={onStartEdit}
                aria-label="Edit message"
              >
                <span className="edit-pill__icon" aria-hidden="true">
                  ✎
                </span>
                <span className="edit-pill__label">Edit message</span>
              </button>
            )}

            {/* МИКРОФОН ВНУТРИ ИНПУТА — только в приветственном состоянии */}
            {showVoiceButton && (
              <button
                type="button"
                className={[
                  "voice-button",
                  isListening ? "voice-button--active" : "",
                  isSpeechAvailable === false ? "voice-button--disabled" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                onClick={
                  isSpeechAvailable === false || !onToggleVoice ? undefined : onToggleVoice
                }
                aria-label={
                  isSpeechAvailable === false
                    ? "Voice input is not supported in this browser"
                    : isListening
                    ? "Stop voice input"
                    : "Start voice input"
                }
              >
                <span className="voice-button__icon" aria-hidden="true">
                  🎤
                </span>
              </button>
            )}
          </div>

          {/* Стартовая стрелка — только до первого сабмита */}
          {!hasSubmitted && (
            <button type="submit" className="hero-button" aria-label="Start">
              <span aria-hidden="true">➜</span>
            </button>
          )}
        </form>

        {/* СТАТУС “СЕЙЧАС СЛУШАЮ” ПОД ИНПУТОМ */}
        {isListening && (
          <div className="voice-status">
            <span className="voice-status__dot" />
            <span className="voice-status__label">
              Listening…
              {currentLangCode && (
                <span className="voice-status__lang">
                  {currentLangCode === "ru-RU" ? "RU" : "EN"}
                </span>
              )}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
