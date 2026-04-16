# Codex Iterative Skills

Этот репозиторий упаковывает три навыка для управляемой работы через итерации и финальное ревью.

Что здесь лежит:

- `iterative-plan-review` строит рабочий план по задаче, прогоняет его через до трёх независимых проходов критического ревью и поднимает пользователю только бизнес-развилки.
- `iterative-review-fix` закрывает цикл `review -> fix -> re-review`, сохраняет весь след артефактов, опционально использует `$final-gate-review` внутри review-субагента и поднимает пользователю только решения, которые меняют бизнес-смысл.
- `final-gate-review` даёт отдельный жёсткий финальный quality gate (контроль качества) для staged change set (подготовленного набора изменений), ищет long impact (долгий эффект), архитектурные риски и пропущенные сценарии и возвращает результат прямо в ответе без отдельного файла в репозитории.

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
  final-gate-review/
    SKILL.md
```

## Why These Skills Exist

Обычный агент часто либо слишком быстро принимает спорные решения, либо теряет след изменений между раундами обсуждения.

Эти навыки решают это через явный процесс:

- отделяют рабочие улучшения от бизнес-выборов;
- добавляют независимое критическое ревью;
- сохраняют историю вопросов, ответов и изменений;
- останавливают цикл раньше третьей итерации, когда открытых findings уже нет вообще.

## Installation

Скопируй нужные директории в `$CODEX_HOME/skills`.

Если `CODEX_HOME` у тебя не задан, Codex обычно использует `~/.codex`.

Пример:

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R skills/iterative-plan-review "${CODEX_HOME:-$HOME/.codex}/skills/"
cp -R skills/iterative-review-fix "${CODEX_HOME:-$HOME/.codex}/skills/"
cp -R skills/final-gate-review "${CODEX_HOME:-$HOME/.codex}/skills/"
```

## Usage

Примеры запросов:

- `Use $iterative-plan-review to turn this task into a working plan and review it up to three times.`
- `Use $iterative-review-fix to close these review findings and keep the full artifact trail.`
- `Use $final-gate-review to perform a final principal-level review of the staged change set.`

Оба навыка уже включают:

- шаблон артефактной структуры;
- скрипт инициализации рабочего прогона;
- prompt contract (контракт промпта) для субагента;
- явный запрет на каскадную делегацию из субагента.

`iterative-review-fix` дополнительно умеет:

- использовать `$final-gate-review`, если этот skill доступен в сессии review-субагента;
- работать без него, если skill не установлен;
- считать цикл завершённым только при нуле открытых findings любого уровня.

`final-gate-review` полезен отдельно, когда нужен последний независимый архитектурный и продуктовый фильтр перед merge (вливанием). Он работает во встроенном режиме: показывает findings сразу в ответе, а сохранение в артефакты оставляет вызывающему workflow.
