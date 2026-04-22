---
name: claude-review-manager
description: "Управлять локальным Claude CLI как независимым reviewer (ревьюером) для архитектурного review (ревью), contract review (ревью контрактов), plan review (ревью плана), code review (ревью кода) и критики предложенных решений. Использовать, когда пользователь просит спросить Claude, обсудить решение с Claude, прогнать дополнительное независимое ревью через Claude, получить second opinion (второе мнение) по архитектуре, импорту, idempotency (идемпотентности), API, blast radius (радиусу последствий) или decision memo (мемо решения)."
---

# Claude Review Manager

## Overview

Подключай Claude как внешнего критика для независимого ревью.

Работай через persistent session review (сессионное ревью): первый запрос идет с `--session-id`, все продолжения идут через `--resume`.

## Workflow

1. Определи review target (цель ревью).
- архитектурное решение;
- контракт импорта;
- схема ключей и идентичности;
- diff (дифф) или документ;
- спорный вывод или формулировка.

2. Собери минимальный контекст.
- факты;
- подтвержденные решения;
- ограничения;
- спорный контракт;
- формат ожидаемого ответа.

3. Подготовь prompt (промпт).
- Передавай только релевантный контекст.
- Проси критиковать, а не подтверждать.
- Не передавай ожидаемый ответ.

4. Подними session (сессию).
- Создай `session_id`.
- Сохрани его в `/tmp`.
- Первый запрос отправь через `claude -p` с `--session-id`.

5. Продолжай review в той же session.
- Follow-up вопросы отправляй через `--resume`.
- Добирай короткий итог отдельным follow-up prompt-ом.

6. Интегрируй вывод сам.
- Claude дает независимую критику.
- Ты отвечаешь за финальную интерпретацию и итоговое решение.

## Command Pattern

### Start session

```bash
SESSION_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')
echo "$SESSION_ID" > /tmp/claude_session_id.txt

cat > /tmp/claude_prompt_1.txt <<'EOF'
Нужен критический архитектурный review.

Контекст:
- ...

Вопрос:
- ...

Ответь в формате:
1. Что оставить.
2. Что изменить.
3. Что запретить.
4. Главный риск.
EOF

claude -p \
  --output-format text \
  --session-id "$SESSION_ID" \
  --permission-mode bypassPermissions \
  --dangerously-skip-permissions \
  --allowedTools Read \
  < /tmp/claude_prompt_1.txt
```

### Continue session

```bash
SESSION_ID=$(cat /tmp/claude_session_id.txt)

cat > /tmp/claude_prompt_2.txt <<'EOF'
Дай итог very concise.
1. Что оставить.
2. Что изменить.
3. Что запретить.
4. Главный риск.
EOF

claude -p \
  --output-format text \
  --resume "$SESSION_ID" \
  --permission-mode bypassPermissions \
  --dangerously-skip-permissions \
  --allowedTools Read \
  < /tmp/claude_prompt_2.txt
```

## Prompt Rules

### Передавай минимум

Включай:

- суть задачи;
- подтвержденные ограничения;
- принятые решения;
- сам спорный контракт;
- явный формат ответа.

Не включай:

- длинную историю без фильтрации;
- лишние детали;
- свой ожидаемый вывод.

### Проси critique-first output

Используй формулировки:

- `Назови слабые места схемы.`
- `Скажи, где смешаны identity (идентичность) строки, операции и версии.`
- `Предложи сильнейший вариант для first delivery.`
- `Ответь очень конкретно: что оставить, что изменить, что запретить.`

### Давай четкую reviewer role (роль ревьюера)

Используй одну роль на один prompt:

- `независимый критик архитектуры`;
- `reviewer контракта импорта`;
- `критик idempotency`;
- `reviewer read/write side`;
- `критик blast radius`.

## Review Shapes

### Architecture review

Фокус:

- owner (владелец логики);
- SSOT;
- границы слоев;
- special case (особый случай);
- blast radius.

### Contract review

Фокус:

- идентичность строки;
- идентичность операции;
- идентичность версии;
- idempotency;
- replace/supersede;
- неразрешенные коллизии.

### Decision memo review

Фокус:

- что уже стало решением;
- что еще остается анализом;
- где документ делает слишком ранний product choice (продуктовый выбор);
- где нужен точный acceptance contract (контракт приемки).

## Hard Rules

- Не используй `claude -p` без `--session-id` или `--resume`.
- Не передавай секреты, токены и чувствительные данные.
- Не давай Claude лишние tools (инструменты), если нужен только review.
- По умолчанию давай только `Read`.
- Не проси Claude "сделать всё". Проси critique (критику) конкретного решения.
- Не принимай его вывод без сверки с локальным проектом и `AGENTS.md`.

## Practical Rules

- Для больших prompt-ов используй файл в `/tmp`.
- Если нужен короткий финальный verdict (вердикт), добирай его отдельным follow-up prompt-ом через `--resume`.
- Если Claude формулирует вывод слишком широко, сужай итог до подтвержденных фактов источника.

## Output Integration

После ответа Claude всегда своди вывод к одному из форматов:

- `подтвердил / опроверг / усилил`;
- `оставляем / меняем / запрещаем`;
- `факт / интерпретация / решение`.
