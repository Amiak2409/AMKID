import React from "react";

interface WelcomeSectionProps {
  value: string;
  hasSubmitted: boolean;
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onSubmit: (event: React.FormEvent) => void;
}

export const WelcomeSection: React.FC<WelcomeSectionProps> = ({
  value,
  hasSubmitted,
  onChange,
  onSubmit,
}) => {
  return (
    <div className={`question-shell ${hasSubmitted ? "question-shell--pinned" : ""}`}>
      <div className="question-inner">
        {!hasSubmitted && (
          <h1 className="hero-title hero-title--brand">welcome from AMKID</h1>
        )}

        <form className="hero-form" onSubmit={onSubmit}>
          <input
            type="text"
            className="hero-input"
            placeholder={hasSubmitted ? "" : "Type anything to begin…"}
            value={value}
            readOnly={hasSubmitted}
            onChange={hasSubmitted ? undefined : onChange}
          />

          {!hasSubmitted && (
            <button type="submit" className="hero-button" aria-label="Start">
              <span aria-hidden="true">➜</span>
            </button>
          )}
        </form>
      </div>
    </div>
  );
};
