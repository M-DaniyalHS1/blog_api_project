import { useEffect, useRef, useState } from "react";
import "./WritingAssistant.css";

export default function WritingAssistant({ apiBase, token, postId, title, summary, content, disabled, onApply }) {
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const pending = useRef(null);
  const snapshot = JSON.stringify({ title, summary, content });
  const stale = result && result.snapshot !== snapshot;
  const unavailable = busy || disabled || !content.trim() || content.length > 12000 || title.length > 300;
  useEffect(() => () => pending.current?.abort(), []);

  async function suggest(action) {
    if (unavailable || pending.current) return;
    const controller = new AbortController();
    pending.current = controller;
    setBusy(true); setError(""); setResult(null);
    const timeout = setTimeout(() => controller.abort(), 40000);
    try {
      const response = await fetch(`${apiBase}/writing-assistant`, {
        method: "POST", signal: controller.signal,
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ action, post_id: postId, title, content }),
      });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(response.status === 401 ? "Your session expired. Log in again to request suggestions. Your text is unchanged." : response.status === 404 ? "Writing assistance is unavailable for this post or server." : typeof data?.detail === "string" ? data.detail : "Could not create a suggestion. Please try again.");
      const suggestion = data?.suggestion;
      const valid = action === "titles" ? Array.isArray(suggestion?.titles) && suggestion.titles.length === 3 && suggestion.titles.every(text => typeof text === "string") : typeof suggestion?.[action === "summary" ? "summary" : "content"] === "string";
      if (!valid) throw new Error("The suggestion could not be read. Your text is unchanged.");
      setResult({ action, suggestion, snapshot });
    } catch (failure) {
      if (!controller.signal.aborted || pending.current) setError(failure.name === "AbortError" ? "The request timed out. Your text is unchanged. Try again." : failure.message);
    } finally {
      clearTimeout(timeout); pending.current = null; setBusy(false);
    }
  }

  function apply(field, value) {
    if (stale || disabled) return;
    onApply(field, value);
    setResult(null);
  }

  return <section className="writing-assistant" aria-label="Writing assistant">
    <h3>Writing assistant</h3>
    <p>Get help with your article, then review before applying. Requesting a suggestion sends this article text—including private drafts—to Google Gemini.</p>
    <div className="writing-actions">
      <button type="button" disabled={unavailable} onClick={() => suggest("titles")}>Suggest titles</button>
      <button type="button" disabled={unavailable} onClick={() => suggest("summary")}>Write a summary</button>
      <button type="button" disabled={unavailable} onClick={() => suggest("improve")}>Improve article</button>
    </div>
    {!content.trim() && <p>Add article text first.</p>}
    {(content.length > 12000 || title.length > 300) && <p>Writing assistance supports articles up to 12,000 characters and titles up to 300 characters. You can still save your post normally.</p>}
    {busy && <p role="status">Preparing a suggestion… You can keep editing.</p>}
    {error && <p role="alert" className="writing-error">{error}</p>}
    {result && <div className="writing-preview">
      <h4>Review suggestion</h4>
      <p>Check facts and wording. Applying replaces the selected editor field; save or publish separately.</p>
      {stale && <p role="status">Your text changed. Request a new suggestion to use the latest version.</p>}
      {result.action === "titles" ? result.suggestion.titles.map((value, index) => <div className="writing-choice" key={index}><p>{value}</p><button type="button" disabled={stale || disabled} onClick={() => apply("title", value)}>Use this title</button></div>) : <>
        <div className="writing-text">{result.suggestion[result.action === "summary" ? "summary" : "content"]}</div>
        <button type="button" disabled={stale || disabled} onClick={() => apply(result.action === "summary" ? "summary" : "content", result.suggestion[result.action === "summary" ? "summary" : "content"])}>Replace {result.action === "summary" ? "summary" : "article"} with suggestion</button>
      </>}
      <button type="button" className="writing-dismiss" onClick={() => setResult(null)}>Discard suggestion</button>
    </div>}
  </section>;
}
