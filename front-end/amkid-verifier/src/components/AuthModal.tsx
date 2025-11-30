// components/AuthModal.tsx
import React, { useEffect } from "react";

type AuthMode = "help" | "login" | "signup";

interface AuthModalProps {
  mode: AuthMode;
  onClose: () => void;
  onChangeMode: (mode: AuthMode) => void;
}

interface LoginValues {
  email: string;
  password: string;
}

interface SignupValues {
  name?: string;
  email: string;
  password: string;
}

const LoginForm: React.FC<{ onSubmit?: (values: LoginValues) => void }> = ({
  onSubmit,
}) => {
  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);

    const email = (formData.get("email") || "").toString().trim();
    const password = (formData.get("password") || "").toString();

    if (onSubmit) {
      onSubmit({ email, password });
    } else {
      console.log("[Auth] Login submit (ready for backend wiring)", {
        email,
        password,
      });
    }
  };

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      <label className="auth-field">
        <span className="auth-field__label">Email</span>
        <input
          type="email"
          name="email"
          autoComplete="email"
          required
          className="auth-field__input"
          placeholder="you@example.com"
        />
      </label>

      <label className="auth-field">
        <span className="auth-field__label">Password</span>
        <input
          type="password"
          name="password"
          autoComplete="current-password"
          required
          className="auth-field__input"
          placeholder="••••••••"
        />
      </label>

      <button type="submit" className="auth-submit">
        <span>Log in</span>
      </button>
    </form>
  );
};

const SignupForm: React.FC<{ onSubmit?: (values: SignupValues) => void }> = ({
  onSubmit,
}) => {
  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);

    const name = (formData.get("name") || "").toString().trim();
    const email = (formData.get("email") || "").toString().trim();
    const password = (formData.get("password") || "").toString();

    if (onSubmit) {
      onSubmit({ name, email, password });
    } else {
      console.log("[Auth] Sign up submit (ready for backend wiring)", {
        name,
        email,
        password,
      });
    }
  };

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      <label className="auth-field">
        <span className="auth-field__label">Name</span>
        <input
          type="text"
          name="name"
          autoComplete="name"
          className="auth-field__input"
          placeholder="Your name"
        />
      </label>

      <label className="auth-field">
        <span className="auth-field__label">Email</span>
        <input
          type="email"
          name="email"
          autoComplete="email"
          required
          className="auth-field__input"
          placeholder="you@example.com"
        />
      </label>

      <label className="auth-field">
        <span className="auth-field__label">Password</span>
        <input
          type="password"
          name="password"
          autoComplete="new-password"
          required
          className="auth-field__input"
          placeholder="Create a password"
        />
      </label>

      <button type="submit" className="auth-submit">
        <span>Sign up</span>
      </button>
    </form>
  );
};

export const AuthModal: React.FC<AuthModalProps> = ({
  mode,
  onClose,
  onChangeMode,
}) => {
  const isAuthMode = mode === "login" || mode === "signup";

  // Закрытие по Esc
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  const handleLoginSubmit = (values: LoginValues) => {
    // Здесь потом можно вызвать fetch/axios к /login
    console.log("[Auth] Login submit (ready for backend wiring)", values);
  };

  const handleSignupSubmit = (values: SignupValues) => {
    // Здесь потом можно вызвать fetch/axios к /signup
    console.log("[Auth] Sign up submit (ready for backend wiring)", values);
  };

  const title =
    mode === "help"
      ? "Welcome to AMKID verifier"
      : mode === "login"
      ? "Log in to AMKID"
      : "Create your AMKID account";

  const handleOverlayClick = () => {
    onClose();
  };

  const stopPropagation: React.MouseEventHandler<HTMLDivElement> = (event) => {
    event.stopPropagation();
  };

  return (
    <div className="info-overlay" onClick={handleOverlayClick}>
      <div
        className="info-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="auth-modal-title"
        onClick={stopPropagation}
      >
        <button
          type="button"
          className="info-modal__close"
          onClick={onClose}
          aria-label="Close"
        >
          ✕
        </button>

        <div className="info-modal__badge">AMKID</div>
        <h2 id="auth-modal-title" className="info-modal__title">
          {title}
        </h2>

        {/* HELP-режим: описание + кнопки Log in / Sign up */}
        {mode === "help" && (
          <>
            <p className="info-modal__text">
              AMKID helps you quickly check any text for safety, manipulation and
              emotional pressure using AI.
            </p>
            <ul className="info-modal__list">
              <li>Type or paste any text — or use voice input.</li>
              <li>Press the arrow to run the analysis.</li>
              <li>
                See trust, manipulation and emotion scores, dangerous phrases and a
                short summary.
              </li>
            </ul>
            <p className="info-modal__hint">
              You can change the text and rerun the analysis as many times as you
              like.
            </p>

            <div className="auth-help-actions">
              <button
                type="button"
                className="auth-help-button auth-help-button--primary"
                onClick={() => onChangeMode("signup")}
              >
                Sign up
              </button>
              <button
                type="button"
                className="auth-help-button"
                onClick={() => onChangeMode("login")}
              >
                Log in
              </button>
            </div>
          </>
        )}

        {/* LOGIN / SIGNUP РЕЖИМЫ */}
        {isAuthMode && (
          <>
            <div className="auth-tabs">
              <button
                type="button"
                className={`auth-tab ${
                  mode === "login" ? "auth-tab--active" : ""
                }`}
                onClick={() => onChangeMode("login")}
              >
                Log in
              </button>
              <button
                type="button"
                className={`auth-tab ${
                  mode === "signup" ? "auth-tab--active" : ""
                }`}
                onClick={() => onChangeMode("signup")}
              >
                Sign up
              </button>
            </div>

            <p className="auth-subtitle">
              {mode === "login"
                ? "Use your email and password. Later we can connect this form to your backend API."
                : "Create a simple account so AMKID can save your analysis history and preferences."}
            </p>

            {mode === "login" ? (
              <LoginForm onSubmit={handleLoginSubmit} />
            ) : (
              <SignupForm onSubmit={handleSignupSubmit} />
            )}
          </>
        )}
      </div>
    </div>
  );
};
