---
name: monorepo-skill-structure-creator
description: Create or update agent-oriented monorepo skill structure. Use when Codex needs to set up repo-local .agents/skills, convert AGENTS.md files into project-name-skills-* context skills, add mandatory quality-control skills for monorepo subprojects, or update root AGENTS.md routing for React, Next.js, KMM, Android, React Native, Python backend, or mixed-stack monorepos.
---

# Monorepo Skill Structure Creator

## Goal

Create a repo-local skill system for monorepos where the root `AGENTS.md` is the context router and `.agents/skills/project-name-skills-*` contains project, platform, and quality-control skills.

## Target Layout

Use this default structure:

```text
repo-root/
  AGENTS.md
  .agents/
    skills/
      project-name-skills-workspace/
      project-name-skills-<subproject>/
      project-name-skills-<subproject>-quality/
      project-name-skills-<subproject>-<platform>/
      project-name-skills-<subproject>-<platform>-quality/
```

Use `.agents/skills`, not `.codex/skills`, for repo-local skills. Codex discovers `.agents/skills` while walking between the project root and current working directory.

## Naming

Use lowercase hyphen-case names:

- `project-name-skills-workspace`
- `project-name-skills-web`
- `project-name-skills-web-quality`
- `project-name-skills-mobile`
- `project-name-skills-mobile-quality`
- `project-name-skills-kmm`
- `project-name-skills-kmm-quality`
- `project-name-skills-backend`
- `project-name-skills-backend-quality`

Replace `project-name` with the real product or monorepo name.

## Required Skill Types

Every agent-oriented monorepo must have these skill categories:

- Workspace skill: global project map, routing rules, Linear and branch policy, common architecture expectations.
- Project/context skills: one skill per major app, package, service, or bounded context.
- Quality skills: one quality-control skill for every subproject that can be changed independently.

Quality skills are mandatory because agents need exact local commands, inspection expectations, test scope, and untested contour reporting. Use dedicated quality skills as the source of truth for quality gates.

## What Goes Where

Put stable always-on routing in root `AGENTS.md`:

- project list;
- directory-to-skill mapping;
- required skill combinations;
- language and collaboration rules;
- global test/reporting policy.

Put detailed instructions in skills:

- copied or summarized local `AGENTS.md`;
- exact build/test/lint/typecheck commands;
- architecture boundaries;
- platform-specific constraints;
- quality gates and inspection workflow.

Put long source material in `references/`:

- verbatim copied `AGENTS.md`;
- test matrix;
- architecture notes;
- migration notes.

## Creation Workflow

1. Identify monorepo root and all subprojects.
2. Read existing `AGENTS.md`, `README.md`, `package.json`, Gradle files, `pyproject.toml`, and workspace manifests.
3. Create `.agents/skills` at the monorepo root.
4. Create one `project-name-skills-*` skill per project/context.
5. Create one `project-name-skills-*-quality` skill per independently testable subproject.
6. Copy existing local `AGENTS.md` into the relevant skill `references/AGENTS.md` when preserving source rules matters.
7. Write concise `SKILL.md` files that point to references and explain when to use them.
8. Update root `AGENTS.md` with explicit rules:
   - if task touches `<path>`, use `<project skill>`;
   - if task changes code under `<path>`, also use `<quality skill>`;
   - if task crosses projects, use all affected project and quality skills.
9. Validate every skill with `quick_validate.py`.
10. Run `mlint` for changed Markdown files.

## Root AGENTS.md Routing Template

Add a section like this:

```markdown
## Repo Skills

Use repo skills from `.agents/skills`.

If a task touches `apps/web/`, use `project-name-skills-web`.
If a task changes code under `apps/web/`, also use `project-name-skills-web-quality`.

If a task touches `packages/shared-kmm/`, use `project-name-skills-kmm`.
If a task changes code under `packages/shared-kmm/`, also use `project-name-skills-kmm-quality`.

If a task crosses multiple subprojects, use every affected project skill and every affected quality skill.
```

## Common Stack Patterns

Use these defaults for the current family of projects:

- React/Next.js web apps: project skill + web quality skill.
- React Native mobile apps: project skill + mobile quality skill.
- KMM shared modules: KMM skill + KMM quality skill.
- Android/Gradle apps: Android skill + Android quality skill.
- Python backends: backend skill + backend quality skill.

For projects like `proCLEVER`, `pattita`, and `lilit-hob`, expect mixed React, Next.js, KMM, Android/Gradle, React Native, and Python backend contours.

## Quality Skill Minimum Content

Each quality skill must contain:

- exact lint, format, typecheck, test, and build commands;
- narrow checks for local changes;
- full checks before handoff;
- IDE inspection requirements when applicable;
- command order;
- known expensive checks;
- what to report when checks are not run;
- project-specific warning policy.

## Validation

Run:

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py .agents/skills/<skill-name>
mlint AGENTS.md
mlint .agents/skills/<skill-name>/SKILL.md
```
