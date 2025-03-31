# vSecure Analyzer

**vSecure Analyzer** is a Visual Studio Code extension that enables static security analysis of source code using powerful tools like **Semgrep** and **CodeQL**, along with GPT-based recommendations and fixes.

---

## Features

- Analyze local workspace code by zipping and sending it to a backend server
- Choose between Semgrep, CodeQL, or both
- Inline diagnostics in Problems panel
- GPT-generated explanations for each vulnerability
- GPT-powered Quick Fix for selected code blocks (with preview and approval)
- Server-based analysis backend (FastAPI)
- GPT securely accessed via your own API key

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/vsecure-analyzer.git
cd vsecure-analyzer
```

### 2. Backend Setup

```bash
cd analyzer-server
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file with your OpenAI API key and CodeQL DB path:

```env
OPENAI_API_KEY=your-openai-key
CODEQL_DB_DIR=/tmp/codeql_dbs
```

To run the backend:

```bash
uvicorn app.main:app --reload
```

> Alternatively, use `docker-compose up` if Docker is preferred.

---

### 3. VSCode Extension Setup

```bash
cd ../vsecure-analyzer-extension
npm install
npm run compile
```

Then press `F5` in VSCode to launch a new Extension Development Host.

---

### 4. Run Analysis

- Open a workspace folder in VSCode
- Open the command palette and run `vSecure Analyzer: Run Analysis`
- Select the desired analyzer(s)
- View diagnostics and GPT-enhanced explanations in the Problems panel

To fix code manually:

- Select vulnerable code
- Run `vSecure Analyzer: Fix with GPT` from the command palette
- Review and apply the suggested fix

---

## Project Structure

```
vsecure-analyzer/
├── analyzer-server/            # FastAPI backend for analysis
│   ├── app/
│   ├── runner/
│   └── utils/
├── vsecure-analyzer-extension/ # VSCode frontend extension
```

---

## TODO

- [ ] Improve file handling and zipping performance
- [ ] Add caching mechanism for CodeQL databases
- [ ] Display diff-based fixes for clearer quick fix context
- [ ] Support Java fully with CodeQL build hooks
- [ ] Add per-analyzer visual distinction in diagnostics

---

## Powered By

- [Semgrep](https://semgrep.dev/)
- [CodeQL](https://codeql.github.com/)
- [OpenAI GPT](https://platform.openai.com/docs/)

---

## License

MIT License
