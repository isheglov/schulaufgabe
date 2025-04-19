# MatheCheck

MatheCheck is a web app that helps parents and children improve math skills using real school tests. Upload a photo of a graded math test, and the app generates a new, similar worksheet in LaTeX format for print.

## Features
- Upload JPG, PNG, or PDF of a math test
- FastAPI backend saves uploads and returns a session ID
- Next.js frontend with file upload and preview

---

## Project Structure
- `components/` – React components (frontend)
- `pages/` – Next.js pages (frontend)
- `backend/` – FastAPI backend (Python)

---

## Prerequisites
- Node.js (v18+ recommended)
- Python 3.8+

---

## Frontend: Next.js

### Install dependencies
```bash
npm install
```

### Run the development server
```bash
npm run dev
```

App will be available at [http://localhost:3000](http://localhost:3000)

### Run linters (ESLint & TypeScript)
```bash
# Run ESLint
npx eslint . --ext .ts,.tsx

# Run TypeScript type check
npx tsc --noEmit
```

### Run frontend tests (Playwright)
```bash
# Install Playwright and its browsers (only needed once)
npx playwright install --with-deps

# Run all Playwright tests
npx playwright test

# Run Playwright in UI mode (for debugging)
npx playwright test --ui
```

---

## Backend: FastAPI

### Create and activate a virtual environment
```bash
python3 -m venv backend/venv
# For bash/zsh:
source backend/venv/bin/activate
# For fish shell:
source backend/venv/bin/activate.fish
```

### Install dependencies
```bash
pip install -r backend/requirements.txt
```

### Run the FastAPI server
```bash
uvicorn main:app --reload --app-dir backend
```

API will be available at [http://localhost:8000/api/upload](http://localhost:8000/api/upload)

### Run backend linter (flake8)
```bash
pip install flake8
flake8 backend/
```

### Run backend tests (pytest)
```bash
pytest
```

---

## Deploying to Render (Free Hosting)

You can deploy both the frontend (Next.js) and backend (FastAPI) to [Render](https://render.com/) for free:

### Backend (FastAPI)
1. Push your code to GitHub.
2. Go to Render, click "New +" → "Web Service".
3. Connect your GitHub repo and set the root directory to `backend`.
4. Set the build command:
   ```bash
   pip install -r requirements.txt
   ```
5. Set the start command:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 10000
   ```
6. Set the environment to Python 3.10.
7. Click "Create Web Service".

### Frontend (Next.js)
1. Go to Render, click "New +" → "Web Service" (or "Static Site" for static export).
2. Set the root directory to the project root (leave blank if at root).
3. Set the build command:
   ```bash
   npm install && npm run build
   ```
4. Set the start command:
   ```bash
   npm start
   ```
5. Set the environment to Node 18.
6. Set environment variables as needed (e.g., `NEXT_PUBLIC_API_URL` to your backend's Render URL).
7. Click "Create Web Service".

Render will auto-deploy on every push to GitHub.
