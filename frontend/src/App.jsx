import { useEffect, useState } from "react";

function App() {
  const [blogs, setBlogs] = useState([]);

  useEffect(() => {
    fetch("https://blog-api-ecef21cc.fastapicloud.dev/blogs")
      .then((response) => response.json())
      .then((data) => {
        setBlogs(data); // Changed from data.data to data
      });
  }, []);

  return (
    <div>
      <h1>My Blog</h1>
      {blogs.map((blog) => (
        <div key={blog.id}>
          <h2>{blog.title}</h2>
          <p>{blog.content}</p>
        </div>
      ))}
    </div>
  );
}

export default App;