# Publish the frontend on Vercel

The frontend runs on Vercel; the backend remains on FastAPI Cloud. Deployment is manual.

1. Push the intended frontend changes to your GitHub repository using your normal workflow.
2. In Vercel, choose Add New Project and import `M-DaniyalHS1/blog_api_project`.
3. Set Root Directory to `frontend`, Framework Preset to Vite, Build Command to `npm run build`, and Output Directory to `dist`.
4. Set the frontend environment variable `VITE_API_BASE_URL` to `https://blog-api-ecef21cc.fastapicloud.dev` (no trailing slash). Do not add backend secrets such as Gemini keys, database credentials, or SECRET_KEY to Vercel's frontend environment.
5. Deploy and copy the production URL Vercel assigns to the project.
6. In your FastAPI Cloud backend environment, set `CORS_ORIGINS` to `http://localhost:5173,https://YOUR-PROJECT.vercel.app`, replacing the example with that exact production origin (no path).
7. Manually redeploy the backend with the updated `main.py`. It must include the new CORS configuration code.
8. Open the production URL in a private browser window. Check posts, registration/login, article links, comments/likes, the chatbot, and the writing assistant. Check on a phone too.

Only explicitly listed origins are allowed. Add a custom domain or specific preview URL to CORS_ORIGINS if needed; do not allow every vercel.app site. Frontend environment changes need a new frontend deployment. Backend environment changes need a backend restart/redeployment.

The app uses hash URLs such as `/#/posts/15`; these do not require a Vercel SPA rewrite. Share the production domain rather than a temporary preview deployment. If Vercel requests login from visitors, check the deployment protection settings for your production deployment.

Reference: https://vercel.com/docs/frameworks/frontend/vite
