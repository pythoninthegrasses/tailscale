# Style & Conventions

## Formatting
- Line length: 130
- Indent: 4 spaces
- Line endings: LF
- Quote style: preserve (don't change existing quotes)

## Imports
- isort via ruff: combine-as-imports, order-by-type, no-sections, from-first=false

## Models
- Use mashumaro DataClassDictMixin with orjson for serialization
- See docs/architecture.md for model design patterns

## Comments
- Explain WHAT or WHY, never "improved/better/new/enhanced"
- Never remove comments unless provably false

## Code Quality
- YAGNI principle
- Simple over clever
- Reduce duplication aggressively
- TDD for new features/bugfixes
