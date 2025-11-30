import React, { useEffect, useMemo, useState, useRef } from "react";
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

/* ============================
   HELPERЫ ДЛЯ ФОНА
   ============================ */

type RGB = [number, number, number];

const clamp01 = (v: number) => Math.max(0, Math.min(1, v));

const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

const mixColor = (a: RGB, b: RGB, t: number): RGB => [
  lerp(a[0], b[0], t),
  lerp(a[1], b[1], t),
  lerp(a[2], b[2], t),
];

const rgbTripletToVarValue = (c: RGB): string => {
  const [r, g, b] = c.map((x) => Math.round(x)) as RGB;
  return `${r}, ${g}, ${b}`;
};

const rgbTripletToColor = (c: RGB): string => {
  const [r, g, b] = c.map((x) => Math.round(x)) as RGB;
  return `rgb(${r}, ${g}, ${b})`;
};

// ПАЛИТРА ДЛЯ ОЧЕНЬ ХОРОШИХ / БЕЗОПАСНЫХ СООБЩЕНИЙ
const POSITIVE_PALETTE = {
  bg1: [8, 22, 40] as RGB,   // чуть более мягкий сине-фиолетовый фон
  bg2: [4, 10, 30] as RGB,
  c1: [110, 240, 220] as RGB, // мятно-бирюзовые бабблы
  c2: [170, 210, 255] as RGB, // светло-голубые
  c3: [215, 190, 255] as RGB, // лавандовые
  c4: [130, 220, 255] as RGB,
  c5: [20, 40, 90] as RGB,
  interactive: [185, 225, 255] as RGB,
};

// НЕЙТРАЛЬНАЯ ПАЛИТРА — ТВОЙ ТЕКУЩИЙ ФОН
const NEUTRAL_PALETTE = {
  bg1: [6, 0, 28] as RGB, // ~ #06001c
  bg2: [2, 0, 16] as RGB, // ~ #020010
  c1: [115, 215, 255] as RGB,
  c2: [180, 130, 255] as RGB,
  c3: [255, 145, 255] as RGB,
  c4: [120, 170, 255] as RGB,
  c5: [40, 15, 80] as RGB,
  interactive: [175, 145, 255] as RGB,
};

// ОЧЕНЬ ПЛОХИЕ / ТОКСИЧНЫЕ СООБЩЕНИЯ
const NEGATIVE_PALETTE = {
  bg1: [24, 2, 16] as RGB,   // темно-бордовый фон
  bg2: [8, 0, 8] as RGB,
  c1: [255, 120, 120] as RGB, // красно-розовые бабблы
  c2: [255, 80, 160] as RGB,
  c3: [255, 40, 120] as RGB,
  c4: [210, 90, 255] as RGB,
  c5: [60, 0, 40] as RGB,
  interactive: [255, 110, 190] as RGB,
};

// tone ∈ [-1, 1]:
// -1  → максимально позитивная палитра
//  0  → нейтральная
//  1  → максимально тревожная
const mix3 = (positive: RGB, neutral: RGB, negative: RGB, tone: number): RGB => {
  const t = Math.max(-1, Math.min(1, tone));

  if (t <= 0) {
    // от POSITIVE (-1) к NEUTRAL (0)
    const u = t + 1; // -1 → 0; 0 → 1
    return mixColor(positive, neutral, u);
  }

  // от NEUTRAL (0) к NEGATIVE (1)
  const u = t; // 0 → 0; 1 → 1
  return mixColor(neutral, negative, u);
};

const applyDangerToCss = (dangerLevel: number) => {
  if (typeof document === "undefined") return;

  const danger = clamp01(dangerLevel);
  // danger = 0   → tone = -1 (очень хороший текст → позитивные цвета)
  // danger = 0.5 → tone = 0  (нейтральный)
  // danger = 1   → tone = 1  (максимально плохой → красный тёмный фон)
  const tone = danger * 2 - 1;

  const root = document.documentElement;

  const bg1 = mix3(POSITIVE_PALETTE.bg1, NEUTRAL_PALETTE.bg1, NEGATIVE_PALETTE.bg1, tone);
  const bg2 = mix3(POSITIVE_PALETTE.bg2, NEUTRAL_PALETTE.bg2, NEGATIVE_PALETTE.bg2, tone);
  const c1 = mix3(POSITIVE_PALETTE.c1, NEUTRAL_PALETTE.c1, NEGATIVE_PALETTE.c1, tone);
  const c2 = mix3(POSITIVE_PALETTE.c2, NEUTRAL_PALETTE.c2, NEGATIVE_PALETTE.c2, tone);
  const c3 = mix3(POSITIVE_PALETTE.c3, NEUTRAL_PALETTE.c3, NEGATIVE_PALETTE.c3, tone);
  const c4 = mix3(POSITIVE_PALETTE.c4, NEUTRAL_PALETTE.c4, NEGATIVE_PALETTE.c4, tone);
  const c5 = mix3(POSITIVE_PALETTE.c5, NEUTRAL_PALETTE.c5, NEGATIVE_PALETTE.c5, tone);
  const interactive = mix3(
    POSITIVE_PALETTE.interactive,
    NEUTRAL_PALETTE.interactive,
    NEGATIVE_PALETTE.interactive,
    tone,
  );

  // фон-градиент
  root.style.setProperty("--color-bg1", rgbTripletToColor(bg1));
  root.style.setProperty("--color-bg2", rgbTripletToColor(bg2));

  // сами «пятна»-бабблы
  root.style.setProperty("--color1", rgbTripletToVarValue(c1));
  root.style.setProperty("--color2", rgbTripletToVarValue(c2));
  root.style.setProperty("--color3", rgbTripletToVarValue(c3));
  root.style.setProperty("--color4", rgbTripletToVarValue(c4));
  root.style.setProperty("--color5", rgbTripletToVarValue(c5));
  root.style.setProperty("--color-interactive", rgbTripletToVarValue(interactive));
};

// 0 → всё ок, 1 → всё очень плохо
const computeDangerLevelFromAnalysis = (a: AiAnalysisResponse): number => {
  const trustComponent = clamp01(1 - a.trust_score / 100); // ниже trust → опаснее
  const manipulationComponent = clamp01(a.manipulation_score);
  const emotionComponent = clamp01(a.emotion_intensity);
  const phrasesComponent =
    a.dangerous_phrases && a.dangerous_phrases.length > 0 ? 1 : 0;

  // простая взвешенная смесь: чем хуже метрики, тем выше danger
  const raw =
    trustComponent * 0.4 +
    manipulationComponent * 0.3 +
    emotionComponent * 0.2 +
    phrasesComponent * 0.1;

  return clamp01(raw);
};


/* ============================
   METRIC DIAL
   ============================ */

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

/* ============================
   RESPONSE PANEL
   ============================ */

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
        typeof (parsed as AiAnalysisResponse).trust_score === "number"
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

  // 👉 тут мы обновляем фон в зависимости от анализа
  // текущее значение "опасности" (нужно, чтобы анимировать от старого к новому)
// текущее значение "опасности" (нужно, чтобы анимировать от старого к новому)
const dangerRef = useRef(0.5);

// плавная анимация фона при смене анализа
useEffect(() => {
  // если анализа нет (новый запрос / старт) → уходим в нейтральную палитру (0.5)
  const targetDanger = analysis ? computeDangerLevelFromAnalysis(analysis) : 0.5;
  const startDanger = dangerRef.current;
  const duration = 4000; // 2 секунды
  const startTime = performance.now();
  let frameId: number;

  const tick = (now: number) => {
    const elapsed = now - startTime;
    const progress = Math.min(1, elapsed / duration);

    // лёгкий easing
    const eased = progress * (2 - progress);

    const current = startDanger + (targetDanger - startDanger) * eased;
    dangerRef.current = current;
    applyDangerToCss(current);

    if (progress < 1) {
      frameId = requestAnimationFrame(tick);
    }
  };

  frameId = requestAnimationFrame(tick);

  return () => {
    cancelAnimationFrame(frameId);
  };
}, [analysis]);




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
