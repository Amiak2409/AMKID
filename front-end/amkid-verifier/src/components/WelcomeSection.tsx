// WelcomeSection.tsx
import React from "react";

interface WelcomeSectionProps {
  value: string;
  hasSubmitted: boolean;
  isEditing: boolean;
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
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
  const showVoiceButton = Boolean(onToggleVoice);

  return (
    <div className={`question-shell ${hasSubmitted ? "question-shell--pinned" : ""}`}>
      <div className="question-inner">
        {!hasSubmitted && (
          <h1 className="hero-title hero-title--brand">welcome from AMKID</h1>
        )}

        <form className="hero-form" onSubmit={onSubmit}>
          <div className="hero-input-container">
            <input
              type="text"
              className={`hero-input ${
                hasSubmitted && isEditing ? "hero-input--editing" : ""
              }`}
              placeholder={hasSubmitted ? "" : "Type anything to begin…"}
              value={value}
              readOnly={hasSubmitted && !isEditing}
              onChange={!hasSubmitted || isEditing ? onChange : undefined}
            />

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

            {/* МИКРОФОН ВНУТРИ ИНПУТА */}
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
