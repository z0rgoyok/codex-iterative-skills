# Codex Iterative Skills

Этот репозиторий упаковывает навыки для управляемой работы через итерации, финальное ревью и агентно-ориентированные монорепы.

Что здесь лежит:

- `iterative-plan-review` строит рабочий план по задаче, прогоняет его через до трёх независимых проходов критического ревью и поднимает пользователю только бизнес-развилки.
- `iterative-review-fix` закрывает цикл `review -> fix -> re-review`, сохраняет компактный машинно-парсерный след артефактов, опционально использует `$final-gate-review` внутри review-субагента и поднимает пользователю только решения, которые меняют бизнес-смысл.
- `final-gate-review` даёт отдельный жёсткий финальный quality gate (контроль качества) для staged change set (подготовленного набора изменений), ищет long impact (долгий эффект), архитектурные риски и пропущенные сценарии и возвращает результат прямо в ответе без отдельного файла в репозитории.
- `epic-coordinator` координирует программный эпик от первичного разбора до ревью: Linear, workstreams (потоки работ), агенты, epic branch, PR, проверки, статусы и остаточные риски.
- `monorepo-skill-structure-creator` создаёт структуру `.agents/skills/project-name-skills-*`, обновляет root `AGENTS.md` как router (маршрутизатор) контекста и фиксирует обязательные quality skills (навыки контроля качества) для подпроектов монорепы.
- `agentic-monorepo-operator` описывает работу агента в таких монорепах: выбор project/context skills (проектных/контекстных навыков), quality skills, границы React/Next.js, KMM, Android, React Native и backend.

Итеративные навыки сохраняют историю работы и артефакты так, чтобы результат можно было восстановить, проверить и продолжить. Для `iterative-plan-review` и `iterative-review-fix` рабочий след теперь хранится в JSON-first формате.

## Repository Layout

```text
skills/
  iterative-plan-review/
    SKILL.md
    agents/openai.yaml
    references/artifact-layout.md
    scripts/init_plan_review_run.py
    scripts/persist_plan_review_pass.py
  iterative-review-fix/
    SKILL.md
    agents/openai.yaml
    references/artifact-layout.md
    scripts/init_review_fix_run.py
    scripts/persist_review_pass.py
  final-gate-review/
    SKILL.md
  epic-coordinator/
    SKILL.md
    agents/openai.yaml
  monorepo-skill-structure-creator/
    SKILL.md
    agents/openai.yaml
  agentic-monorepo-operator/
    SKILL.md
    agents/openai.yaml
```

## Why These Skills Exist

Обычный агент часто либо слишком быстро принимает спорные решения, либо теряет след изменений между раундами обсуждения.

Эти навыки решают это через явный процесс:

- отделяют рабочие улучшения от бизнес-выборов;
- добавляют независимое критическое ревью;
- сохраняют историю вопросов, ответов и изменений;
- останавливают цикл раньше третьей итерации, когда открытых findings уже нет вообще.

Оба итеративных навыка дополнительно решают операционную проблему "субагент ответил, но артефакты не были сохранены" через обязательный checkpoint persistence (контрольный шаг сохранения) после `wait_agent`.

## Installation

Скопируй нужные директории в `$CODEX_HOME/skills`.

Если `CODEX_HOME` у тебя не задан, Codex обычно использует `~/.codex`.

Пример:

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R skills/iterative-plan-review "${CODEX_HOME:-$HOME/.codex}/skills/"
cp -R skills/iterative-review-fix "${CODEX_HOME:-$HOME/.codex}/skills/"
cp -R skills/final-gate-review "${CODEX_HOME:-$HOME/.codex}/skills/"
cp -R skills/epic-coordinator "${CODEX_HOME:-$HOME/.codex}/skills/"
cp -R skills/monorepo-skill-structure-creator "${CODEX_HOME:-$HOME/.codex}/skills/"
cp -R skills/agentic-monorepo-operator "${CODEX_HOME:-$HOME/.codex}/skills/"
```

Для воспроизводимой синхронизации используй проектный скрипт:

```bash
scripts/sync-skills.sh install codex
scripts/sync-skills.sh install claude
scripts/sync-skills.sh install all
```

Он умеет три режима:

- `install` копирует навыки из репозитория в домашний каталог агента;
- `pull` копирует навыки из домашнего каталога агента обратно в репозиторий;
- `diff` показывает расхождения между репозиторием и установленной копией.

Примеры:

```bash
scripts/sync-skills.sh diff all
scripts/sync-skills.sh pull codex claude-review-manager
scripts/sync-skills.sh install all iterative-plan-review iterative-review-fix
```

## Usage

Примеры запросов:

- `Use $iterative-plan-review to turn this task into a working plan and review it up to three times.`
- `Use $iterative-review-fix to close these review findings and keep the full artifact trail.`
- `Use $final-gate-review to perform a final principal-level review of the staged change set.`
- `Use $epic-coordinator to coordinate this Linear epic through implementation, review, PR and status updates.`
- `Use $monorepo-skill-structure-creator to create repo-local project and quality skills for this monorepo.`
- `Use $agentic-monorepo-operator while working across this React/KMM/backend monorepo.`

Итеративные навыки уже включают:

- шаблон артефактной структуры;
- скрипт инициализации рабочего прогона;
- prompt contract (контракт промпта) для субагента;
- явный запрет на каскадную делегацию из субагента.

`iterative-plan-review` дополнительно умеет:

- хранить `session-state.json` как SSOT (единый источник истины) прогона;
- хранить `event-log.jsonl` как append-only журнал;
- хранить каждый review pass в одном `reviews/iteration-N.json`;
- фиксировать raw response (сырой ответ) reviewer-а и normalized review (нормализованное ревью) через `scripts/persist_plan_review_pass.py`;
- обновлять тот же pass после ответов пользователя и финализации без россыпи вспомогательных Markdown-файлов.

`iterative-review-fix` дополнительно умеет:

- использовать `$final-gate-review`, если этот skill доступен в сессии review-субагента;
- работать без него, если skill не установлен;
- считать цикл завершённым только при нуле открытых findings любого уровня;
- хранить `session-state.json` как SSOT (единый источник истины) прогона;
- хранить `event-log.jsonl` как append-only журнал;
- хранить каждый review pass в одном `reviews/iteration-N.json`;
- фиксировать raw response (сырой ответ) reviewer-а и normalized review (нормализованное ревью) через `scripts/persist_review_pass.py`.

`final-gate-review` полезен отдельно, когда нужен последний независимый архитектурный и продуктовый фильтр перед merge (вливанием). Он работает во встроенном режиме: показывает findings сразу в ответе, а сохранение в артефакты оставляет вызывающему workflow.
