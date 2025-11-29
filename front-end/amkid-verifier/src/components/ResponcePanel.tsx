import React from "react";

interface ResponsePanelProps {
  show: boolean;
  assistantText: string;
}

export const ResponsePanel: React.FC<ResponsePanelProps> = ({ show, assistantText }) => {
  return (
    <div className={`chat-shell ${show ? "chat-shell--visible" : ""}`}>
      <div className="chat-container glass-panel glass-panel--response">
        <div className="chat-header">
          <div className="chat-header-title">Assistant response</div>
          <div className="chat-header-subtitle">
            Mock analysis only — real models will plug in here later.
          </div>
        </div>

        <main className="chat-main">
          <div className="chat-result">
            {assistantText && <p className="chat-result-text">{assistantText}</p>}
          </div>
        </main>
      </div>
    </div>
  );
};
