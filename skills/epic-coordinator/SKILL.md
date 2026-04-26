---
name: epic-coordinator
description: Координировать программный эпик от первичного разбора до ревью в абстрактном, независимом от конкретного проекта виде. Использовать, когда Codex должен изучить эпик или крупную фичу, прочитать правила проекта, декомпозировать потоки работ, создать или актуализировать задачи Linear, координировать нескольких агентов, вести epic branch и PR, проводить циклы ревью, соблюдать project quality gates, обновлять статусы задач и фиксировать проверки, риски и follow-ups.
---

# Координатор Эпика

Используй этот навык, когда пользователь просит вести, координировать, актуализировать, ревьюить, довести до конца или разложить эпик / крупную фичу через несколько задач, репозиториев, агентов, PR или потоков работ.

Цель координатора — не просто написать код. Цель — держать эпик правдивым: требования, реализация, ревью, PR, проверки и остаточные риски должны совпадать с реальностью.

## Правила Проекта Сначала

Перед планированием, изменениями, делегированием, сменой статусов задач или отчётом сначала прочитай и соблюдай правила текущего проекта.

Ищи:

- `AGENTS.md` в корне репозитория и релевантных подпапках.
- `.codex/skills/*/SKILL.md` для проектных правил backend, frontend, mobile, QA, review или release.
- `README`, `CONTRIBUTING`, архитектурные документы, документацию по тестам, CI, PR templates и workflow задач.
- Существующие паттерны кода, правила веток, формат коммитов, формат PR, названия статусов, команды тестов, требования к инспекциям и release-правила.

Правила проекта имеют приоритет над этим навыком. Если проект требует сначала IDE inspections, конкретный MCP/tooling, screenshot checks, особое имя ветки, выбор Linear project или полный test suite, выполняй именно это.

## Источник Истины

Сначала установи текущее фактическое состояние:

- Linear epic, дочерние задачи, комментарии, labels, project, status, assignee и blockers.
- Существующие PR, ветки, коммиты, CI, review comments и draft/ready state.
- Локальный git status, dirty files, unpushed commits и чужие изменения пользователя.
- Документы проекта и mailbox/status docs, созданные для эпика.
- Реальный diff реализации относительно target branch.

Планы и комментарии считаются гипотезой, пока они не проверены по коду, тестам и PR state.

## Жизненный Цикл Эпика

1. **Разобрать**: прочитать эпик, связанные задачи, комментарии, PR, правила проекта и релевантный код.
2. **Уточнить scope**: отделить MVP, явные исключения, предположения, открытые вопросы и follow-ups.
3. **Декомпозировать**: разделить работу на независимые потоки с владельцем и acceptance criteria.
4. **Скоординировать**: распределить агентов или локальную работу по repo/module/layer с непересекающимися write scopes.
5. **Интегрировать**: совместить workstreams на epic branch без отката чужих изменений.
6. **Отревьюить**: провести ревью контрактов, архитектуры, data integrity, UX, тестов и rollout.
7. **Исправить**: закрыть блокирующие findings и повторить targeted checks.
8. **Проверить**: запустить проектные inspections, quality gates, tests, screenshots и final review.
9. **Опубликовать**: закоммитить, запушить, открыть или обновить PR и написать evidence-based описание / комментарии.
10. **Актуализировать**: обновить Linear tasks, statuses, links, scope notes, checks, residual risks и follow-up задачи.

Не перескакивай от реализации сразу к “done”. Ревью и правдивое состояние задач — часть работы по эпику.

## Потоки Работ

Фактическое разбиение зависит от проекта, но типовые потоки такие:

- domain model, status machine, policies и audit;
- backend/API contract, persistence, migrations, repositories и integration tests;
- shared/generated contracts и client DTO;
- пользовательский flow A;
- reviewer/manager flow B;
- finalizer/admin/accounting flow C;
- design system и общие UI components;
- localization и accessibility;
- data migration/backfill/rollout;
- QA, screenshots, review и release notes.

У каждого потока должны быть:

- owner или agent;
- файлы/модули, которые он может менять;
- зависимости и blockers;
- acceptance criteria;
- проверки, которые нужно запустить;
- место для mailbox/status update;
- PR или branch destination.

## Работа С Агентами

Используй субагентов только когда пользователь разрешил делегирование или параллельную работу агентов.

При делегировании:

- явно скажи агенту, что он не один в кодовой базе;
- скажи не откатывать и не перезаписывать чужие изменения;
- задай непересекающийся write scope;
- потребуй список changed files, tests, checks и checks left out;
- используй mailbox/status document для handoff, если параллельно работают несколько агентов;
- оставь интеграцию, финальные решения и пользовательский статус за координатором.

Не делегируй immediate blocking step, если координатор может сделать его быстрее локально. Делегируй bounded sidecar work, который реально идёт параллельно.

## Архитектурные Ограничители

Применяй архитектуру текущего проекта. Если проект использует DDD / Clean Architecture:

- domain владеет invariants, policies, status machines, typed errors и бизнес-терминологией;
- application владеет orchestration;
- data владеет persistence, API clients, DTO mapping, cache и atomic repository operations;
- presentation владеет prepared screen state, effects и view models;
- UI только рендерит state и отправляет intents;
- infrastructure владеет wiring и внешними системами.

Предпочитай один SSOT (single source of truth, единый источник истины) для:

- statuses, actions, roles, scopes, route ids, tab ids и API enum values;
- permission rules и access policies;
- validation rules;
- money/date/time semantics;
- localization keys;
- error codes и user-facing error mapping.

Избегай silent fallbacks для обязательных данных, дублированных string registries, бизнес-логики в UI, прямого доступа к repositories из UI/controllers при наличии use cases и скрытых compatibility layers без прямого запроса пользователя.

## Linear

Держи Linear актуальным по мере движения эпика:

- создавай недостающие дочерние задачи, если эпик слишком широкий;
- выставляй parent, project, priority, labels, blockers и PR links;
- переводи задачи в фактический status только когда code/review state ему соответствует;
- добавляй комментарии по scope changes, checks, residual risks и decisions;
- держи future scope отдельно от MVP tasks;
- создавай follow-up issues для принятых остаточных рисков, а не прячь их в комментариях.

Когда пользователь говорит “все в ревью”, переводи эпик и реализованные дочерние задачи в проектный review status, прикрепляй PR links, а future-scope задачи оставляй в backlog, если они не входят в delivered PRs.

## Цикл Ревью

Ревью — это gate, а не украшение.

Проверяй минимум:

- покрытие acceptance criteria;
- API и data contracts;
- layer boundaries;
- authorization и access scope;
- money, dates, idempotency, audit и concurrency для high-risk domains;
- migration и backfill behavior;
- UI states, localization, accessibility и screenshots для user-facing изменений;
- missing tests и unrun quality gates;
- rollout, monitoring и rollback.

Severity:

- P0: data loss, security issue, wrong irreversible operation, broken critical path.
- P1: broken main scenario, wrong contract, wrong authorization, missing required audit, wrong financial/domain result.
- P2: важный edge case или maintainability issue, который можно оставить только с явным принятием.
- P3: cleanup, naming, polish, minor consistency.

Исправляй P0/P1 перед публикацией как ready for review. Принятые P2/P3 фиксируй как follow-ups, если они остаются вне scope.

## Проверки И Доказательства

Запускай проверки по правилам проекта. Типовые gates:

- IDE inspections, если проект их требует;
- formatter/linter/quality scripts;
- targeted tests для изменённых модулей;
- full tests при широком blast radius;
- migration/backfill checks;
- API/schema/codegen checks;
- screenshot и accessibility evidence для видимых UI изменений;
- final independent review.

Явно фиксируй, что запускалось и с каким результатом. Также фиксируй, что осталось вне запуска и почему.

## Git И PR

Соблюдай проектные правила веток, коммитов и PR.

Для epic branches:

- мержи вложенные задачи в epic branch, если так требуют правила проекта;
- не смешивай unrelated changes;
- сохраняй изменения пользователя и других агентов;
- коммить по repo/workstream, если так проще ревьюить;
- пушь и обновляй PR descriptions после verification.

PR body или комментарий должен включать:

- changed user behavior;
- business value или снятый риск;
- contract и data changes;
- implementation boundaries;
- tests и checks;
- screenshots, если релевантно;
- rollout/rollback;
- residual risks и follow-ups.

## Финальный Отчёт

В отчёте пользователю или Linear укажи:

- состояние эпика и задач;
- PR links и commit hashes;
- реализованный scope по workstreams;
- явные exclusions и future scope;
- checks run with results;
- review findings fixed;
- remaining risks и follow-up tasks;
- чистоту репозитория или dirty files, если это важно.

Пиши кратко и фактически. Координатор отвечает за правдивость: не называй эпик завершённым, если задачи, PR, проверки или review state ещё расходятся.
