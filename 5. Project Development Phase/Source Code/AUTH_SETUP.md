# What was added

This adds authentication, a database, prediction history, and input
validation on top of the original flood-prediction Flask app.

## New files
- `extensions.py` — shared `db`, `login_manager`, `csrf` instances
- `models.py` — `User` (accounts) and `Prediction` (history) tables
- `forms.py` — WTForms for register/login/predict, with server-side validation
- `templates/login.html`, `templates/register.html`, `templates/history.html`
- `templates/partials/nav.html`, `templates/partials/flash.html` — shared navbar & flash messages
- `templates/errors/404.html`, `templates/errors/500.html`
- `.env.example` — copy to `.env` and fill in real values

## Changed
- `app.py` — rewritten with routes for register/login/logout/history/delete,
  `/predict` now requires login, validates input server-side, and saves each
  prediction to the database instead of just rendering a result page.
- `requirements.txt` — added Flask-SQLAlchemy, Flask-Login, Flask-WTF, WTForms,
  email-validator, python-dotenv.
- `static/main.css` — added styles for form errors, flash messages, the
  history table, and badges (reused your existing panel/field/btn classes).
- `home.html`, `predict.html`, `chance.html`, `no_chance.html` — nav swapped
  for the shared `partials/nav.html` include (adds Login/Sign up/History
  links) and flash messages added.

## Google sign-in ("Continue with Google")
Added via Authlib. To enable it:
1. Create OAuth credentials in the Google Cloud Console (APIs & Services →
   Credentials → OAuth client ID → Web application), with this redirect URI
   for local dev: `http://127.0.0.1:5000/login/google/callback`
2. Copy the Client ID and Client Secret into your `.env`:
   ```
   GOOGLE_CLIENT_ID=...
   GOOGLE_CLIENT_SECRET=...
   ```
3. Restart the app. The "Continue with Google" button appears automatically
   on the login/register pages once both values are set — if they're blank,
   the button is hidden and the app runs as normal email/password-only.

Accounts created via Google have no local password (`password_hash` is
nullable). If someone signs up with email/password first and later clicks
"Continue with Google" using the same email, the accounts get linked
automatically instead of creating a duplicate.

For production, add your live domain's callback URL
(`https://yourdomain.com/login/google/callback`) as an additional
Authorized redirect URI in the Google Cloud Console.

## Running locally
```bash
cp .env.example .env          # then edit SECRET_KEY
pip install -r requirements.txt
python app.py                 # creates floods.db automatically on first run
```
Visit `http://127.0.0.1:5000`. Register an account, then `/predict` is
available — every prediction you make is saved to `/history` where you can
also delete it.

## Notes / what to know before deploying
- The SQLite database lives in `instance/floods.db` (Flask's default
  location) and is git-ignored. For a real deployment, set `DATABASE_URL`
  to a Postgres connection string instead (e.g. Heroku/Render add-ons) —
  SQLite files don't survive redeploys on most hosting platforms.
- Set a strong, random `SECRET_KEY` in production — sessions and CSRF
  tokens are signed with it.
- If the model/scaler files fail to load, the app still starts (so
  login/history keep working) but `/predict` shows a friendly "unavailable"
  message instead of crashing.
- Not yet added, worth doing next: password-reset emails, rate limiting
  on login/register, and a `/api/predict` JSON endpoint — happy to build
  any of those next.
