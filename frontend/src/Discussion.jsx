import { useEffect, useState } from "react";
import { Avatar } from "./Profile.jsx";

export default function Discussion({ postId, apiUrl, token, user, onLogin, onExpired }) {
  const [comments, setComments] = useState(null);
  const [reaction, setReaction] = useState(null);
  const [page, setPage] = useState(1);
  const [revision, setRevision] = useState(0);
  const [body, setBody] = useState("");
  const [editId, setEditId] = useState(null);
  const [editBody, setEditBody] = useState("");
  const [deleteId, setDeleteId] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const base = `${apiUrl}/${postId}`;
  useEffect(() => {
    const controller = new AbortController();
    async function load() {
      try {
        const [list, likes] = await Promise.all([
          fetch(`${base}/comments?page=${page}`, { signal: controller.signal }),
          fetch(`${base}/reactions`, { signal: controller.signal, headers: token ? { Authorization: `Bearer ${token}` } : {} }),
        ]);
        if (!list.ok || !likes.ok) throw new Error(likes.status === 401 ? "Your session expired. Log in again to react." : "Could not load the discussion. Try again after the backend is updated.");
        const [data, reactions] = await Promise.all([list.json(), likes.json()]);
        if (controller.signal.aborted) return;
        const lastPage = Math.max(1, Math.ceil(data.total / 10));
        if (page > lastPage) { setPage(lastPage); return; }
        setComments(data); setReaction(reactions);
      } catch (err) { if (!controller.signal.aborted) setError(err.message); }
    }
    load();
    return () => controller.abort();
  }, [base, token, page, revision]);

  async function mutate(path, method, payload, success) {
    if (busy) return;
    setBusy(true); setError(""); setNotice("");
    try {
      const response = await fetch(`${base}${path}`, {
        method, headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        ...(payload ? { body: JSON.stringify(payload) } : {}),
      });
      if (response.status === 401) { onExpired(); throw new Error("Your session expired. Log in again; the change was not saved."); }
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(typeof data.detail === "string" ? data.detail : "Could not save your change. Please try again.");
      }
      success();
      setRevision(value => value + 1);
    } catch (err) { setError(err.message); } finally { setBusy(false); }
  }
  function changePage(next) { setComments(null); setError(""); setPage(next); }
  return <section className="discussion" aria-labelledby="discussion-title">
    <div className="discussion-heading"><h2 id="discussion-title">Join the conversation</h2>
      <button className={`cancel-button like-button${reaction?.liked ? " is-liked" : ""}`} disabled={busy || (Boolean(token) && !reaction)} aria-pressed={Boolean(reaction?.liked)} onClick={() => token ? mutate("/like", reaction?.liked ? "DELETE" : "PUT", null, () => setNotice(reaction?.liked ? "Like removed." : "Post liked.")) : onLogin()}>
        {reaction?.liked ? "♥ Liked" : "♡ Like"}{reaction ? ` · ${reaction.count}` : ""}
      </button>
    </div>
    {error && <div className="create-error" role="alert">{error} <button className="account-link" disabled={busy} onClick={() => { setError(""); setRevision(value => value + 1); }}>Retry</button></div>}
    <p className="discussion-notice" role="status">{notice}</p>
    {token ? <form className="comment-form" onSubmit={event => { event.preventDefault(); mutate("/comments", "POST", { content: body }, () => { setBody(""); setPage(1); setNotice("Comment posted."); }); }}>
      <label htmlFor="new-comment">Comment as {user?.display_name || user?.username}</label>
      <textarea id="new-comment" value={body} onChange={event => setBody(event.target.value)} maxLength={2000} required rows={3} disabled={busy} placeholder="Share your thoughts about this story…" />
      <div className="comment-form-footer"><small>{body.length}/2000</small><button className="publish-button" disabled={busy || !body.trim()}>{busy ? "Saving…" : "Post comment"}</button></div>
    </form> : <p className="discussion-login"><button className="account-link" onClick={onLogin}>Log in or create an account</button> to comment and like this story.</p>}
    <h3 className="comment-count">Comments{comments ? ` (${comments.total})` : ""}</h3>
    {!comments && !error && <p role="status">Loading comments…</p>}
    {comments?.total === 0 && <p className="discussion-empty">No comments yet. Be the first to share a thought.</p>}
    {comments?.data.map(comment => <article className="comment" key={comment.id}>
      <div className="comment-author"><Avatar key={comment.author.avatar_url} url={comment.author.avatar_url} name={comment.author.display_name || comment.author.username} /><div><a href={`#/authors/${comment.author.id}`}>{comment.author.display_name || comment.author.username}</a><time dateTime={comment.created_at}>{new Date(comment.created_at).toLocaleString()}{comment.edited_at ? " · edited" : ""}</time></div></div>
      {editId === comment.id ? <form className="comment-form" onSubmit={event => { event.preventDefault(); mutate(`/comments/${comment.id}`, "PUT", { content: editBody }, () => { setEditId(null); setNotice("Comment updated."); }); }}>
        <label htmlFor={`edit-comment-${comment.id}`}>Edit your comment</label><textarea id={`edit-comment-${comment.id}`} rows={3} maxLength={2000} required value={editBody} disabled={busy} onChange={event => setEditBody(event.target.value)} />
        <div className="managed-actions"><button className="publish-button" disabled={busy || !editBody.trim()}>Save changes</button><button type="button" className="cancel-button" disabled={busy} onClick={() => setEditId(null)}>Cancel</button></div>
      </form> : <p className="comment-body">{comment.content}</p>}
      {user?.id === comment.user_id && token && <div className="managed-actions"><button className="account-link" disabled={busy} onClick={() => { setEditId(comment.id); setEditBody(comment.content); setDeleteId(null); }}>Edit</button><button className="account-link delete-link" disabled={busy} onClick={() => setDeleteId(comment.id)}>Delete</button></div>}
      {deleteId === comment.id && user?.id === comment.user_id && <div className="delete-confirm"><p>Delete your comment permanently?</p><button className="cancel-button" disabled={busy} onClick={() => setDeleteId(null)}>Keep comment</button><button className="publish-button" disabled={busy} onClick={() => mutate(`/comments/${comment.id}`, "DELETE", null, () => { setDeleteId(null); setNotice("Comment deleted."); })}>Confirm delete</button></div>}
    </article>)}
    {comments && comments.total > 10 && <nav className="pagination" aria-label="Comment pages"><button className="cancel-button" disabled={busy || page === 1} onClick={() => changePage(page - 1)}>Previous</button><span>Page {page} of {Math.ceil(comments.total / 10)}</span><button className="cancel-button" disabled={busy || page * 10 >= comments.total} onClick={() => changePage(page + 1)}>Next</button></nav>}
  </section>;
}
