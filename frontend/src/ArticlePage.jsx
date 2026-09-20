import { useEffect, useState } from "react";

export default function ArticlePage({ id, apiUrl }) {
  const [post, setPost] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(Boolean(id));
  const [attempt, setAttempt] = useState(0);
  const [imageFailed, setImageFailed] = useState(false);

  useEffect(() => {
    if (!id) return;
    const controller = new AbortController();
    async function load() {
      try {
        const response = await fetch(`${apiUrl}/${id}`, { signal: controller.signal });
        if (!response.ok) {
          throw new Error(response.status === 404 ? "This post could not be found." : "We couldn’t load this story. Please try again.");
        }
        const data = await response.json();
        if (!controller.signal.aborted) setPost(data);
      } catch (err) {
        if (!controller.signal.aborted) setError(err.message === "Failed to fetch" ? "Unable to connect. Check your connection and try again." : err.message);
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }
    load();
    return () => controller.abort();
  }, [id, apiUrl, attempt]);

  useEffect(() => {
    document.title = post ? `${post.title} | Dani Blogs` : "Read a story | Dani Blogs";
    return () => { document.title = "Dani Blogs"; };
  }, [post]);

  const date = post?.published_at ? new Date(post.published_at) : null;
  const validDate = date && !Number.isNaN(date.getTime());
  const source = /^https?:\/\//i.test(post?.source_url || "") ? post.source_url : null;

  return (
    <div className="app">
      <nav className="navbar" aria-label="Article navigation">
        <a className="logo" href="#home"><img className="logo-image" src="/pics/logo.png" alt="" /><span>Dani Blogs</span></a>
        <a className="read-link article-back" href="#posts">All posts &rarr;</a>
      </nav>
      <main className="article-page">
        <a className="read-link" href="#posts">&larr; Back to posts</a>
        {loading && <p className="article-status" role="status">Loading story…</p>}
        {(!id || error) && (
          <div className="article-status" role="alert">
            <h1>{!id ? "Page not found" : "Story unavailable"}</h1>
            <p>{!id ? "This article link is not valid." : error}</p>
            {id && <button className="secondary-button" onClick={() => { setError(""); setLoading(true); setAttempt(attempt + 1); }}>Try again</button>}
          </div>
        )}
        {!loading && !error && post && (
          <article>
            <header className="article-header">
              <span className="section-label">DANI BLOGS</span>
              <h1>{post.title}</h1>
              {post.author && <p className="article-date"><a href={`#/authors/${post.author.id}`}>By {post.author.display_name || post.author.username}</a></p>}
              {post.summary?.trim() && <p className="article-summary">{post.summary}</p>}
              {validDate ? <time dateTime={post.published_at}>{date.toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" })}</time> : <p className="article-date">Publication date unavailable</p>}
            </header>
            {post.image_url && (imageFailed ? <p className="article-date">Article image unavailable.</p> : <img className="article-image" src={post.image_url} alt={`Image for ${post.title}`} referrerPolicy="no-referrer" onError={() => setImageFailed(true)} />)}
            <div className="article-body">{post.content.split(/\r?\n\s*\r?\n/).filter((paragraph) => paragraph.trim()).map((paragraph, index) => <p key={index}>{paragraph}</p>)}</div>
            {source && <div className="article-source"><span className="section-label">SOURCE</span><a href={source} target="_blank" rel="noopener noreferrer">Read the original source ↗</a></div>}
          </article>
        )}
      </main>
    </div>
  );
}
