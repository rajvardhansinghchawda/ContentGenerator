# EduFlow 🎓

> **AI-Powered Academic Content Automation Platform for Teachers**

EduFlow is a full-stack web application that empowers teachers to instantly generate high-quality academic content — pre-read documents, post-read documents, and quiz forms — using the **Groq AI** (LLaMA 3.3) and **Google Workspace APIs**. Teachers simply describe a topic, configure their preferences, and EduFlow handles the rest asynchronously via a Celery task queue, pushing the finished documents directly to their Google Drive and Google Forms.

---

## ✨ Features

- 🔐 **Google OAuth Login** — Seamless sign-in using institutional Google accounts
- 🤖 **AI Content Generation** — Powered by Groq (LLaMA 3.3 70B) to generate structured academic content instantly
- 📄 **Google Docs Integration** — Auto-creates Pre-read and Post-read documents in the teacher's Google Drive
- 📝 **Google Forms Integration** — Auto-creates quiz forms with MCQ, Short Answer, or Mixed question types
- ⚙️ **Asynchronous Processing** — Background job queue via Celery + Redis; no UI blocking
- 📊 **Job Dashboard** — Real-time tracking of job status (Pending → Processing → Completed/Failed)
- 🏫 **Subject Management** — Organize content generation by subject, class, and semester

---

## 🏗️ Architecture

```
eduflow/
├── backend/                   # Django REST API
│   ├── auth_app/              # Google OAuth + custom Teacher user model
│   ├── jobs/                  # Job & Subject models, Celery tasks, REST endpoints
│   ├── ai_engine/             # Groq client, prompt builder, content validator
│   ├── google_services/       # Google Docs, Forms, and Drive integration
│   └── config/                # Django settings and URL routing
│
└── frontend/                  # React + Vite SPA
    └── src/
        ├── pages/             # LoginPage, DashboardPage
        ├── components/        # Reusable UI components
        ├── context/           # React context (auth, etc.)
        ├── hooks/             # Custom React hooks
        └── services/          # Axios API service layer
```

### Content Generation Pipeline

```
Teacher submits job
       │
       ▼
[Django API] — creates Job (status: pending) → enqueues Celery task
       │
       ▼
[Celery Worker]
  1. Build AI Prompt     (ai_engine/prompt_builder.py)
  2. Call Groq API       (ai_engine/groq_client.py)
  3. Validate Content    (ai_engine/validators.py)
  4. Create Pre-Doc      (google_services/docs_creator.py)
  5. Create Post-Doc     (google_services/docs_creator.py)
  6. Create Quiz Form    (google_services/forms_creator.py)
  7. Update Job status → completed ✅
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, React Router v6, Axios, Tailwind CSS, Vite |
| Backend | Django 5, Django REST Framework |
| AI | Groq API (LLaMA 3.3 70B Versatile) |
| Task Queue | Celery 5 + Redis |
| Database | PostgreSQL |
| Auth | Google OAuth 2.0 (via `google-auth` + `google-auth-oauthlib`) |
| Google APIs | Google Docs API, Google Forms API, Google Drive API |
| Encryption | Fernet (for secure token storage) |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL
- Redis
- A [Google Cloud Project](https://console.cloud.google.com/) with the following APIs enabled:
  - Google Docs API
  - Google Forms API
  - Google Drive API
  - Google People API (for user info)
- A [Groq API key](https://console.groq.com/)

---

### 1. Clone the Repository

```bash
git clone https://github.com/rajvardhansinghchawda/ContentGenerator.git
cd eduflow
```

---

### 2. Backend Setup

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate    # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

#### Configure Environment Variables

Copy the example file and fill in your values:

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True` for development, `False` for production |
| `DATABASE_URL` | PostgreSQL connection URL |
| `GOOGLE_CLIENT_ID` | OAuth 2.0 Client ID from Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` | OAuth 2.0 Client Secret |
| `GOOGLE_REDIRECT_URI` | Authorized redirect URI (must match Cloud Console) |
| `TOKEN_ENCRYPTION_KEY` | Fernet key for encrypting stored OAuth tokens |
| `GROQ_API_KEY` | Your Groq API key |
| `GROQ_MODEL` | Model ID (default: `llama-3.3-70b-versatile`) |
| `REDIS_URL` | Redis connection URL (default: `redis://localhost:6379/0`) |
| `FRONTEND_URL` | Frontend origin (default: `http://localhost:5173`) |
| `CORS_ALLOWED_ORIGINS` | Comma-separated list of allowed frontend origins |

> **Generate a Fernet key:**
> ```bash
> python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
> ```

#### Run Migrations & Start Server

```bash
python manage.py migrate
python manage.py runserver
```

---

### 3. Start the Celery Worker

In a **separate terminal** (with the virtual environment activated):

```bash
cd backend
celery -A config worker --loglevel=info --pool=solo
```

> **Note:** The `--pool=solo` flag is recommended on Windows.

---

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend will be available at **http://localhost:5173**.

---

## 📖 Usage

1. Navigate to `http://localhost:5173` and click **Sign in with Google**.
2. Authorize EduFlow to access your Google Workspace (Docs, Forms, Drive).
3. On the **Dashboard**, click **New Generation**.
4. Fill in the topic, subtopics, difficulty, question count, and question type.
5. Submit the job — it will appear in your dashboard with a **Pending** status.
6. The Celery worker picks it up and begins generation. The status updates to **Processing**.
7. Once complete, the job card shows direct links to the generated **Pre-Doc**, **Post-Doc**, and **Quiz Form** in your Google Drive.

---

## 🧩 Key Modules

### `ai_engine`
| File | Purpose |
|---|---|
| `groq_client.py` | Authenticates and calls the Groq inference API |
| `prompt_builder.py` | Constructs structured system + user prompts from job parameters |
| `validators.py` | Validates and sanitizes AI-generated content before it is pushed to Google |

### `jobs`
| File | Purpose |
|---|---|
| `models.py` | `Job` and `Subject` database models |
| `tasks.py` | `generate_content_task` — the main Celery task orchestrating the pipeline |
| `views.py` | REST endpoints for creating and querying jobs |
| `serializers.py` | DRF serializers for Job/Subject |

### `google_services`
| Module | Purpose |
|---|---|
| `auth_manager.py` | Builds authenticated Google API service clients from stored teacher tokens |
| `docs_creator.py` | Creates Pre-read and Post-read documents in Google Docs |
| `forms_creator.py` | Creates quiz forms with auto-grading in Google Forms |

---

## 🔒 Security Notes

- OAuth tokens are encrypted at rest using **Fernet symmetric encryption** before being stored in the database.
- Sessions are HTTP-only, lasting 7 days.
- CORS is restricted to configured origins only.
- Never commit your `.env` file — it is listed in `.gitignore`.

---

## 🧪 Testing the Groq Connection

A standalone test script is included:

```bash
cd backend
python test_groq.py
```

---

## 📄 License

This project is private and proprietary. All rights reserved.

---

*Built with ❤️ for educators.*
