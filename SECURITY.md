# Security Policy

## Supported Versions

Security fixes are applied to the default branch and the latest public release.
Older research snapshots are provided for reproducibility and may not receive
backported fixes.

## Reporting a Vulnerability

Please do not disclose sensitive issues in a public GitHub issue. Instead,
contact the maintainer listed in `pyproject.toml` or use GitHub's private
security advisory workflow if it is enabled for the repository.

Useful reports include:

- affected version or commit,
- operating system and Python version,
- exact dependency versions when relevant,
- minimal reproduction steps,
- whether secrets, local files, or remote services are exposed.

## Secrets and Credentials

AdsMind can use hosted LLM APIs. Never commit API keys or provider credentials.
Use environment variables or the local config file managed by the UI. The
project `.gitignore` excludes `.env` files and Streamlit secrets by default.

