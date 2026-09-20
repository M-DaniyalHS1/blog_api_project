import { useEffect, useState } from "react";

export function Avatar({ url, name }) {
  const [failed, setFailed] = useState(false);
  return url && !failed ? <img className="profile-avatar" src={url} alt={`${name}'s profile`} referrerPolicy="no-referrer" onError={() => setFailed(true)} /> : <span className="profile-avatar avatar-placeholder" aria-label={`${name}'s profile`}>{name?.[0]?.toUpperCase() || "?"}</span>;
}

export function ProfileEditor({ user, token, apiBase, onSaved, onClose }) {
  const [name, setName] = useState(user.display_name || "");
  const [bio, setBio] = useState(user.bio || "");
  const [avatar, setAvatar] = useState(user.avatar_url || "");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  async function save(event) {
    event.preventDefault();
    setSaving(true); setError("");
    try {
      const response = await fetch(`${apiBase}/me/profile`, { method: "PATCH", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` }, body: JSON.stringify({ display_name: name, bio, avatar_url: avatar }) });
      const data = await response.json();
      if (!response.ok) throw new Error(response.status === 401 ? "Your session expired. Close this form and log in again." : typeof data.detail === "string" ? data.detail : "Check the picture URL and field lengths.");
      onSaved(data);
    } catch (err) { setError(err.message); } finally { setSaving(false); }
  }
  return <div className="modal-overlay"><section className="create-modal" role="dialog" aria-modal="true" aria-labelledby="profile-editor-title">
    <div className="modal-header"><h2 id="profile-editor-title">Edit profile</h2><button className="close-button" disabled={saving} onClick={onClose} aria-label="Close profile editor">×</button></div>
    <form onSubmit={save}>
      <label htmlFor="profile-name">Display name</label><input id="profile-name" value={name} onChange={e => setName(e.target.value)} maxLength={80} placeholder={user.username} disabled={saving} />
      <label htmlFor="profile-avatar">Picture URL</label><input id="profile-avatar" type="url" value={avatar} onChange={e => setAvatar(e.target.value)} maxLength={2048} placeholder="https://example.com/portrait.jpg" disabled={saving} />
      <p className="image-help">Use a public HTTP or HTTPS image link, or leave empty for your initial.</p>
      <Avatar key={avatar} url={/^https?:\/\//i.test(avatar) ? avatar : null} name={name || user.username} />
      <label htmlFor="profile-bio">About you</label><textarea id="profile-bio" value={bio} onChange={e => setBio(e.target.value)} maxLength={1000} rows={4} placeholder="Tell readers a little about yourself." disabled={saving} />
      {error && <p className="create-error" role="alert">{error}</p>}
      <div className="form-buttons"><button type="button" className="cancel-button" onClick={onClose} disabled={saving}>Cancel</button><button className="publish-button" disabled={saving}>{saving ? "Saving…" : "Save profile"}</button></div>
    </form>
  </section></div>;
}

export function AuthorPage({ id, apiBase }) {
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [page, setPage] = useState(1);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    fetch(`${apiBase}/authors/${id}?page=${page}`, { signal: controller.signal }).then(async response => {
      if (!response.ok) throw new Error(response.status === 404 ? "Author not found." : "Could not load this profile.");
      return response.json();
    }).then(data => { if (!controller.signal.aborted) setResult(data); }).catch(err => { if (!controller.signal.aborted) setError(err.message); });
    return () => controller.abort();
  }, [id, apiBase, page, attempt]);
  useEffect(() => {
    document.title = result ? `${result.author.display_name || result.author.username} | Dani Blogs` : "Author | Dani Blogs";
    return () => { document.title = "Dani Blogs"; };
  }, [result]);
  function changePage(next) { setResult(null); setError(""); setPage(next); window.scrollTo(0, 0); }
  return <div className="app"><nav className="navbar"><a className="logo" href="#home">Dani Blogs</a><a className="read-link" href="#posts">All posts</a></nav><main className="article-page">
    {error ? <div className="article-status" role="alert"><p>{error}</p><button className="secondary-button" onClick={() => { setError(""); setAttempt(attempt + 1); }}>Try again</button></div> : !result ? <p role="status">Loading profile…</p> : <>
      <header className="profile-header"><Avatar key={result.author.avatar_url} url={result.author.avatar_url} name={result.author.display_name || result.author.username} /><div><span className="section-label">AUTHOR</span><h1>{result.author.display_name || result.author.username}</h1><p>@{result.author.username}</p></div></header>
      <p className="profile-bio">{result.author.bio || "This author hasn’t added a bio yet."}</p>
      <h2 className="profile-post-heading">Published posts · {result.total}</h2>
      {result.total === 0 && <p>No published posts yet.</p>}
      {result.data.map(post => <article className="profile-post" key={post.id}><h3><a href={`#/posts/${post.id}`}>{post.title}</a></h3><p>{(post.summary || post.content).slice(0, 220)}{(post.summary || post.content).length > 220 ? "…" : ""}</p><a className="read-link" href={`#/posts/${post.id}`}>Read story →</a></article>)}
      {result.total > 12 && <div className="form-buttons"><button className="cancel-button" disabled={page === 1} onClick={() => changePage(page - 1)}>Previous</button><span>Page {page}</span><button className="cancel-button" disabled={page * 12 >= result.total} onClick={() => changePage(page + 1)}>Next</button></div>}
    </>}
  </main></div>;
}
