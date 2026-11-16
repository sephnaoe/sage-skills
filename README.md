# Sage Skills

Repository: https://github.com/sephnaoe/sage-skills

A monorepo of shareable AI skills and tools from the Sage AI Assistant Platform.

## Packages

| Package | Description | Grade |
|---------|-------------|-------|
| [impact-analyzer](packages/impact-analyzer/) | Multi-language change-impact analysis (Python, JS/TS, Go, Rust) | A (93/100) |
| [permguard](packages/permguard/) | Declarative permission-shape engine: substring glob rules over whole command strings, last-match-wins, order-aware drift detection | A |
| [healthgate](packages/healthgate/) | Declarative health-check engine: gate project phases on PASS/SKIPPED with a known-failure baseline | A |

## Structure

```
sage-skills/
├── packages/
│   ├── impact-analyzer/     # Change-impact analysis
│   ├── <next-skill>/        # Future skills
│   └── ...
├── README.md
├── LICENSE (Apache-2.0)
└── NOTICE
```

## Adding a New Skill

1. Create `packages/<skill-name>/`
2. Add `manifest.yaml` with capability contract
3. Add code, tests, docs, examples
4. Run grader: target Grade B or better before publishing

## License

Apache-2.0 (see LICENSE file)