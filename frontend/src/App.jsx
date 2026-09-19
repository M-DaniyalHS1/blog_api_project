import ArticlePage from "./ArticlePage.jsx";
import { useEffect, useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "https://blog-api-ecef21cc.fastapicloud.dev";
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

function BlogImage({ url, preview = false }) {
  const [failed, setFailed] = useState(false);
  if (!url || failed) {
    return <span>{preview ? "Image could not load. Check that the URL links directly to a public image." : "Dani Blogs"}</span>;
  }
  return (
    <img
      src={url}
      alt={preview ? "Post image preview" : ""}
      loading="lazy"
      referrerPolicy="no-referrer"
      onError={() => setFailed(true)}
    />
  );
}

function validImageUrl(value) {
  try {
    const url = new URL(value);
    return url.protocol === "https:" || url.protocol === "http:";
  } catch {
    return false;
  }
}

function HomeApp() {
  const [blogs, setBlogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");

  const [showCreateForm, setShowCreateForm] = useState(false);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [summary, setSummary] = useState("");
  const [imageUrl, setImageUrl] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [createError, setCreateError] = useState("");

  const [token, setToken] = useState("");
  const [loggingIn, setLoggingIn] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [sessionExpiresAt, setSessionExpiresAt] = useState(0);
  const [authMode, setAuthMode] = useState("login");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [authOnly, setAuthOnly] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  useEffect(() => {
    if (!token || !sessionExpiresAt) return;
    const timer = setTimeout(() => {
      setToken("");
      setCurrentUser(null);
      setAuthMode("login");
      setCreateError("Your session expired. Log in again; your draft is still here.");
    }, Math.max(0, sessionExpiresAt - Date.now()));
    return () => clearTimeout(timer);
  }, [token, sessionExpiresAt]);

  async function handleLogin(event) {
  event.preventDefault();
  if (loggingIn) return;
  if (!username.trim() || !password) {
    setCreateError("Enter your username and password.");
    return;
  }

  if (authMode === "register" && password !== confirmPassword) {
    setCreateError("Passwords do not match.");
    return;
  }
  setLoggingIn(true);
  setCreateError("");

  try {
    if (authMode === "register") {
      const registered = await fetch(`${API_BASE_URL}/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: username.trim(), password }),
      });
      if (!registered.ok) throw new Error(await getErrorMessage(registered, "Could not create your account. Try again."));
      setAuthMode("login");
    }
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
      if (response.status === 401) {
        throw new Error("Wrong username or password.");
      }
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
    setCurrentUser(data.user);
    setSessionExpiresAt(Date.now() + (data.expires_in || 1800) * 1000);
    setPassword("");
    setConfirmPassword("");
    if (authOnly) setShowCreateForm(false);
  } catch (error) {
    setCreateError(error.message);
  } finally {
    setLoggingIn(false);
  }
}

  function openAuth(mode, only = true) {
    setAuthMode(mode);
    setAuthOnly(only);
    setCreateError("");
    setPassword("");
    setConfirmPassword("");
    setShowCreateForm(true);
  }

  async function handleLogout() {
    if (loggingOut) return;
    setLoggingOut(true);
    try {
      const response = await fetch(`${API_BASE_URL}/logout`, {
        method: "POST", headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok && response.status !== 401) throw new Error("Logout failed. Please try again.");
      setToken("");
      setCurrentUser(null);
      setPassword("");
      setConfirmPassword("");
      setCreateError("");
      setShowCreateForm(false);
    } catch {
      setCreateError("Could not log out. Check your connection and try again.");
      setShowCreateForm(true);
    } finally {
      setLoggingOut(false);
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

    if (imageUrl.trim() && !validImageUrl(imageUrl.trim())) {
      setCreateError("Enter a valid image URL starting with https:// or http://.");
      return;
    }

    if (sourceUrl.trim() && !validImageUrl(sourceUrl.trim())) {
      setCreateError("Enter a source URL starting with https:// or http://.");
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
          summary: summary.trim() || null,
          image_url: imageUrl.trim() || null,
          source_url: sourceUrl.trim() || null,
        }),
      });

      if (!response.ok) {
        if (response.status === 401) {
          setToken("");
          setCurrentUser(null);
          setAuthMode("login");

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
      setSummary("");
      setImageUrl("");
      setSourceUrl("");
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
      blog.content.toLowerCase().includes(searchText) ||
      (blog.summary || "").toLowerCase().includes(searchText)
    );
  });


  return (
    <div className="app" id="home">
      {/* NAVBAR */}
      <nav className="navbar">
      <div className="logo">
          <img
            className="logo-image"
            src="/pics/logo.png"
            alt="Dani Blogs logo"
          />
          <span>Dani Blogs</span>
        </div>

        <div className="nav-links">
          <a className="active" href="#home">
            Home
          </a>
          <a href="#posts">Posts</a>
          <a href="#about">About</a>
        </div>

        <div className="nav-actions">
          <input
            type="text"
            placeholder="Search posts..."
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />

          {!token ? (
            <div className="account-actions">
              <button className="account-link" onClick={() => openAuth("login")}>Log in</button>
              <button className="account-link" onClick={() => openAuth("register")}>Sign up</button>
            </div>
          ) : (
            <div className="account-actions">
              <span className="account-name">@{currentUser?.username}</span>
              <button className="account-link" disabled={loggingOut || submitting} onClick={handleLogout}>{loggingOut ? "Logging out…" : "Log out"}</button>
            </div>
          )}
          <button
            className="new-post-button"
            onClick={() => openAuth("login", false)}
          >
            + New Post
          </button>
        </div>
      </nav>

      {/* HERO */}
      <section className="hero">
        <div className="hero-content">
          <div className="welcome-badge">Welcome to Dani Blogs</div>
          <h1>Fresh stories. <span>Different voices.</span></h1>
          <p>Discover news, ideas, and perspectives from a growing community. Explore what’s happening and find stories worth reading.</p>
          <div className="hero-buttons">
            <a href="#posts" className="primary-button">Explore posts &rarr;</a>
            <a href="#about" className="secondary-button">About Dani Blogs</a>
          </div>
        </div>
        <div className="hero-collage">
          <img
            className="collage-art"
            src="/pics/community-collage.png"
            alt="A collage of a city at sunset, a newspaper reader, and friends gathering in a park"
            width="1280"
            height="1280"
            fetchPriority="high"
          />
          <span className="collage-topic collage-topic-news">News</span>
          <span className="collage-topic collage-topic-culture">Culture</span>
          <span className="collage-topic collage-topic-life">Life</span>
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
              <article className="post-card" id={`post-${blog.id}`} key={blog.id}>
                <div className="post-thumbnail">
                  <BlogImage key={blog.image_url || "placeholder"} url={blog.image_url} />
                </div>

                <div className="post-content">
                  <span className="post-category">BLOG POST</span>

                  <h3><a href={`#/posts/${blog.id}`}>{blog.title}</a></h3>
                  <p className="post-excerpt">{blog.summary?.trim() || (blog.content.length > 220 ? `${blog.content.slice(0, 220)}…` : blog.content)}</p>

                  <div className="post-meta">
                    <span>Post #{blog.id}</span>
                    <span>•</span>
                    <span>{blog.author ? `By ${blog.author.username}` : "Dani Blogs"}</span>
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
            <img className="about-portrait" src="/pics/logo.png" alt="Dani Blogs logo" />
            <h3>News, ideas, and perspectives</h3>
            <p>Explore stories, follow new ideas, and discover different views on the world around you.</p>
            <a className="read-link" href="#about">About Dani Blogs &rarr;</a>
          </div>

          <div className="quote-card">
            <span className="quote">"</span>
            <p>A little progress each day adds up to big results.</p>
          </div>
        </aside>
      </main>

      <section className="about-section" id="about" aria-labelledby="about-title">
        <img className="about-portrait" src="/pics/logo.png" alt="Dani Blogs logo" />
        <div>
          <span className="section-label">ABOUT THE PROJECT</span>
          <h2 id="about-title">About Dani Blogs</h2>
          <p>Dani Blogs brings news, ideas, and different perspectives together in one place. We’re building a community around stories worth reading and sharing, with space for a variety of topics and voices.</p>
          <a className="read-link" href="#posts">Find something to read &rarr;</a>
        </div>
      </section>

      {/* FOOTER */}
      <footer>
        <div>
          <strong>Dani Blogs</strong>
          <p>News, ideas, and perspectives.</p>
        </div>

        <div className="footer-links">
          <a href="#home">Home</a>
          <a href="#posts">Posts</a>
          <a href="#about">About</a>
        </div>

        <p>Fresh stories. Different voices.</p>
      </footer>

      {/* CREATE POST MODAL */}
      {showCreateForm && (
        <div className="modal-overlay">
          <div className={`create-modal${token ? "" : " login-modal"}`} role="dialog" aria-modal="true" aria-labelledby="modal-title">
            <div className="modal-header">
              <div>
                <span className="section-label">{token ? "CREATE" : "JOIN THE CONVERSATION"}</span>
                <h2 id="modal-title">{token ? "New Post" : authMode === "register" ? "Create an account" : "Welcome back"}</h2>
              </div>

              <button
                className="close-button"
                onClick={() => setShowCreateForm(false)}
                aria-label="Close"
              >
                ×
              </button>
            </div>

            <form onSubmit={token ? handleCreatePost : handleLogin}>
            {!token && (
                <div className="login-fields">
                  <p className="login-description">{authMode === "register" ? "Choose a username and password to start sharing your stories." : "Log in to write and publish your next post."}</p>

                  <label htmlFor="login-username">Username</label>
                  <input
                    id="login-username"
                    type="text"
                    autoComplete="username"
                    required
                    minLength={authMode === "register" ? 3 : undefined}
                    maxLength={authMode === "register" ? 32 : undefined}
                    pattern={authMode === "register" ? "[A-Za-z0-9_]+" : undefined}
                    title="Use letters, numbers, and underscores"
                    placeholder="Enter your username"
                    value={username}
                    onChange={(event) => setUsername(event.target.value)}
                    disabled={loggingIn}
                  />

                  <label htmlFor="login-password">Password</label>
                  <input
                    id="login-password"
                    type="password"
                    autoComplete={authMode === "register" ? "new-password" : "current-password"}
                    required
                    minLength={authMode === "register" ? 8 : undefined}
                    maxLength={128}
                    placeholder="Enter your password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    disabled={loggingIn}
                  />

                  {authMode === "register" && (
                    <>
                      <p className="image-help">Username: 3–32 letters, numbers, or underscores. Password: 8–128 characters.</p>
                      <label htmlFor="confirm-password">Confirm password</label>
                      <input id="confirm-password" type="password" autoComplete="new-password" required minLength={8} maxLength={128} value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} disabled={loggingIn} />
                    </>
                  )}
                  {createError && (
                    <p className="create-error" role="alert">{createError}</p>
                  )}

                  <button
                    type="submit"
                    className="publish-button login-submit"
                    disabled={loggingIn}
                  >
                    {loggingIn ? "Please wait…" : authMode === "register" ? "Create account" : "Log in"}
                  </button>
                  <button type="button" className="auth-switch" disabled={loggingIn} onClick={() => { setAuthMode(authMode === "login" ? "register" : "login"); setCreateError(""); setPassword(""); setConfirmPassword(""); }}>
                    {authMode === "login" ? "New here? Create an account" : "Already have an account? Log in"}
                  </button>
                </div>
              )}

            {token && (
              <div className="session-bar">
                <p>Logged in as <strong>{currentUser?.username}</strong></p>

                <button
                  type="button"
                  className="cancel-button"
                  disabled={submitting || loggingOut}
                  onClick={handleLogout}
                >
                  Log out
                </button>
              </div>
            )}

              {token && (
                <>
              <label htmlFor="post-title">Title</label>
              <input
                id="post-title"
                type="text"
                placeholder="Enter post title"
                value={title}
                onChange={(event) => setTitle(event.target.value)}
              />

              <label htmlFor="post-image">Picture URL <span className="optional-label">(optional)</span></label>
              <input
                id="post-image"
                type="url"
                placeholder="https://example.com/photo.jpg"
                value={imageUrl}
                onChange={(event) => setImageUrl(event.target.value)}
                aria-describedby="image-help"
              />
              <p id="image-help" className="image-help">Paste a direct link to a public image. HTTPS works best.</p>
              {validImageUrl(imageUrl.trim()) && (
                <div className="image-preview">
                  <BlogImage key={imageUrl.trim()} url={imageUrl.trim()} preview />
                </div>
              )}

              <label htmlFor="post-source">Source link <span className="optional-label">(optional)</span></label>
              <input id="post-source" type="url" placeholder="https://example.com/original-story" value={sourceUrl} onChange={(event) => setSourceUrl(event.target.value)} />

              <label htmlFor="post-summary">Short summary <span className="optional-label">(optional)</span></label>
              <textarea id="post-summary" className="summary-input" rows="3" maxLength={500} placeholder="A short introduction for the homepage card" value={summary} onChange={(event) => setSummary(event.target.value)} aria-describedby="summary-help" />
              <p id="summary-help" className="image-help">Up to 500 characters. If empty, the homepage uses the beginning of your article.</p>

              <label htmlFor="post-content">Full article</label>
              <textarea
                id="post-content"
                placeholder="Write the complete article here. Separate paragraphs with a blank line."
                value={content}
                onChange={(event) => setContent(event.target.value)}
                rows="10"
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
                </>
              )}
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

function App() {
  const [hash, setHash] = useState(window.location.hash);
  useEffect(() => {
    const updateRoute = () => {
      setHash(window.location.hash);
      if (window.location.hash.startsWith("#/posts/")) window.scrollTo(0, 0);
    };
    window.addEventListener("hashchange", updateRoute);
    return () => window.removeEventListener("hashchange", updateRoute);
  }, []);
  const match = hash.match(/^#\/posts\/([1-9]\d*)$/);
  const isArticle = hash.startsWith("#/");
  return (
    <>
      <div hidden={isArticle}><HomeApp /></div>
      {isArticle && <ArticlePage key={hash} id={match?.[1]} apiUrl={API_URL} />}
    </>
  );
}

export default App;
