# Style and conventions

## Formatting

- Line length: 130 (`ruff.toml`)
- Quote style: preserve (don't normalize quotes)
- LF line endings enforced (`.gitattributes`, `.editorconfig`, ruff)

## Imports

Managed by isort via ruff:

- `combine-as-imports`
- `no-sections`
- `order-by-type`

## Lint and format commands

```bash
# Lint (fix mode, exits non-zero if fixes applied)
uv run ruff check --fix --exit-non-zero-on-fix .

# Format check / apply
uv run ruff format --check --diff .
uv run ruff format .

# Type check
uv run mypy src/

# Pre-commit (runs ruff, markdownlint, misc hooks; fail_fast: true)
prek run --all-files
```

## Markdown tables

markdownlint enforces aligned table columns (MD060). When writing markdown tables, generate them programmatically to guarantee pipe alignment:

```python
rows = [["Header1", "Header2"], ["cell", "cell"]]
widths = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]
def fmt(row):
    return "| " + " | ".join(c.ljust(w) for c, w in zip(row, widths)) + " |"
print(fmt(rows[0]))
print("| " + " | ".join("-" * w for w in widths) + " |")
for row in rows[1:]:
    print(fmt(row))
```

Do NOT hand-align tables -- column math is error-prone and markdownlint rejects even single-character misalignment.

## Model conventions

- Models use `mashumaro` `field_options(alias=...)` to map camelCase API fields to snake_case
- `__pre_deserialize__` classmethod on models handles API inconsistencies (e.g. empty string -> None)
