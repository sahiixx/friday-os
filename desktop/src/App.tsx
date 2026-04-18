import { useState } from "react";

// Tauri shell points at the local FRIDAY A2A server. Swap via env:
//   VITE_FRIDAY_URL=http://localhost:8001 npm run dev
const FRIDAY_URL = import.meta.env.VITE_FRIDAY_URL ?? "http://localhost:8001";

type Turn = { role: "user" | "friday"; text: string };

export default function App() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);

  async function send() {
    const text = input.trim();
    if (!text || busy) return;
    setTurns((t) => [...t, { role: "user", text }]);
    setInput("");
    setBusy(true);
    try {
      const r = await fetch(`${FRIDAY_URL}/a2a/invoke`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ skill: "chat", input: text }),
      });
      const data = await r.json();
      setTurns((t) => [...t, { role: "friday", text: data.output ?? "(no reply)" }]);
    } catch (err) {
      setTurns((t) => [...t, { role: "friday", text: `error: ${err}` }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={styles.app}>
      <header style={styles.header}>FRIDAY OS</header>
      <main style={styles.log}>
        {turns.map((t, i) => (
          <div key={i} style={{ ...styles.turn, ...(t.role === "user" ? styles.user : styles.friday) }}>
            <b>{t.role}:</b> {t.text}
          </div>
        ))}
      </main>
      <form style={styles.bar} onSubmit={(e) => { e.preventDefault(); send(); }}>
        <input
          style={styles.input}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask FRIDAY..."
          autoFocus
        />
        <button type="submit" disabled={busy} style={styles.send}>
          {busy ? "…" : "Send"}
        </button>
      </form>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  app: { fontFamily: "system-ui", height: "100vh", display: "flex", flexDirection: "column", background: "#0b0d12", color: "#eaeaea" },
  header: { padding: "12px 16px", fontWeight: 600, borderBottom: "1px solid #222" },
  log: { flex: 1, overflowY: "auto", padding: 16, display: "flex", flexDirection: "column", gap: 8 },
  turn: { padding: "8px 12px", borderRadius: 8, maxWidth: "80%" },
  user: { background: "#1d2638", alignSelf: "flex-end" },
  friday: { background: "#15202e", alignSelf: "flex-start" },
  bar: { display: "flex", gap: 8, padding: 12, borderTop: "1px solid #222" },
  input: { flex: 1, padding: "8px 12px", borderRadius: 6, border: "1px solid #333", background: "#111", color: "#eaeaea" },
  send: { padding: "8px 16px", borderRadius: 6, border: 0, background: "#3b82f6", color: "white", cursor: "pointer" },
};
