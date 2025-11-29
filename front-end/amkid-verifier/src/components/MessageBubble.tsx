import React from "react";
import type { ChatMessage } from "../types/chat";

interface MessageBubbleProps {
  message: ChatMessage;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === "user";

  return (
    <div className={`message-row message-row--${isUser ? "user" : "assistant"}`}>
      <div className="message-avatar">
        {isUser ? (
          <div className="avatar-circle avatar-circle--user">U</div>
        ) : (
          <div className="avatar-circle avatar-circle--assistant">AI</div>
        )}
      </div>

      <div className="message-content">
        <div className="message-meta">
          <span className="message-role">{isUser ? "You" : "Assistant"}</span>
        </div>

        <div className="message-bubble">
          {message.text && <p className="message-text">{message.text}</p>}

          {message.images && message.images.length > 0 && (
            <div className="message-images">
              {message.images.map((src, index) => (
                <img
                  key={index}
                  src={src}
                  className="message-image"
                  alt={message.text || "Uploaded image"}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
