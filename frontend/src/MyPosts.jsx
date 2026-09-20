import { useEffect, useState } from "react";

export default function MyPosts({ token, apiBase, onEdit, onClose, onChanged }) {
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [page, setPage] = useState(1);
  const [revision, setRevision] = useState(0);
  const [confirmId, setConfirmId] = useState(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    fetch(`${apiBase}/me/posts?page=${page}`, { headers: { Authorization: `Bearer ${token}` }, signal: controller.signal }).then(async response => {
      if (!response.ok) throw new Error(response.status === 401 ? "Session expired. Log in again." : "Could not load your posts.");
      return response.json();
    }).then(data => { if (!controller.signal.aborted) setResult(data); }).catch(err => { if (!controller.signal.aborted) setError(err.message); });
    return () => controller.abort();
  }, [token, apiBase, page, revision]);
  async function remove(id) {
    setBusy(true); setError("");
    try {
      const response = await fetch(`${apiBase}/blogs/${id}`, { method: "DELETE", headers: { Authorization: `Bearer ${token}` } });
      if (!response.ok) throw new Error(response.status === 401 ? "Session expired. Log in again." : "Could not delete this post.");
      setConfirmId(null); setResult(null);
      if (page > 1 && result.data.length === 1) setPage(page - 1);
      else setRevision(revision + 1);
      onChanged();
    } catch (err) { setError(err.message); } finally { setBusy(false); }
  }
  return <div className="modal-overlay"><section className="create-modal" role="dialog" aria-modal="true" aria-labelledby="my-posts-title">
    <div className="modal-header"><h2 id="my-posts-title">My posts</h2><button className="close-button" onClick={onClose} disabled={busy} aria-label="Close my posts">×</button></div>
    {error && <div role="alert" className="create-error">{error}<button className="account-link" disabled={busy} onClick={() => { setError(""); setRevision(revision + 1); }}>Retry loading</button></div>}
    {!result && !error && <p role="status">Loading your posts…</p>}
    {result && <>
      {!result.total && <p>You haven’t created any posts yet.</p>}
      {result.data.map(post => <article className="managed-post" key={post.id}>
        <span className="post-category">{post.status === "draft" ? "PRIVATE DRAFT" : "PUBLISHED"}</span><h3>{post.title || "Untitled draft"}</h3>
        <div className="managed-actions"><button className="cancel-button" disabled={busy} onClick={() => onEdit(post)}>Edit</button>{post.status === "published" && <a href={`#/posts/${post.id}`} className="read-link" onClick={onClose}>View</a>}<button className="account-link delete-link" disabled={busy} onClick={() => setConfirmId(post.id)}>Delete</button></div>
        {confirmId === post.id && <div className="delete-confirm"><p>Delete this post permanently? This cannot be undone.</p><button className="cancel-button" disabled={busy} onClick={() => setConfirmId(null)}>Keep post</button><button className="publish-button" disabled={busy} onClick={() => remove(post.id)}>{busy ? "Deleting…" : "Confirm delete"}</button></div>}
      </article>)}
      {result.total > 10 && <div className="form-buttons"><button className="cancel-button" disabled={page === 1 || busy} onClick={() => { setPage(page - 1); setResult(null); }}>Previous</button><span>Page {page}</span><button className="cancel-button" disabled={page * 10 >= result.total || busy} onClick={() => { setPage(page + 1); setResult(null); }}>Next</button></div>}
    </>}
  </section></div>;
}
