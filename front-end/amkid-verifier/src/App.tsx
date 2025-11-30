// App.tsx
import React, { useState, useEffect, useRef } from "react";
import { sendChatMessage } from "./api/chat";
import { useTypewriter } from "./hooks/useTypewriter";
import { GradientBackground } from "./components/GradientBackground";
import { WelcomeSection } from "./components/WelcomeSection";
import { ResponsePanel } from "./components/ResponcePanel";
import { AuthModal } from "./components/AuthModal";
import { HistoryAside } from "./components/HistoryAside";

// простая утилита для доступа к SpeechRecognition
type SpeechRecognitionInstance = any;
type SpeechRecognitionConstructor = new () => SpeechRecognitionInstance;

const getSpeechRecognition = (): SpeechRecognitionConstructor | null => {
  if (typeof window === "undefined") return null;
  const w = window as any;
  return w.SpeechRecognition || w.webkitSpeechRecognition || null;
};

// автоопределение RU / EN
const detectLangFromText = (text: string): "ru-RU" | "en-US" => {
  // если есть кириллица — считаем, что RU
  if (/[а-яА-ЯёЁ]/.test(text)) return "ru-RU";

  // если язык браузера русский — тоже RU
  if (
    typeof navigator !== "undefined" &&
    navigator.language &&
    navigator.language.toLowerCase().startsWith("ru")
  ) {
    return "ru-RU";
  }

  // иначе дефолт — EN
  return "en-US";
};

type ModalMode = "help" | "login" | "signup" | null;

// то, что будем хранить в истории (готово под базу)
interface HistoryEntry {
  id: string;
  question: string;
  rawResponse: string; // JSON-строка анализа или просто текст
  createdAt: string; // ISO timestamp
}

const HISTORY_STORAGE_KEY = "amkid_history_v1";

const App: React.FC = () => {
  const [welcomeInput, setWelcomeInput] = useState("");
  const [hasSubmitted, setHasSubmitted] = useState(false);
  const [submittedQuestion, setSubmittedQuestion] = useState<string | null>(null);
  const [showResponseBlock, setShowResponseBlock] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  const { text: assistantText, start: startTyping } = useTypewriter(170);

  // ИСТОРИЯ
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [selectedHistoryId, setSelectedHistoryId] = useState<string | null>(null);

  // ГОЛОС
  const [isListening, setIsListening] = useState(false);
  const [isSpeechAvailable, setIsSpeechAvailable] = useState<boolean | undefined>(undefined);
  const [currentLang, setCurrentLang] = useState<"ru-RU" | "en-US" | null>(null);
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);

  // МОДАЛКА (Help / Login / Sign up)
  const [modalMode, setModalMode] = useState<ModalMode>(null);

  const handleOpenHelp = () => setModalMode("help");
  const handleOpenLogin = () => setModalMode("login");
  const handleOpenSignup = () => setModalMode("signup");
  const handleCloseModal = () => setModalMode(null);

  // Что сейчас показываем в инпуте
  const displayValue = hasSubmitted
    ? isEditing
      ? welcomeInput
      : submittedQuestion ?? ""
    : welcomeInput;

  // ИНИЦИАЛИЗАЦИЯ SpeechRecognition
  useEffect(() => {
    const SR = getSpeechRecognition();
    if (!SR) {
      setIsSpeechAvailable(false);
      return;
    }

    setIsSpeechAvailable(true);

    const recognition = new SR();
    recognition.interimResults = false;
    recognition.continuous = false;

    recognition.onresult = (event: any) => {
      const result = event.results?.[0];
      if (!result) return;
      const transcript = result[0]?.transcript ?? "";
      if (!transcript) return;

      setWelcomeInput((prev) => {
        const base = prev.trim();
        return (base ? base + " " : "") + transcript.trim();
      });
    };

    recognition.onend = () => {
      setIsListening(false);
      setCurrentLang(null);
    };

    recognition.onerror = () => {
      setIsListening(false);
      setCurrentLang(null);
    };

    recognitionRef.current = recognition;

    return () => {
      try {
        recognition.stop();
      } catch {
        // ignore
      }
    };
  }, []);

  // ЗАГРУЗКА истории из localStorage при старте
  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      const raw = window.localStorage.getItem(HISTORY_STORAGE_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        setHistory(parsed);
      }
    } catch (error) {
      console.error("Failed to read history from localStorage", error);
    }
  }, []);

  // сохранение истории в localStorage
  const persistHistory = (entries: HistoryEntry[]) => {
    if (typeof window === "undefined") return;
    try {
      window.localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(entries));
    } catch (error) {
      console.error("Failed to save history to localStorage", error);
    }
  };

  // добавить новый элемент в историю (вызов после успешного анализа)
  const handleSaveHistoryEntry = (question: string, rawResponse: string) => {
    setHistory((prev) => {
      const newEntry: HistoryEntry = {
        id:
          typeof crypto !== "undefined" && "randomUUID" in crypto
            ? crypto.randomUUID()
            : `${Date.now()}-${Math.random().toString(16).slice(2)}`,
        question,
        rawResponse,
        createdAt: new Date().toISOString(),
      };

      // ограничим историю, например, 50 последними
      const next = [newEntry, ...prev].slice(0, 50);
      persistHistory(next);
      return next;
    });
  };

  const handleDeleteHistoryEntry = (id: string) => {
    setHistory((prev) => {
      const next = prev.filter((item) => item.id !== id);
      persistHistory(next);
      return next;
    });

    setSelectedHistoryId((current) => (current === id ? null : current));
  };

  const handleClearHistory = () => {
    setHistory([]);
    setSelectedHistoryId(null);
    if (typeof window !== "undefined") {
      try {
        window.localStorage.removeItem(HISTORY_STORAGE_KEY);
      } catch (error) {
        console.error("Failed to clear history from localStorage", error);
      }
    }
  };

  // выбор элемента истории → восстановить вопрос и анализ без нового запроса
  const handleSelectHistoryEntry = (entry: HistoryEntry) => {
    // остановим микрофон, если активен
    if (isListening && recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {
        // ignore
      }
      setIsListening(false);
      setCurrentLang(null);
    }

    if (!hasSubmitted) {
      setHasSubmitted(true);
    }

    setSubmittedQuestion(entry.question);
    setIsEditing(false);
    setShowResponseBlock(true);
    setWelcomeInput(""); // редактирование только через Edit
    setSelectedHistoryId(entry.id);

    // показываем сохранённый ответ (JSON-строка),
    // ResponsePanel сам его распарсит и отрисует метрики
    startTyping(entry.rawResponse);
  };

  // Отправка текста на бэкенд
  const sendConversationTurn = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;

    // Сначала очищаем текст, чтобы панель поняла, что мы в "loading"
    startTyping("");

    const response = await sendChatMessage({ text: trimmed });
    // сюда уже прилетает JSON-строка, которую потом парсит ResponsePanel
    startTyping(response.reply);

    // Сохраняем в историю (готово для потом подмены на запись в БД)
    handleSaveHistoryEntry(trimmed, response.reply);
  };

  // Сабмит: и первый раз, и при редактировании
  const handleWelcomeSubmit = (event: React.FormEvent) => {
    event.preventDefault();

    const trimmed = welcomeInput.trim();
    if (!trimmed) return;

    // если микрофон ещё слушает — остановим
    if (isListening && recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {
        // ignore
      }
      setIsListening(false);
      setCurrentLang(null);
    }

    if (!hasSubmitted) {
      setHasSubmitted(true);
    }

    setSubmittedQuestion(trimmed);
    setIsEditing(false);

    // при вводе нового текста мы НЕ считаем, что выбран какой-то элемент истории
    setSelectedHistoryId(null);

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

  // Включение / выключение голосового ввода
  const handleToggleVoice = () => {
    if (!isSpeechAvailable || !recognitionRef.current) return;
    const recognition = recognitionRef.current;

    // если уже слушает — стоп
    if (isListening) {
      try {
        recognition.stop();
      } catch {
        // ignore
      }
      setIsListening(false);
      setCurrentLang(null);
      return;
    }

    // если текст уже отправлен — переходим в режим редактирования
    if (hasSubmitted && !isEditing && submittedQuestion) {
      setIsEditing(true);
      setWelcomeInput(submittedQuestion);
    }

    // выбираем язык на основе текущего текста / языка браузера
    const lang = detectLangFromText(displayValue || "");
    recognition.lang = lang;
    setCurrentLang(lang);

    try {
      recognition.start();
      setIsListening(true);
    } catch (err) {
      console.error("Speech recognition start error:", err);
      setIsListening(false);
      setCurrentLang(null);
    }
  };

  // Полный сброс — новая сессия (кнопка "+ New message")
  const handleNewMessage = () => {
    // на всякий случай останавливаем микрофон
    if (isListening && recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {
        // ignore
      }
    }

    setHasSubmitted(false);
    setSubmittedQuestion(null);
    setWelcomeInput("");
    setShowResponseBlock(false);
    setIsEditing(false);
    setIsListening(false);
    setCurrentLang(null);
    setSelectedHistoryId(null);
    startTyping(""); // очистить ответ
  };

  return (
    <div className="app-root">
      <GradientBackground />

      {/* КНОПКА ПОМОЩИ СЛЕВА СВЕРХУ */}
      <button
        type="button"
        className="help-button"
        onClick={handleOpenHelp}
        aria-label="What is this website for?"
      >
        <span className="help-button__icon">?</span>
      </button>

      {/* ВЕРХНЕЕ МЕНЮ СПРАВА */}
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
            onClick={handleOpenLogin}
          >
            Log in
          </button>

          <button
            type="button"
            className="nav-pill nav-pill--primary"
            onClick={handleOpenSignup}
          >
            Sign up
          </button>
        </div>
      </header>

      {/* СПРАВА ПОД КНОПКАМИ — ИСТОРИЯ */}
      <HistoryAside
        items={history}
        selectedId={selectedHistoryId}
        onSelect={handleSelectHistoryEntry}
        onDeleteEntry={handleDeleteHistoryEntry}
        onClearAll={handleClearHistory}
      />

      <WelcomeSection
        value={displayValue}
        hasSubmitted={hasSubmitted}
        isEditing={isEditing}
        onChange={(e) => setWelcomeInput(e.target.value)}
        onSubmit={handleWelcomeSubmit}
        onStartEdit={handleStartEdit}
        // голос
        onToggleVoice={handleToggleVoice}
        isListening={isListening}
        isSpeechAvailable={isSpeechAvailable}
        currentLangCode={currentLang ?? undefined}
      />

      <ResponsePanel
        show={showResponseBlock}
        assistantText={assistantText}
        onNewMessage={handleNewMessage}
      />

      {/* ГЛАВНОЕ СТЕКЛЯННОЕ МОДАЛЬНОЕ ОКНО (Help / Login / Sign up) */}
      {modalMode !== null && (
        <AuthModal
          mode={modalMode}
          onClose={handleCloseModal}
          onChangeMode={(mode) => setModalMode(mode)}
        />
      )}
    </div>
  );
};

export default App;
