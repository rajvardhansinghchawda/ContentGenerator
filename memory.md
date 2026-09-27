# Project Memory

## Project Overview
EduFlow is an automated educational content generation platform built for teachers. It generates lecture documents (Pre-doc, Post-doc) and Google Forms quizzes from teacher prompts using Groq LLM API and integrates with Google Workspace (Google Docs, Forms, Drive).

## Current Architecture
- **Backend**: Django 5.x / Django REST Framework
- **Task Queue**: Celery with Redis broker (deployed on Render)
- **Database**: PostgreSQL (Neon / Render)
- **AI Engine**: Groq API integration (`backend/ai_engine/groq_client.py`)
- **Google Services**: Google OAuth2, Google Docs API, Google Forms API, Google Drive API
- **Frontend**: React / Vite frontend

## Important Decisions
- Use Groq API for rapid inference and structured JSON generation.
- Model rotation implemented in `groq_client.py` to mitigate rate limits and fallbacks.
- Phase-based generation: Phase 1 generates lecture notes/docs, Phase 2 generates quiz.

## Current State
- Deployed on Render with web service and background Celery worker.
- Groq models `llama-3.3-70b-versatile` and `llama-3.1-8b-instant` decommissioned by Groq, causing HTTP 404 in production jobs.
- New Groq models (`openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `qwen/qwen3.8-27b`) require being enabled in Groq Console (`https://console.groq.com/settings/limits`).

## Known Issues
- Groq API 404 error: `llama-3.3-70b-versatile` decommissioned by Groq.
- Groq API 403 error: New models (`openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `qwen/qwen3.8-27b`) currently blocked at the organization level in the user's Groq Console.
- Retry loop in `backend/ai_engine/groq_client.py` only rotates model on HTTP 429; on HTTP 404 or 403 it retries the same dead model 5 times without switching.

## Pending Work
- User needs to enable `openai/gpt-oss-120b` and `openai/gpt-oss-20b` (or `qwen/qwen3.8-27b`) at `https://console.groq.com/settings/limits`.
- Update `backend/ai_engine/groq_client.py` and `backend/jobs/tasks.py` model configurations and rotation logic.

## Interaction History

### 2026-09-26 23:20
**User Request**
> model band ho gaya hai , ki api fail hori hai kya seen ahi
> (Encountered HTTP 404: The model `llama-3.3-70b-versatile` does not exist or you do not have access to it in Render Celery worker)

**Exploration**
- Inspected `backend/jobs/tasks.py`, `backend/ai_engine/groq_client.py`, `backend/test_groq.py`.
- Queried Groq `/openai/v1/models` endpoint directly using active API key.
- Discovered `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, `mixtral-8x7b-32768`, etc., were decommissioned by Groq.
- Tested current active Groq models: `openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `qwen/qwen3.8-27b`.
- Found that new models return HTTP 403 `model_permission_blocked_org` because organization limits in `https://console.groq.com/settings/limits` have not enabled them yet.
- Noticed rotation logic in `groq_client.py` only rotated index on HTTP 429, not on 404/403.

**Work Done**
- Diagnosed root causes: Model decommissioning by Groq + Organization level model block on new models.
- Documented findings, created initial `memory.md`, and formulated clear step-by-step guidance for the user.

**Files Changed**
- `memory.md`
  - Created persistent project memory tracking system state, decisions, and issues.

**Verification**
- Live API calls to `https://api.groq.com/openai/v1/models` and `https://api.groq.com/openai/v1/chat/completions`. Verified exact HTTP 404 on llama models and HTTP 403 on new models.

**Response**
- Detailed diagnosis explaining model decommissioning, Groq console organization limits, code rotation logic, and exact steps to fix.

**Git**
- Branch: master
- Commit: Pending
- Push: Pending

### 2026-09-26 23:25
**User Request**
> i add new api key test with them

**Exploration**
- Inspected the newly added API key from `backend/.env`.
- Executed live API completions against all active Groq models using the new API key.

**Work Done**
- Verified the new API key against Groq API.
- Confirmed that the new key belongs to the same Groq organization and still encounters `HTTP 403: model_permission_blocked_org` for generation models (`openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `qwen/qwen3.8-27b`).
- Identified that the block is an organization-wide setting in Groq Console (`https://console.groq.com/settings/limits`), not an individual API key issue.

**Files Changed**
- None (Code unchanged; user updated local gitignored `backend/.env`).

**Verification**
- Ran test script verifying model endpoints with the new key. Confirmed 403 on generation models and 200 on prompt-guard models.

**Response**
- Informed user of exact test results: Key is valid, but the Organization Limit restriction blocks the models. Provided direct instructions on how to toggle allowlist/blocklist in Groq Console Settings -> Limits.

**Git**
- Branch: master
- Commit: None
- Push: None
- Status: Clean

**Notes**
- The user must unblock the models in Groq Console organization settings so chat completions succeed.

### 2026-09-26 23:30
**User Request**
> User provided the available models list from Groq Console limits table (`openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `qwen/qwen3.8-27b`, `meta-llama/llama-prompt-guard-2-86m`, etc.) and requested:
> "enme se use karo na or agar ek ki limit us hour or day ki reach ho gaye hai to vo automatic dusara use kar le taki service chakti hai app chlata rah user problem face na kare"

**Exploration**
- Filtered generation LLMs from specialized audio (Whisper, Orpheus) and guardrail models.
- Identified text models: `openai/gpt-oss-120b` (primary for lecture notes), `openai/gpt-oss-20b` (secondary for quizzes & fast fallback), `qwen/qwen3.8-27b` (tertiary fallback).
- Tested `meta-llama/llama-prompt-guard-2-86m` for safety checks (returned HTTP 200).

**Work Done**
- Implemented intelligent model pool rotation and cooldown circuit breaker in `backend/ai_engine/groq_client.py`:
  - `_MODEL_COOLDOWN` dictionary tracks when models hit hourly/daily quota or rate limits.
  - Rate limits / burst quotas (RPM/TPM) place the model into a 60s cooldown; daily/hourly quota exhaustion (RPD/TPD) places it into 3600s cooldown.
  - Active pool sorting ensures subsequent requests automatically bypass exhausted models and use working models first without incurring failed attempts.
  - Immediate rotation to next model on 429, 404, 400, 500, 502, 503, 504 errors with minimal delay.
- Updated `backend/jobs/tasks.py` to use `openai/gpt-oss-120b` for notes and `openai/gpt-oss-20b` for quizzes.
- Updated `verify_prompt_safety` in `groq_client.py` to use active `meta-llama/llama-prompt-guard-2-86m`.
- Updated `GROQ_MODEL` default in `backend/config/settings/base.py` and diagnostic script `backend/ai_diagnostic.py`.
- Updated `test_groq.py` to test the candidate models.
- Added `celerybeat-schedule*` to `.gitignore`.

**Files Changed**
- `backend/ai_engine/groq_client.py`
  - Added new model pool (`openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `qwen/qwen3.8-27b`), automatic fallback rotation, in-memory cooldown tracker, and Prompt Guard 2 safety check.
- `backend/jobs/tasks.py`
  - Pointed Phase 1 to `openai/gpt-oss-120b` and Phase 2 to `openai/gpt-oss-20b`.
- `backend/config/settings/base.py`
  - Updated default `GROQ_MODEL` setting.
- `backend/ai_diagnostic.py`
  - Updated diagnostic script model to `openai/gpt-oss-120b`.
- `backend/test_groq.py`
  - Updated test harness for new models.
- `.gitignore`
  - Added `celerybeat-schedule*`.
- `memory.md`
  - Updated project memory and interaction logs.

**Verification**
- Tested safety model `meta-llama/llama-prompt-guard-2-86m` directly against Groq API (200 OK).
- Tested candidate generation models via `test_groq.py`.
- Validated code syntax and git diff.

**Git**
- Branch: master
- Commit: 57697db
- Push: Success (origin/master)
- Status: Pushed to GitHub

**Notes**
- Model migration and quota management logic deployed to GitHub.

### 2026-09-27 20:57
**User Request**
> test now it is working or notr

**Exploration**
- Inspected model permissions after user allowed models in Groq Console.
- Updated `backend/test_groq.py` test harness to test all candidate LLMs (`openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `qwen/qwen3.8-27b`, `openai/gpt-oss-safeguard-20b`) and the prompt-guard safety classifier (`meta-llama/llama-prompt-guard-2-86m`).

**Work Done**
- Executed end-to-end API verification against Groq API.
- Confirmed that all models are active, allowed, and producing valid JSON responses.
- Confirmed Prompt Guard 2 model responds with low injection score (Safe: True).

**Files Changed**
- `backend/test_groq.py`
  - Added JSON validation and Prompt Guard 2 test integration.
- `memory.md`
  - Updated interaction log and current state.

**Verification**
- Executed `python backend/test_groq.py`:
  - `openai/gpt-oss-120b`: HTTP 200 (Success, JSON verified)
  - `openai/gpt-oss-20b`: HTTP 200 (Success, JSON verified)
  - `qwen/qwen3.8-27b`: HTTP 200 (Success, JSON verified)
  - `openai/gpt-oss-safeguard-20b`: HTTP 200 (Success, JSON verified)
  - `meta-llama/llama-prompt-guard-2-86m`: HTTP 200 (Success, Injection score: 0.00035, Safe: True)

**Response**
- Informed user that all models are now working with HTTP 200 and generating valid JSON.

**Git**
- Branch: master
- Commit: Pending
- Push: Pending
- Status: Ready to commit and push

**Notes**
- Production pipeline on Render is ready with auto-rotation across these models.


