---
name: agentic-monorepo-operator
description: Operate monorepos that use root AGENTS.md plus repo-local project-name-skills-* skills. Use when Codex works in a mixed-stack monorepo, chooses which project and quality skills to load, plans changes across React, Next.js, KMM, Android, React Native, or Python backend subprojects, or reports verification across multiple monorepo contours.
---

# Agentic Monorepo Operator

## Operating Model

Treat the root `AGENTS.md` as a router and `.agents/skills/project-name-skills-*` as the detailed context system.

Before making changes, determine all touched paths and load the matching skills:

- project/context skill for each touched subproject;
- quality skill for each subproject where code, tests, config, migrations, or build files change;
- platform skill when the path is platform-specific.

## Skill Selection

Use path-based selection:

- `apps/web`, `web`, `frontend`, `landing`: web project skill and web quality skill.
- `apps/mobile-rn`, `mobile`, `react-native`: mobile project skill and mobile quality skill.
- `packages/shared-kmm`, `shared-kmm`, `kmm`: KMM project skill and KMM quality skill.
- `android`, `*.gradle`, `*.gradle.kts`: Android project skill and Android quality skill.
- `backend`, `services/*`, `pyproject.toml`: backend project skill and backend quality skill.

If a task crosses boundaries, load all affected skills. Prefer too much relevant local context over guessing from a neighboring project.

## Quality Rule

Every independently changeable subproject must have a quality-control skill. If a required quality skill is missing, create or propose it before doing broad work.

Quality skills define:

- inspections;
- format checks;
- lint checks;
- type checks;
- unit tests;
- integration tests;
- build checks;
- final reporting format.

Use quality skills as the source of truth for verification commands.

## Work Sequence

1. Read root `AGENTS.md`.
2. Identify touched subprojects and platforms.
3. Load required `project-name-skills-*` skills.
4. Read only the referenced files needed for the task.
5. Inspect existing architecture before changing code.
6. Keep changes inside the proper bounded context unless root-level extraction is clearly useful.
7. Run checks from the relevant quality skills after meaningful changes.
8. Before final response, report executed checks and untested contours.

## Architecture Bias

Prefer strict boundaries:

- React/Next.js UI code owns presentation and browser interaction.
- React Native code owns mobile shell behavior.
- KMM owns shared domain, data, and platform-neutral business logic.
- Android/iOS native code owns platform integration.
- Backend owns persistence, external integrations, and server-side policy.

Move shared logic upward only when at least two consumers need the same behavior and the target layer is architecturally stable.

## Reporting

Final responses for monorepo work must name:

- changed subprojects;
- skills used;
- checks run and results;
- skipped checks and reason;
- cross-project risks that remain.
