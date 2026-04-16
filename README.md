# Codex Iterative Skills

Этот репозиторий упаковывает два навыка для управляемой работы через итерации ревью.

Что здесь лежит:

- `iterative-plan-review` строит рабочий план по задаче, прогоняет его через до трёх независимых проходов критического ревью и поднимает пользователю только бизнес-развилки.
- `iterative-review-fix` закрывает цикл `review -> fix -> re-review`, сохраняет весь след артефактов и поднимает пользователю только решения, которые меняют бизнес-смысл.

Оба навыка сохраняют историю работы и артефакты в файловую структуру, чтобы результат можно было восстановить, проверить и продолжить.

## Repository Layout

```text
skills/
  iterative-plan-review/
    SKILL.md
    agents/openai.yaml
    references/artifact-layout.md
    scripts/init_plan_review_run.py
  iterative-review-fix/
    SKILL.md
    agents/openai.yaml
    references/artifact-layout.md
    scripts/init_review_fix_run.py
```

## Why These Skills Exist

Обычный агент часто либо слишком быстро принимает спорные решения, либо теряет след изменений между раундами обсуждения.

Эти навыки решают это через явный процесс:

- отделяют рабочие улучшения от бизнес-выборов;
- добавляют независимое критическое ревью;
- сохраняют историю вопросов, ответов и изменений;
- останавливают цикл раньше третьей итерации, когда существенных замечаний уже нет.

## Installation

Скопируй нужные директории в `$CODEX_HOME/skills`.

Если `CODEX_HOME` у тебя не задан, Codex обычно использует `~/.codex`.

Пример:

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R skills/iterative-plan-review "${CODEX_HOME:-$HOME/.codex}/skills/"
cp -R skills/iterative-review-fix "${CODEX_HOME:-$HOME/.codex}/skills/"
```

## Usage

Примеры запросов:

- `Use $iterative-plan-review to turn this task into a working plan and review it up to three times.`
- `Use $iterative-review-fix to close these review findings and keep the full artifact trail.`

Оба навыка уже включают:

- шаблон артефактной структуры;
- скрипт инициализации рабочего прогона;
- prompt contract (контракт промпта) для субагента;
- явный запрет на каскадную делегацию из субагента.
