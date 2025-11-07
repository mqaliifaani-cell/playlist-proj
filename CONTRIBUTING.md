# Contributing to PlaylistPro

Thank you for your interest in contributing!  
This document explains how to contribute code, tests, and documentation.

---

## 🧩 How to Contribute
1. **Fork** the repository and create a feature branch:
   ```bash
   git checkout -b feat/your-feature
   ```
2. **Make changes** and add tests where applicable.
3. **Run locally** and ensure no regressions.
4. **Commit your changes** with clear messages:
   ```bash
   git commit -am "feat: short description"
   ```
5. **Push and open a Pull Request** against `main`.

---

## ✍️ Code Style
- Python: follow **PEP8** and use **Black** for formatting.
- Keep functions small, readable, and testable.
- Add **docstrings** for public classes and functions.

---

## 🧪 Tests
- For logic-heavy modules, add unit tests in `tests/`.
- CI will be extended to run tests on push.

---

## 🚀 CI / Releases
- GitHub Actions build Windows artifacts automatically.
- For packaging or CI changes, edit `.github/workflows/build-windows.yml`.
