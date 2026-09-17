import { useEffect, useState } from "react";

const API_BASE_URL = "https://blog-api-ecef21cc.fastapicloud.dev";
const API_URL = `${API_BASE_URL}/blogs`;

async function getErrorMessage(response, fallback) {
  const data = await response.json().catch(() => null);

  if (typeof data?.detail === "string") {
    return data.detail;
  }

  if (Array.isArray(data?.detail)) {
    return data.detail.map((item) => item.msg).join("; ");
  }

  return fallback;
}

function App() {
  const [blogs, setBlogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");

  const [showCreateForm, setShowCreateForm] = useState(false);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [createError, setCreateError] = useState("");

  const [token, setToken] = useState("");
  const [loggingIn, setLoggingIn] = useState(false);

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  async function handleLogin() {
  if (!username.trim() || !password) {
    setCreateError("Enter your username and password.");
    return;
  }

  setLoggingIn(true);
  setCreateError("");

  try {
    const response = await fetch(`${API_BASE_URL}/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({
        username: username.trim(),
        password,
      }),
    });

    if (!response.ok) {
      throw new Error(
        await getErrorMessage(
          response,
          "Login failed. Please try again."
        )
      );
    }

    const data = await response.json();

    if (
      typeof data.access_token !== "string" ||
      !data.access_token.trim()
    ) {
      throw new Error("Login did not return an access token.");
    }

    setToken(data.access_token);
    setPassword("");
  } catch (error) {
    setCreateError(error.message);
  } finally {
    setLoggingIn(false);
  }
}

  async function handleCreatePost(event) {
    event.preventDefault();

    if (!token) {
      setCreateError("Log in before publishing your post.");
      return;
    }

    if (!title.trim() || !content.trim()) {
      setCreateError("Title and content are required.");
      return;
    }

    try {
      setSubmitting(true);
      setCreateError("");

      const response = await fetch(API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          title,
          content,
        }),
      });

      if (!response.ok) {
        if (response.status === 401) {
          setToken("");

          throw new Error(
            "Your session expired or is invalid. Log in again; your draft is still here."
          );
        }

        throw new Error(
          await getErrorMessage(
            response,
            "Failed to create post. Please try again."
          )
        );
      }

      await loadBlogs();

      setTitle("");
      setContent("");
      setShowCreateForm(false);
    } catch (error) {
      setCreateError(error.message);
    } finally {
      setSubmitting(false);
    }
  }

  async function loadBlogs() {
    try {
      setLoading(true);

      const response = await fetch(API_URL);

      if (!response.ok) {
        throw new Error("Failed to load blogs");
      }

      const data = await response.json();

      setBlogs(data.data);
      setError("");
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadBlogs();
  }, []);

  const filteredBlogs = blogs.filter((blog) => {
    const searchText = search.toLowerCase();

    return (
      blog.title.toLowerCase().includes(searchText) ||
      blog.content.toLowerCase().includes(searchText)
    );
  });

  return (
    <div className="app">
      {/* NAVBAR */}
      <nav className="navbar">
        <div className="logo">
          <span className="logo-icon">◫</span>
          <span>My Blog</span>
        </div>

        <div className="nav-links">
          <a className="active" href="#">
            Home
          </a>
          <a href="#posts">Posts</a>
          <a href="#">About</a>
        </div>

        <div className="nav-actions">
          <input
            type="text"
            placeholder="Search posts..."
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />

          <button
            className="new-post-button"
            onClick={() => setShowCreateForm(true)}
          >
            + New Post
          </button>
        </div>
      </nav>

      {/* HERO */}
      <section className="hero">
        <div className="hero-content">
          <div className="tech-badge">
            ● Powered by FastAPI + Supabase
          </div>

          <h1>
            Ideas. Code. <span>Progress.</span>
          </h1>

          <p>
            A space for ideas, experiments, and the journey of building
            something meaningful with React, FastAPI and Supabase.
          </p>

          <div className="hero-buttons">
            <a href="#posts" className="primary-button">
              Read latest posts →
            </a>

            <button className="secondary-button">Learn more</button>
          </div>
        </div>

        <div className="hero-visual">
          <div className="code-window">
            <div className="window-buttons">
              <span></span>
              <span></span>
              <span></span>
            </div>

            <pre>
              {`> Build
> Share
> Grow
> Repeat_`}
            </pre>
          </div>

          <div className="floating-card fastapi">
            FastAPI
            <small>Backend API</small>
          </div>

          <div className="floating-card supabase">
            Supabase
            <small>PostgreSQL</small>
          </div>
        </div>
      </section>

      {/* SEARCH */}
      <section className="search-section">
        <div className="big-search">
          <span>⌕</span>

          <input
            type="text"
            placeholder="Search blog posts..."
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>

        <div className="categories">
          <button className="selected">All</button>
          <button>Tech</button>
          <button>Updates</button>
          <button>Thoughts</button>
          <button>Life</button>
        </div>
      </section>

      {/* CONTENT */}
      <main className="content-layout" id="posts">
        <section className="posts-section">
          <div className="section-heading">
            <div>
              <span className="section-label">LATEST POSTS</span>
              <h2>From the Blog</h2>
            </div>

            <span>{filteredBlogs.length} posts</span>
          </div>

          {loading && (
            <div className="status-card">
              <p>Loading posts...</p>
            </div>
          )}

          {error && (
            <div className="status-card error">
              <p>{error}</p>
            </div>
          )}

          {!loading && !error && filteredBlogs.length === 0 && (
            <div className="status-card">
              <p>No posts found.</p>
            </div>
          )}

          <div className="posts-list">
            {filteredBlogs.map((blog) => (
              <article className="post-card" key={blog.id}>
                <div className="post-thumbnail">
                  <span>&lt;/&gt;</span>
                </div>

                <div className="post-content">
                  <span className="post-category">DEVELOPMENT</span>

                  <h3>{blog.title}</h3>
                  <p>{blog.content}</p>

                  <div className="post-meta">
                    <span>Post #{blog.id}</span>
                    <span>•</span>
                    <span>FastAPI Blog</span>
                  </div>
                </div>

                <button className="post-arrow">→</button>
              </article>
            ))}
          </div>
        </section>

        {/* SIDEBAR */}
        <aside className="sidebar">
          <div className="sidebar-card">
            <div className="sidebar-icon">✉</div>

            <h3>Stay in the loop</h3>
            <p>Get new posts delivered to your inbox.</p>

            <input type="email" placeholder="Your email address" />
            <button>Subscribe</button>

            <small>No spam. Unsubscribe anytime.</small>
          </div>

          <div className="sidebar-card">
            <h3>Popular Topics</h3>

            <div className="topic-list">
              <span>Development</span>
              <span>FastAPI</span>
              <span>Supabase</span>
              <span>Python</span>
              <span>Ideas</span>
            </div>
          </div>

          <div className="quote-card">
            <span className="quote">"</span>
            <p>A little progress each day adds up to big results.</p>
          </div>
        </aside>
      </main>

      {/* FOOTER */}
      <footer>
        <div>
          <strong>My Blog</strong>
          <p>Thoughts, ideas and updates.</p>
        </div>

        <div className="footer-links">
          <a href="#">Home</a>
          <a href="#posts">Posts</a>
          <a href="#">About</a>
        </div>

        <p>Built with React, FastAPI & Supabase</p>
      </footer>

      {/* CREATE POST MODAL */}
      {showCreateForm && (
        <div className="modal-overlay">
          <div className="create-modal">
            <div className="modal-header">
              <div>
                <span className="section-label">CREATE</span>
                <h2>New Post</h2>
              </div>

              <button
                className="close-button"
                onClick={() => setShowCreateForm(false)}
                aria-label="Close"
              >
                ×
              </button>
            </div>

            <form onSubmit={handleCreatePost}>
            {!token && (
              <div className="status-card">
                <p>
                  Use demo login before publishing. This demo does not
                  check a username or password.
                </p>

                <button
                  type="button"
                  className="publish-button"
                  onClick={handleLogin}
                  disabled={loggingIn}
                >
                  {loggingIn ? "Logging in..." : "Demo login"}
                </button>
              </div>
            )}

            {token && (
              <div className="status-card">
                <p>You are logged in.</p>

                <button
                  type="button"
                  className="cancel-button"
                  disabled={submitting}
                  onClick={() => {
                    setToken("");
                    setPassword("");
                    setCreateError("");
                  }}
                >
                  Log out
                </button>
              </div>
            )}

              <label htmlFor="post-title">Title</label>
              <input
                id="post-title"
                type="text"
                placeholder="Enter post title"
                value={title}
                onChange={(event) => setTitle(event.target.value)}
              />

              <label htmlFor="post-content">Content</label>
              <textarea
                id="post-content"
                placeholder="Write your post..."
                value={content}
                onChange={(event) => setContent(event.target.value)}
                rows="7"
              />

              {createError && (
                <p className="create-error" role="alert">
                  {createError}
                </p>
              )}

              <div className="form-buttons">
                <button
                  type="button"
                  className="cancel-button"
                  onClick={() => setShowCreateForm(false)}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="publish-button"
                  disabled={submitting || loggingIn || !token}
                >
                  {submitting ? "Publishing..." : "Publish Post"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;