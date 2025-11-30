// components/HistoryAside.tsx
import React, { useMemo } from "react";

type HistoryEntry = {
  id: string;
  question: string;
  rawResponse: string;
  createdAt: string,
  kind: "text" | "image";
};

interface HistoryAsideProps {
  items: HistoryEntry[];
  selectedId?: string | null;
  onSelect: (entry: HistoryEntry) => void;
  onDeleteEntry: (id: string) => void;
  onClearAll: () => void;
}

type AiAnalysisPreview = {
  trust_score?: number;
  manipulation_score?: number;
  emotion_intensity?: number;
};

const parseAnalysisPreview = (raw: string): AiAnalysisPreview | null => {
  try {
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object") return null;

    const { trust_score, manipulation_score, emotion_intensity } = parsed as any;

    if (
      typeof trust_score === "number" ||
      typeof manipulation_score === "number" ||
      typeof emotion_intensity === "number"
    ) {
      return { trust_score, manipulation_score, emotion_intensity };
    }
    return null;
  } catch {
    return null;
  }
};

const formatTime = (iso: string): string => {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  });
};

export const HistoryAside: React.FC<HistoryAsideProps> = ({
  items,
  selectedId,
  onSelect,
  onDeleteEntry,
  onClearAll,
}) => {
  const entriesWithPreview = useMemo(
    () =>
      items.map((entry) => ({
        ...entry,
        preview: parseAnalysisPreview(entry.rawResponse),
      })),
    [items],
  );

  return (
    <aside className="history-aside" aria-label="Previous analyses history">
      <div className="glass-panel glass-panel--history">
        <header className="history-header">
          <div className="history-header__title">History</div>
          {items.length > 0 && (
            <button
              type="button"
              className="history-header__clear"
              onClick={onClearAll}
            >
              Clear
            </button>
          )}
        </header>

        <div className="history-body">
          {items.length === 0 ? (
            <div className="history-empty">
              Run your first analysis to see it here.
            </div>
          ) : (
            <ul className="history-list">
              {entriesWithPreview.map((entry) => {
                const isActive = entry.id === selectedId;
                const questionShort =
                  entry.question.length > 80
                    ? entry.question.slice(0, 77) + "…"
                    : entry.question;

                const trust =
                  entry.preview?.trust_score != null
                    ? Math.round(entry.preview.trust_score)
                    : null;
                const manipulation =
                  entry.preview?.manipulation_score != null
                    ? Math.round(entry.preview.manipulation_score * 100)
                    : null;
                const emotion =
                  entry.preview?.emotion_intensity != null
                    ? Math.round(entry.preview.emotion_intensity * 100)
                    : null;

                return (
                  <li key={entry.id} className="history-item-wrapper">
                    <button
                      type="button"
                      className={
                        "history-item" +
                        (isActive ? " history-item--active" : "")
                      }
                      onClick={() => onSelect(entry)}
                    >
                      <div className="history-item__top">
                        <div className="history-item__question">
                          {questionShort || "Untitled message"}
                        </div>
                        <div className="history-item__time">
                          {formatTime(entry.createdAt)}
                        </div>
                      </div>

                      {entry.preview && (
                        <div className="history-item__metrics">
                          {trust != null && (
                            <div className="history-metric">
                              <span className="history-metric__label">
                                Trust
                              </span>
                              <span className="history-metric__value">
                                {trust}%
                              </span>
                            </div>
                          )}
                          {manipulation != null && (
                            <div className="history-metric">
                              <span className="history-metric__label">
                                Manip.
                              </span>
                              <span className="history-metric__value">
                                {manipulation}%
                              </span>
                            </div>
                          )}
                          {emotion != null && (
                            <div className="history-metric">
                              <span className="history-metric__label">
                                Emotion
                              </span>
                              <span className="history-metric__value">
                                {emotion}%
                              </span>
                            </div>
                          )}
                        </div>
                      )}
                    </button>

                    <button
                      type="button"
                      className="history-item__delete"
                      onClick={(event) => {
                        event.stopPropagation();
                        onDeleteEntry(entry.id);
                      }}
                      aria-label="Remove from history"
                    >
                      ✕
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </div>
    </aside>
  );
};
