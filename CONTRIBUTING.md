# Contributing

NEXUS is developed as a learning-focused Linux engineering project.

## Workflow

1. Create a focused branch.
2. Keep changes small and testable.
3. Add or update tests for behavior changes.
4. Run `python -m unittest discover -s tests -v`.
5. Use a conventional commit message such as `feat: add memory sensor`.
6. Open a pull request with a concise description of the change.

## Safety

Do not introduce destructive system commands without an explicit design review. Any future operation that can modify packages, services, files, or system configuration must have a dry-run mode and an explicit confirmation boundary.
