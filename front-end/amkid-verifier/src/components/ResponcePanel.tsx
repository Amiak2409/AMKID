import React, { useEffect, useMemo, useState } from "react";
import { RadialBarChart, RadialBar, PolarAngleAxis } from "recharts";

interface ResponsePanelProps {
  show: boolean;
  assistantText: string;
  onNewMessage?: () => void;
}

interface ClaimEvaluationItem {
  text: string;
  true_likeliness: number; // может быть 0–1 или 0–100
  comment: string;
}

interface AiAnalysisResponse {
  trust_score: number; // 0–100
  ai_likeliness: number; // 0–1
  manipulation_score: number; // 0–1
  emotion_intensity: number; // 0–1
  claims_evaluation?: ClaimEvaluationItem[];
  dangerous_phrases?: string[];
  summary?: string;
}

interface MetricDialProps {
  label: string;
  value: number; // 0–100
  color: string;
}

const MetricDial: React.FC<MetricDialProps> = ({ label, value, color }) => {
  const clamped = Math.max(0, Math.min(100, value));

  const data = [
    {
      name: label,
      value: clamped,
      fill: color,
    },
  ];

  return (
    <div className="metric-dial">
      <div className="metric-dial__chart">
        <RadialBarChart
          width={120}
          height={120}
          innerRadius="70%"
          outerRadius="100%"
          barSize={10}
          data={data}
          startAngle={90}
          endAngle={450}
        >
          <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
          <RadialBar
            dataKey="value"
            cornerRadius={999}
            background={{ fill: "rgba(15,23,42,0.7)" }}
          />
        </RadialBarChart>
        <div className="metric-dial__center">
          <div className="metric-dial__value">{Math.round(clamped)}%</div>
        </div>
      </div>
      <div className="metric-dial__label">{label}</div>
    </div>
  );
};

export const ResponsePanel: React.FC<ResponsePanelProps> = ({
  show,
  assistantText,
  onNewMessage,
}) => {
  const trimmed = assistantText.trim();
  const isJsonCandidate =
    trimmed.startsWith("{") && trimmed.includes("trust_score");

  const analysis: AiAnalysisResponse | null = useMemo(() => {
    if (!isJsonCandidate) return null;
    try {
      const parsed = JSON.parse(trimmed);
      if (
        typeof parsed === "object" &&
        parsed !== null &&
        typeof parsed.trust_score === "number"
      ) {
        return parsed as AiAnalysisResponse;
      }
      return null;
    } catch {
      return null;
    }
  }, [trimmed, isJsonCandidate]);

  const hasAnalysis = Boolean(analysis);

  // === состояния анимаций ===
  const [showMetrics, setShowMetrics] = useState(false);
  const [showDanger, setShowDanger] = useState(false);
  const [showClaims, setShowClaims] = useState(false);
  const [showSummarySection, setShowSummarySection] = useState(false);
  const [typedSummary, setTypedSummary] = useState("");
  const [summaryFinished, setSummaryFinished] = useState(false);

  // loading: панель уже показана, но анализа ещё нет
  const isInitiallyLoading = show && !assistantText;
  const isLoading = isInitiallyLoading || (isJsonCandidate && !analysis);

  // fallback: это не JSON анализа, а просто текст
  const showTextFallback =
    !isLoading && !hasAnalysis && !!assistantText && !isJsonCandidate;

  // когда появился analysis — по очереди включаем секции + печатаем summary по словам
  useEffect(() => {
    const timers: number[] = [];

    if (analysis) {
      setShowMetrics(false);
      setShowDanger(false);
      setShowClaims(false);
      setShowSummarySection(false);
      setTypedSummary("");
      setSummaryFinished(false);

      // метрики
      timers.push(window.setTimeout(() => setShowMetrics(true), 120));

      // опасные фразы
      if (analysis.dangerous_phrases && analysis.dangerous_phrases.length > 0) {
        timers.push(window.setTimeout(() => setShowDanger(true), 280));
      }

      // утверждения
      if (analysis.claims_evaluation && analysis.claims_evaluation.length > 0) {
        timers.push(window.setTimeout(() => setShowClaims(true), 440));
      }

      // summary + печать по словам
      if (analysis.summary) {
        timers.push(
          window.setTimeout(() => {
            setShowSummarySection(true);

            const words = analysis.summary?.split(/\s+/) ?? [];
            if (!words.length) {
              setSummaryFinished(true);
              return;
            }

            let index = 0;
            const intervalId = window.setInterval(() => {
              index += 1;
              setTypedSummary(words.slice(0, index).join(" "));
              if (index >= words.length) {
                window.clearInterval(intervalId);
                setSummaryFinished(true);
              }
            }, 80);

            timers.push(intervalId);
          }, 600),
        );
      } else {
        // если summary нет — просто считаем, что анимация к этому моменту завершена
        timers.push(window.setTimeout(() => setSummaryFinished(true), 600));
      }
    } else {
      setShowMetrics(false);
      setShowDanger(false);
      setShowClaims(false);
      setShowSummarySection(false);
      setTypedSummary("");
      setSummaryFinished(false);
    }

    return () => {
      timers.forEach((id) => window.clearTimeout(id));
    };
  }, [analysis]);

  return (
    <div className={`chat-shell ${show ? "chat-shell--visible" : ""}`}>
      <div className="chat-container glass-panel glass-panel--response">
        <div className="chat-header">
          <div className="chat-header-title">Assistant analysis</div>
          <div className="chat-header-subtitle">
            AI-powered safety & trust overview of your text
          </div>
        </div>

        <main className="chat-main">
          {/* ЛОАДЕР — мигающая точка, пока JSON ещё не готов */}
          {isLoading && (
            <div className="analysis-loader">
              <span className="analysis-loader__dot" />
            </div>
          )}

          {/* КРАСИВЫЙ АНАЛИЗ, когда JSON уже есть */}
          {!isLoading && hasAnalysis && analysis && (
            <div className="analysis-layout">
              {/* METRICS */}
              {showMetrics && (
                <section className="analysis-section analysis-section--animated">
                  <h3 className="analysis-section__title">Overall scores</h3>
                  <div className="analysis-metrics-grid">
                    <MetricDial
                      label="Trust score"
                      value={analysis.trust_score}
                      color="#22d3ee"
                    />
                    <MetricDial
                      label="AI likeliness"
                      value={analysis.ai_likeliness * 100}
                      color="#a855f7"
                    />
                    <MetricDial
                      label="Manipulation"
                      value={analysis.manipulation_score * 100}
                      color="#fb7185"
                    />
                    <MetricDial
                      label="Emotion intensity"
                      value={analysis.emotion_intensity * 100}
                      color="#f973ff"
                    />
                  </div>
                </section>
              )}

              {/* DANGEROUS PHRASES */}
              {analysis.dangerous_phrases &&
                analysis.dangerous_phrases.length > 0 &&
                showDanger && (
                  <section className="analysis-section analysis-section--animated">
                    <h3 className="analysis-section__title">
                      Dangerous phrases detected
                    </h3>
                    <p className="analysis-section__hint">
                      These fragments look toxic, hateful or unsafe and may
                      require rephrasing.
                    </p>
                    <div className="danger-chips">
                      {analysis.dangerous_phrases.map((phrase, idx) => (
                        <span
                          key={`${phrase}-${idx}`}
                          className="danger-chip"
                        >
                          <span className="danger-chip__dot" />
                          {phrase}
                        </span>
                      ))}
                    </div>
                  </section>
                )}

              {/* CLAIMS */}
              {analysis.claims_evaluation &&
                analysis.claims_evaluation.length > 0 &&
                showClaims && (
                  <section className="analysis-section analysis-section--animated">
                    <h3 className="analysis-section__title">
                      Claims evaluation
                    </h3>
                    <div className="claims-grid">
                      {analysis.claims_evaluation.map((claim, idx) => {
                        const raw = claim.true_likeliness;
                        const likelihood =
                          raw <= 1 ? Math.round(raw * 100) : Math.round(raw);
                        const clamped = Math.max(
                          0,
                          Math.min(100, likelihood),
                        );
                        const isLikelyTrue = clamped >= 60;

                        return (
                          <article key={idx} className="claim-card">
                            <header className="claim-card__header">
                              <div
                                className={`claim-badge ${
                                  isLikelyTrue
                                    ? "claim-badge--true"
                                    : "claim-badge--false"
                                }`}
                              >
                                {isLikelyTrue ? "Likely true" : "Likely false"}
                              </div>
                              <div className="claim-score">{clamped}%</div>
                            </header>
                            <p className="claim-text">“{claim.text}”</p>
                            {claim.comment && (
                              <p className="claim-comment">
                                {claim.comment}
                              </p>
                            )}
                          </article>
                        );
                      })}
                    </div>
                  </section>
                )}

              {/* SUMMARY */}
              {analysis.summary && showSummarySection && (
                <section className="analysis-section analysis-summary analysis-section--animated">
                  <h3 className="analysis-section__title">Summary</h3>
                  <p className="analysis-summary__text">
                    {typedSummary || analysis.summary}
                  </p>
                </section>
              )}

              {/* NEW MESSAGE BUTTON */}
              {onNewMessage && (
                <div className="analysis-footer">
                  <button
                    type="button"
                    className={`new-message-pill ${
                      summaryFinished ? "new-message-pill--visible" : ""
                    }`}
                    onClick={onNewMessage}
                  >
                    <span
                      className="new-message-pill__icon"
                      aria-hidden="true"
                    >
                      +
                    </span>
                    <span className="new-message-pill__label">
                      New message
                    </span>
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Fallback: если это обычный текст, а не JSON анализа */}
          {showTextFallback && (
            <div className="chat-result">
              <p className="chat-result-text">{assistantText}</p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};
