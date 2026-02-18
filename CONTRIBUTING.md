# Contributing to MediBot

Thank you for your interest in contributing to MediBot! We welcome contributions from the community to make this AI medical assistant even better.

## Development Setup

### Prerequisites

- **Node.js** v18+ (verified v22.17.1)
- **Python** 3.11+
- **AWS CLI** configured
- **AWS SAM CLI** installed
- **Git**

### 1. Clone the repository

```bash
git clone https://github.com/your-username/medibot.git
cd medibot
```

### 2. Backend Setup

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

### 4. Local Development

**Backend API**:
```bash
# From backend/ directory
uvicorn api_server:app --reload --port 8000
```
API Docs will be available at http://localhost:8000/docs

**Frontend**:
```bash
# From frontend/ directory
npm run dev
```
Open http://localhost:5173

## Project Structure

- `backend/` - Python FastAPI application (Lambda)
- `frontend/` - React + Vite application
- `infrastructure/` - AWS SAM template
- `docs/` - Architecture and other documentation

## Pull Request Process

1.  Fork the repository and create your branch from `main`.
2.  If you've added code that should be tested, add tests.
3.  Ensure the test suite passes (`pytest` for backend, `npm test` for frontend).
4.  Make sure your code lints (`flake8`/`black` for Python, `eslint` for TS).
5.  Update documentation if you've changed APIs or features.
6.  Submit a Pull Request!

## Reporting Issues

Use the GitHub Issues tab to report bugs or suggest features. Please provide as much detail as possible, including steps to reproduce for bugs.

## License

By contributing, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).
