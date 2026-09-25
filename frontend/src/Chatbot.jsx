import { useEffect, useRef, useState } from "react";
import "./Chatbot.css";

export default function Chatbot({ apiBase, articleId }) {
  const [open, setOpen] = useState(false);
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const controller = useRef(null);
  const input = useRef(null);
  const end = useRef(null);
  const launcher = useRef(null);

  useEffect(() => () => controller.current?.abort(), []);
  useEffect(() => { if (open) input.current?.focus(); }, [open]);
  useEffect(() => { if (open) end.current?.scrollIntoView({ block: "nearest" }); }, [messages, busy, open]);

  function close() {
    setOpen(false);
    launcher.current?.focus();
  }

  async function ask(text) {
    const clean = text.trim();
    if (!clean || controller.current) return;
    const request = new AbortController();
    controller.current = request;
    setBusy(true);
    setError("");
    const timer = setTimeout(() => request.abort(), 40000);
    try {
      const response = await fetch(`${apiBase}/chat`, {
        method: "POST", headers: { "Content-Type": "application/json" }, signal: request.signal,
        body: JSON.stringify({ question: clean, article_id: articleId ? Number(articleId) : null, previous_question: messages.filter(message => message.role === "user").at(-1)?.text || "" }),
      });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(response.status === 404 ? "Chat isn't available on this server yet." : typeof data?.detail === "string" ? data.detail : "Unable to get an answer. Please try again.");
      if (typeof data?.answer !== "string" || !Array.isArray(data.sources)) throw new Error("Unable to read the answer. Please try again.");
      setMessages(previous => [...previous, { role: "user", text: clean }, { role: "assistant", text: data.answer, sources: data.sources }].slice(-20));
      setQuestion("");
    } catch (failure) {
      setQuestion(clean);
      setError(failure.name === "AbortError" ? "The request timed out. Please try again." : failure.message || "Connection failed. Please try again.");
    } finally {
      clearTimeout(timer);
      controller.current = null;
      setBusy(false);
    }
  }

  return <div className="reader-chat">
    {open && <section id="reader-chat-panel" className="reader-chat-panel" role="region" aria-label="Ask Dani Blogs" onKeyDown={event => { if (event.key === "Escape") close(); }}>
      <header className="reader-chat-header">
        <div><strong>Ask Dani Blogs</strong><p>Your guide to published stories</p></div>
        <button type="button" onClick={close} aria-label="Close chat">×</button>
      </header>
      <p className="reader-chat-context">{articleId ? "Reading this article · Answers use its available text" : "Discover stories from the community"}</p>
      <div className="reader-chat-messages" role="log" aria-live="polite" aria-relevant="additions">
        {!messages.length && <div className="reader-chat-welcome"><h3>What would you like to read?</h3><p>I can find posts and explain what they say. Open an article to ask about it.</p></div>}
        {messages.map((message, index) => <div className={`reader-chat-message ${message.role}`} key={index}>
          <span className="reader-chat-speaker">{message.role === "user" ? "You" : "Dani Blogs"}</span>
          <p>{message.text}</p>
          {!!message.sources?.length && <div className="reader-chat-sources"><strong>Read the sources</strong>{message.sources.map(source => <a key={source.id} href={`#/posts/${source.id}`} onClick={close}>{source.title} →</a>)}</div>}
        </div>)}
        {busy && <p role="status">Reading published posts…</p>}
        <div ref={end} />
      </div>
      <div className="reader-chat-starters">
        {(articleId ? ["Summarize this article", "What are the key points?"] : ["Show me the latest posts", "Find posts about technology"]).map(text => <button type="button" key={text} disabled={busy} onClick={() => { setQuestion(text); ask(text); }}>{text}</button>)}
      </div>
      {error && <p className="reader-chat-error" role="alert">{error}</p>}
      <form className="reader-chat-form" onSubmit={event => { event.preventDefault(); ask(question); }}>
        <label htmlFor="reader-chat-question">Ask about published posts</label>
        <div><input id="reader-chat-question" ref={input} value={question} maxLength={1000} disabled={busy} onChange={event => setQuestion(event.target.value)} placeholder="Type your question…" autoComplete="off" /><button type="submit" disabled={busy || !question.trim()}>Send</button></div>
      </form>
      <footer className="reader-chat-footer"><span>AI can make mistakes. Check the sources. Questions and public excerpts are sent to our AI provider (Google or OpenAI).</span><button type="button" disabled={busy} onClick={() => { setMessages([]); setError(""); setQuestion(""); input.current?.focus(); }}>Clear chat</button></footer>
    </section>}
    <button ref={launcher} type="button" className="reader-chat-launcher" aria-expanded={open} aria-controls="reader-chat-panel" onClick={() => open ? close() : setOpen(true)}>✦ Ask Dani Blogs</button>
  </div>;
}
