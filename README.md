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
