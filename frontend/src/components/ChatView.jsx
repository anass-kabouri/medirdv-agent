import { useEffect, useRef, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const WELCOME_MESSAGE = {
  role: "assistant",
  content:
    "Bonjour ! Je suis l'assistant de prise de rendez-vous de MediRDV. " +
    "Dites-moi quel type de praticien vous cherchez, ou pour quand vous " +
    "souhaitez un rendez-vous, et je m'occupe du reste.",
};

function ChatView({ onGoToAdmin, onGoToPatientAccount }) {
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  async function sendMessage(e) {
    e.preventDefault();
    const text = input.trim();
    if (!text || isLoading) return;

    const nextMessages = [...messages, { role: "user", content: text }];
    setMessages(nextMessages);
    setInput("");
    setError(null);
    setIsLoading(true);

    try {
      const response = await fetch(`${API_URL}/chat/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: nextMessages }),
      });

      if (!response.ok) {
        throw new Error(`Le serveur a repondu avec le code ${response.status}`);
      }

      const data = await response.json();
      setMessages([...nextMessages, { role: "assistant", content: data.reply }]);
    } catch (err) {
      setError(
        "Impossible de contacter l'assistant. Verifie que le backend tourne bien sur " +
          API_URL +
          "."
      );
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <h1>MediRDV</h1>
          <p>Assistant de prise de rendez-vous</p>
        </div>
        <div className="header-actions">
          <button className="admin-link" onClick={onGoToPatientAccount}>
            Mon compte
          </button>
          <button className="admin-link" onClick={onGoToAdmin}>
            Espace admin
          </button>
        </div>
      </header>

      <main className="chat-window">
        {messages.map((msg, i) => (
          <div key={i} className={`bubble-row ${msg.role}`}>
            <div className={`bubble ${msg.role}`}>{msg.content}</div>
          </div>
        ))}

        {isLoading && (
          <div className="bubble-row assistant">
            <div className="bubble assistant typing">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}

        {error && <div className="error-banner">{error}</div>}

        <div ref={scrollRef} />
      </main>

      <form className="chat-input" onSubmit={sendMessage}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ecrivez votre message..."
          disabled={isLoading}
        />
        <button type="submit" disabled={isLoading || !input.trim()}>
          Envoyer
        </button>
      </form>
    </div>
  );
}

export default ChatView;