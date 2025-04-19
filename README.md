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
pip install fastapi uvicorn aiofiles python-multipart
```

### Run the FastAPI server
```bash
uvicorn main:app --reload --app-dir backend
```

API will be available at [http://localhost:8000/api/upload](http://localhost:8000/api/upload)

---

## Example: Upload a file via curl
```bash
curl -F "file=@/path/to/your/test.jpg" http://localhost:8000/api/upload
```

---

## Linting & Code Style

### Frontend (TypeScript/Next.js)

1. Install dependencies (if not already):
   ```bash
   npm install
   ```
2. Run ESLint:
   ```bash
   npx eslint . --ext .ts,.tsx
   ```

### Backend (Python)

1. Activate your virtual environment:
   ```bash
   source backend/venv/bin/activate
   # or for fish shell:
   source backend/venv/bin/activate.fish
   ```
2. Install flake8 and black (if not already):
   ```bash
   pip install flake8 black
   ```
3. Run flake8:
   ```bash
   flake8 backend/
   ```
4. Run black (to check formatting):
   ```bash
   black --check backend/
   ```
   (or to auto-format: `black backend/`)

---

## License
MIT 