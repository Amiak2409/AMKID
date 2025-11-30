// WelcomeSection.tsx
import React, {
  useRef,
  useLayoutEffect,
  useEffect,
  useState,
} from "react";

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

  // 📷 КАРТИНКА
  attachedImage?: File | null;
  onImageChange?: (file: File | null) => void;
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
  attachedImage,
  onImageChange,
}) => {
  const hasImage = Boolean(attachedImage);

  // 🎙 Микрофон показываем только до первого сабмита и пока нет картинки
  const showVoiceButton = Boolean(onToggleVoice) && !hasSubmitted && !hasImage;

  // textarea используется только ПОСЛЕ сабмита (когда блок наверху)
  const textAreaRef = useRef<HTMLTextAreaElement | null>(null);
  const formRef = useRef<HTMLFormElement | null>(null);

  // hidden input под картинку
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // превью (URL) для маленькой плашки
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!attachedImage) {
      setPreviewUrl(null);
      return;
    }
    const url = URL.createObjectURL(attachedImage);
    setPreviewUrl(url);
    return () => {
      URL.revokeObjectURL(url);
    };
  }, [attachedImage]);

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
  // Enter (без Shift) = отправка
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

  // 📷 клик по иконке "прикрепить"
  const handleImageButtonClick = () => {
    if (!fileInputRef.current) return;
    fileInputRef.current.click();
  };

  // 📷 выбор файла
  const handleFileChange: React.ChangeEventHandler<HTMLInputElement> = (
    event,
  ) => {
    if (!onImageChange) return;
    const file = event.target.files?.[0] ?? null;

    // можно только одну картинку — просто храним один файл
    onImageChange(file);
  };

  // ❌ удалить картинку
  const handleRemoveImage = () => {
    if (onImageChange) {
      onImageChange(null);
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  // значение поля: если есть картинка — текст визуально не показываем
  const inputValue = hasImage ? "" : value;

  const isTextReadOnly =
    hasImage || (hasSubmitted && !isEditing); // если картинка — всегда запрет текста

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
            {/* Скрытый инпут для картинки */}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              className="image-input-hidden"
              onChange={handleFileChange}
            />

            {/* 
              ДО отправки: обычный однострочный <input>,
              текст идёт в одну строку и прокручивается горизонтально.
              Если прикреплена картинка — поле визуально пустое и readOnly.
            */}
            {!hasSubmitted && (
              <input
                type="text"
                className="hero-input"
                placeholder={
                  hasImage ? "Image attached" : "Type anything to begin…"
                }
                value={inputValue}
                readOnly={isTextReadOnly}
                onChange={
                  isTextReadOnly
                    ? undefined
                    : (onChange as React.ChangeEventHandler<HTMLInputElement>)
                }
              />
            )}

            {/* 
              ПОСЛЕ отправки (когда блок наверху): textarea.
              Если есть картинка — текст не редактируем и не показываем.
            */}
            {hasSubmitted && (
              <textarea
                ref={textAreaRef}
                className={`hero-input ${
                  hasSubmitted && isEditing ? "hero-input--editing" : ""
                }`}
                placeholder={hasImage ? "Image attached" : ""}
                value={inputValue}
                readOnly={isTextReadOnly}
                onChange={
                  isTextReadOnly
                    ? undefined
                    : (onChange as React.ChangeEventHandler<HTMLTextAreaElement>)
                }
                onKeyDown={isTextReadOnly ? undefined : handleKeyDown}
                rows={1} // стартуем с одной строки, дальше растим через useLayoutEffect
              />
            )}

            {/* 📷 КНОПКА ПРИКРЕПИТЬ КАРТИНКУ (только до первого сабмита) */}
            {!hasSubmitted && (
              <button
                type="button"
                className={[
                  "image-button",
                  hasImage ? "image-button--active" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                onClick={handleImageButtonClick}
                aria-label={hasImage ? "Change attached image" : "Attach image"}
              >
                <span className="image-button__icon" aria-hidden="true">
                  📷
                </span>
              </button>
            )}

            {/* Плашка с превью прикреплённой картинки */}
            {hasImage && (
              <button
                type="button"
                className="image-pill"
                onClick={handleRemoveImage}
                aria-label="Remove attached image"
              >
                {previewUrl && (
                  <span className="image-pill__thumb">
                    <img src={previewUrl} alt="Attached" />
                  </span>
                )}
                <span className="image-pill__name">
                  {attachedImage?.name ?? "Image attached"}
                </span>
                <span className="image-pill__remove" aria-hidden="true">
                  ✕
                </span>
              </button>
            )}

            {/* КНОПКА РЕДАКТА ПОСЛЕ ОТПРАВКИ (только для текстовых сообщений) */}
            {hasSubmitted && !isEditing && !hasImage && (
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

            {/* МИКРОФОН ВНУТРИ ИНПУТА — только в приветственном состоянии и без картинки */}
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
