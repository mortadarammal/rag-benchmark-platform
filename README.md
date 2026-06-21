```md
# RAG Benchmark Platform

A fullstack RAG benchmark platform that compares multiple LLMs using document-based retrieval and LLM-as-a-judge evaluation.

## Features

- Project dashboard
- Document upload
- Automatic document chunking
- NVIDIA embeddings
- Qdrant vector storage
- Question generation from uploaded documents
- Question selection
- Multi-LLM answer generation
- Judge evaluation
- RAGAS-style metrics
- Ranking page
- CSV and JSON exports

## Tech Stack

### Backend

- Django
- Django REST Framework
- Celery
- Redis
- PostgreSQL
- Qdrant
- LangChain
- NVIDIA AI Endpoints

### Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS

### AI Pipeline

- Embeddings: NVIDIA embedding model
- Question generation: NVIDIA-hosted Llama
- Answer generation: multiple NVIDIA-hosted LLMs
- Judge evaluation: NVIDIA-hosted judge LLM

## Local Setup

### 1. Clone the repository

```bash
git clone 
cd rag-benchmark-platform
```

### 2. Start Docker services

```bash
docker compose up -d
```

### 3. Backend setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` from `.env.example`:

```bash
copy .env.example .env
```

Then edit `.env` and add your NVIDIA API key.

Run migrations:

```bash
python manage.py migrate
```

Start Django:

```bash
python manage.py runserver
```

### 4. Start Celery

Open another terminal:

```bash
cd backend
venv\Scripts\activate
celery -A config worker -l info --pool=solo
```

### 5. Frontend setup

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

## Workflow

```text
Create project
→ Upload documents
→ Generate questions
→ Select question
→ Generate answers
→ Run judge evaluation
→ View ranking
→ Export CSV/JSON
```

## Prompt Locations

You can edit the AI prompts here:

### Question generation prompt

```text
backend/benchmarks/question_generation.py
```

Look for:

```python
class SimpleQuestionGenerator
self.prompt = ChatPromptTemplate.from_messages(...)
```

### Multi-LLM answer generation prompt

```text
backend/benchmarks/answer_generation.py
```

Look for:

```python
RAG_ANSWER_PROMPT = PromptTemplate(...)
```

### Judge evaluation prompt

```text
backend/benchmarks/judge_evaluation.py
```

Look for:

```python
JUDGE_PROMPT = """
...
"""
```

### Model configuration

```text
backend/rag/config.py
```

This file controls:

- Embedding model
- Question generation model
- Answer generation models
- Judge model
- Top-k retrieval
- Max tokens
- Temperature
- Evaluation weights