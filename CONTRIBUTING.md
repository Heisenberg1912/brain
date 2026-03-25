# Contributing

Thanks for contributing to BuiltAttic Brain.

## Branch Workflow

- Keep `main` releasable.
- Branch from `main` for every change.
- Use short, descriptive branch names such as `feat/location-ranking`, `fix/valuation-core`, `docs/setup-guide`, or `chore/ci-cache`.
- Keep each branch focused on one change set.
- Rebase or merge the latest `main` before requesting final review.
- Prefer squash merges so the `main` history stays easy to read.

## Local Setup

1. Create a local `.env` from `.env.example` and add only the API keys you need for your provider.
2. Install backend and test dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

3. Install frontend dependencies:

```bash
cd frontend
npm ci
```

## Before Opening A Pull Request

- Run `python -m pytest -q` from the repo root.
- Run `npm run build` from `frontend/`.
- Update `.env.example`, docs, or sample payloads if your change affects configuration or API contracts.
- Never commit `.env`, real API keys, local build output, or machine-specific files.
- Add screenshots or short recordings for visible frontend changes.

## Pull Request Workflow

- Open a draft PR early if the work will take more than one session.
- Use small PRs when possible so reviewers can reason about them quickly.
- Fill out the PR template with a summary, testing notes, and follow-up items.
- Link the issue you are solving, or explain the problem clearly if no issue exists.
- Call out migrations, breaking changes, or deployment notes in the PR description.

## Review Expectations

- Keep CI green before asking for merge.
- Address review comments with follow-up commits or clear replies.
- Ask for a fresh review after significant changes.
- Leave TODOs only when they are tracked by an issue or clearly documented follow-up work.
