// components/AuthModal.tsx
import React, { useEffect, useState } from "react";
import { login as apiLogin, signup as apiSignup } from "../api/chat";

type AuthMode = "help" | "login" | "signup";

interface AuthModalProps {
  mode: AuthMode;
  onClose: () => void;
  onChangeMode: (mode: AuthMode) => void;
  // 🔐 вызовем это после успешного login / signup
  onAuthSuccess?: (email: string) => void;
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

interface LoginFormProps {
  onSubmit?: (values: LoginValues) => void;
  disabled?: boolean;
}

interface SignupFormProps {
  onSubmit?: (values: SignupValues) => void;
  disabled?: boolean;
}

const LoginForm: React.FC<LoginFormProps> = ({ onSubmit, disabled }) => {
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
          disabled={disabled}
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
          disabled={disabled}
        />
      </label>

      <button type="submit" className="auth-submit" disabled={disabled}>
        <span>{disabled ? "Logging in..." : "Log in"}</span>
      </button>
    </form>
  );
};

const SignupForm: React.FC<SignupFormProps> = ({ onSubmit, disabled }) => {
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
          disabled={disabled}
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
          disabled={disabled}
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
          disabled={disabled}
        />
      </label>

      <button type="submit" className="auth-submit" disabled={disabled}>
        <span>{disabled ? "Signing up..." : "Sign up"}</span>
      </button>
    </form>
  );
};

export const AuthModal: React.FC<AuthModalProps> = ({
  mode,
  onClose,
  onChangeMode,
  onAuthSuccess,
}) => {
  const isAuthMode = mode === "login" || mode === "signup";

  const [authError, setAuthError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

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

  // При переключении режимов очищаем ошибку
  useEffect(() => {
    setAuthError(null);
  }, [mode]);

  const handleLoginSubmit = async (values: LoginValues) => {
    try {
      setAuthError(null);
      setIsSubmitting(true);

      const result = await apiLogin({
        email: values.email,
        password: values.password,
      });

      console.log("[Auth] Login success", result);

      // сообщаем App, что авторизация прошла
      if (onAuthSuccess) {
        onAuthSuccess(values.email);
      }

      onClose();
    } catch (error) {
      console.error("[Auth] Login error", error);
      const message =
        error instanceof Error ? error.message : "Failed to log in";
      setAuthError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSignupSubmit = async (values: SignupValues) => {
    try {
      setAuthError(null);
      setIsSubmitting(true);

      const result = await apiSignup({
        email: values.email,
        password: values.password,
        name: values.name,
      });

      console.log("[Auth] Sign up success", result);

      if (onAuthSuccess) {
        onAuthSuccess(values.email);
      }

      onClose();
    } catch (error) {
      console.error("[Auth] Sign up error", error);
      const message =
        error instanceof Error ? error.message : "Failed to sign up";
      setAuthError(message);
    } finally {
      setIsSubmitting(false);
    }
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
                ? "Use your email and password to access your AMKID account."
                : "Create a simple account so AMKID can save your analysis history and preferences."}
            </p>

            {authError && (
              <p className="auth-error" role="alert">
                {authError}
              </p>
            )}

            {mode === "login" ? (
              <LoginForm onSubmit={handleLoginSubmit} disabled={isSubmitting} />
            ) : (
              <SignupForm
                onSubmit={handleSignupSubmit}
                disabled={isSubmitting}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
};
