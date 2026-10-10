# WAEC/NECO Maths Assist — Deployment Guide

This is a Flask web app (Progressive Web App). It runs locally out of the box,
and this guide shows the fastest way to put it on a free, permanent HTTPS link
so your students can install it and you can monitor their progress.

## What's inside
- `app.py` — the Flask application (routes, auth, dashboards)
- `db.py` — SQLite database setup and helpers
- `solvers.py` — all the maths solvers (Algebra, Geometry, Graphs), ported from
  the desktop app, using sympy for step-by-step working
- `templates/` — all the HTML pages
- `static/` — CSS, JS, the PWA manifest, service worker, and app icons
- `requirements.txt`, `Procfile` — for deployment

## Run it locally first (optional but recommended)
```
cd maths_pwa
pip install -r requirements.txt
python app.py
```
Then open http://127.0.0.1:5000 in your browser. The database file
(`maths_assist.db`) is created automatically on first run.

## Deploying to Render (free, ~5 minutes)

1. **Put the code on GitHub.**
   Create a new repository and push the `maths_pwa` folder's contents to it
   (it already has a `.gitignore` set up).

2. **Create a Render account** at render.com (free, no card required for the
   free web service tier).

3. **New → Web Service**, connect your GitHub repo.

4. Render should auto-detect Python. Set:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app` (already in the `Procfile`, so
     Render should pick this up automatically)

5. **Add environment variables** (Render dashboard → Environment):
   - `SECRET_KEY` — any long random string (used to sign login sessions)
   - `TEACHER_SIGNUP_CODE` — a code you choose and keep private; only people
     who know this code can register as a teacher. Change this from the
     default (`TEACHME123`) before going live.

6. Click **Deploy**. Render gives you a URL like
   `https://maths-assist-yourname.onrender.com` — that's your permanent link.

7. **Important — persistent storage:** Render's free tier has an ephemeral
   filesystem, meaning the SQLite database (student accounts + progress) can
   reset if the service restarts or redeploys. For a real classroom rollout,
   add a Render **Disk** (Render dashboard → your service → Disks → Add Disk,
   mount it at `/opt/render/project/src`, 1GB is plenty and free) so the
   database persists. Without this, treat it as a demo/testing deploy only.

## Sharing the link with students
Once deployed, send students the URL. On a phone, opening it in Chrome/Safari
and choosing "Add to Home Screen" (or the install prompt that appears)
installs it like a regular app, using the icon and name from the manifest.

## Setting up your teacher account
Go to `<your-url>/teacher/register`, enter your name, a username/password,
and the `TEACHER_SIGNUP_CODE` you set in step 5. That gives you access to
`/teacher/dashboard` — the class-wide view (active students, activity trend,
topic engagement, most-used tools, full roster) and a drill-down page per
student.

## Alternative hosts
The app has no Render-specific code — `requirements.txt` + `Procfile` work
the same way on Railway, Fly.io, or PythonAnywhere (PythonAnywhere doesn't
use gunicorn/Procfile — instead point its WSGI config at `app.app` from
`app.py`). Any host that persists a disk and runs Python 3.10+ will work.

## Extending it later
- The `Sequence`, `Sets`, `Trigonometry`, and `Calculus` sections from the
  desktop app aren't ported yet — `solvers.py` is the place to add them,
  following the same pattern as the existing functions.
- Grading (right/wrong tracking) currently isn't wired up — `attempts.correct`
  exists in the schema for this, but every solve is logged as ungraded
  (`correct = NULL`) since these are worked-solution tools, not quizzes.
  If you want practice questions with a known answer to check against, that's
  the column to use.
