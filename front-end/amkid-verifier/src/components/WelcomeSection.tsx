import React from "react";

interface WelcomeSectionProps {
  value: string;
  hasSubmitted: boolean;
  isEditing: boolean;
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onSubmit: (event: React.FormEvent) => void;
  onStartEdit: () => void;
}

export const WelcomeSection: React.FC<WelcomeSectionProps> = ({
  value,
  hasSubmitted,
  isEditing,
  onChange,
  onSubmit,
  onStartEdit,
}) => {
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
          </div>

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
