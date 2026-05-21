# CJPHub Production Deployment Guide

This guide details the step-by-step instructions to deploy **CJPHub** (`cjphub.com` / `cjp.lol`) to the public internet using a resilient, scalable, and cost-effective modern cloud infrastructure.

---

## 🏗️ Production Architecture Map

```
┌────────────────────────────────────────────────────────┐
│                    GitHub Repository                   │
└──────────────────────────┬─────────────────────────────┘
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
┌─────────────────────────┐ ┌─────────────────────────┐
│     Next.js Frontend    │ │     FastAPI Backend     │
│       (on Vercel)       │ │   (Docker on Render)    │
└────────────┬────────────┘ └────────────┬────────────┘
             │                           │
             │ HTTP API Requests         │ SQL Queries &
             └──────────────────────────►│ pgvector calculations
                                         ▼
                            ┌─────────────────────────┐
                            │    Managed Postgres     │
                            │  (Supabase / Neon)      │
                            └─────────────────────────┘
```

---

## Step 1: Set Up Managed PostgreSQL Database (with `pgvector`)

Because the observatory relies on vector similarity clustering for grouping and tracing narratives, your database must support the `pgvector` extension. 

### A. Choose a Provider (Supabase or Neon)
*   **Option 1: Supabase (Recommended)**
    1. Sign up/log in to [Supabase](https://supabase.com).
    2. Create a new project named `cjphub`.
    3. Go to **Database** -> **Extensions**, search for `vector`, and toggle it **ON**.
*   **Option 2: Neon**
    1. Sign up/log in to [Neon](https://neon.tech).
    2. Create a new project. `pgvector` is enabled by default.

### B. Retrieve your Connection String
1. In your database dashboard (Supabase or Neon), find the connection settings.
2. Copy the **URI/Connection String** (Transaction mode / Port `5432` or pooler connection).
3. It should look like this:
   `postgresql://postgres:[YOUR-PASSWORD]@db.[REF].supabase.co:5432/postgres`

---

## Step 2: Deploy the FastAPI Backend (Docker Container)

We have created a production-ready `Dockerfile` in the `/backend` directory. This makes deployment on container-based hosting services completely automatic.

### A. Choose a Hosting Provider (Render or Railway)
*   **Option 1: Render (Recommended)**
    1. Sign up/log in to [Render](https://render.com).
    2. Click **New +** -> **Web Service**.
    3. Connect your GitHub repository.
    4. Set **Root Directory** to `backend`.
    5. Set **Runtime** to `Docker` (Render automatically detects `/backend/Dockerfile`).
*   **Option 2: Railway**
    1. Sign up/log in to [Railway](https://railway.app).
    2. Create a new project and select **Deploy from GitHub**.
    3. Set **Root Directory** to `backend`. Railway will build the Docker container automatically.

### B. Add Environment Variables
Add the following key-value pairs in the **Environment Variables** section of your hosting provider:

| Variable | Recommended Value / Notes |
| :--- | :--- |
| `DATABASE_URL` | Your Supabase/Neon PostgreSQL URI (from Step 1) |
| `GEMINI_API_KEY` | Your Gemini API Key (for cluster synthesis & summaries) |
| `PORT` | `8000` (Render/Railway binds this port automatically) |
| `DEBUG` | `False` |
| `REDDIT_CLIENT_ID` | *Optional* (Required only if running live Reddit scraper) |
| `REDDIT_CLIENT_SECRET` | *Optional* (Required only if running live Reddit scraper) |
| `REDDIT_USER_AGENT` | *Optional* (Required only if running live Reddit scraper) |

### C. Deploy & Save API URL
1. Click **Deploy Web Service**.
2. Once the service builds and is healthy, copy the public URL provided by Render (e.g., `https://cjp-backend.onrender.com`).
3. Verify it is live by opening `https://your-backend-url.onrender.com/` in your browser (it should return `{"status":"online",...}`).

---

## Step 3: Run Database Migrations & Seed Data

Now that the backend is connected to the PostgreSQL database, we need to build the tables and load seed data.

### Method A: Automatic Schema Creation
*   FastAPI is configured to run `Base.metadata.create_all(bind=engine)` automatically when the backend server boots up in production. This will instantly build all 15 tables inside your remote Postgres database.

### Method B: Run Seed Script (Highly Recommended)
To populate your production database with the initial 100+ telemetry logs, narratives, and verified timelines:
1. Open your terminal locally.
2. In your `/backend` directory, temporarily change `DATABASE_URL` in your local `.env` to point to your new remote Supabase database connection string.
3. Run the Python seed command:
   ```bash
   python -m app.seed
   ```
4. Restore your local `.env` back to using the local SQLite file (`sqlite:///./cjphub.db`) for development.

---

## Step 4: Deploy the Next.js Frontend to Vercel

Vercel is the native hosting platform for Next.js and provides instant global edge routing, automatic SSL/TLS certificates, and performance optimization.

### A. Initialize Deployment
1. Sign up/log in to [Vercel](https://vercel.com).
2. Click **Add New** -> **Project**.
3. Select and import your GitHub repository.
4. Configure the Project settings:
   *   **Framework Preset:** Next.js
   *   **Root Directory:** Edit and set to `frontend`

### B. Add Environment Variables
Add the following environment variable to link the frontend to your live backend:

| Key | Value |
| :--- | :--- |
| `NEXT_PUBLIC_API_URL` | `https://your-backend-url.onrender.com` (from Step 2C) |

### C. Deploy
1. Click **Deploy**.
2. Vercel will compile, optimize, and build the Next.js production bundle.
3. Once completed, your observatory dashboard is **LIVE**! You will be given a public URL (e.g., `https://cjp-frontend.vercel.app`).

---

## Step 5: Connect Custom Domains (Optional)
Once deployed, you can assign your custom domains (`cjphub.com` or `cjp.lol`):
*   **For Frontend (Vercel):** Go to Project Settings -> **Domains**, add `cjphub.com` or `cjp.lol`, and follow Vercel's instructions to add `CNAME`/`A` records at your domain registrar.
*   **For Backend (Render):** Go to Settings -> **Custom Domains** if you wish to run your API at `api.cjphub.com`.

---

> [!TIP]
> **Adversarial & Scraper Schedulers in Production:** 
> In production, you can set up a CRON job (using Render Cron Services, GitHub Actions, or Vercel Crons) that calls your backend `/api/v1/collect` or scheduler endpoint to regularly refresh and cluster community stream content.
