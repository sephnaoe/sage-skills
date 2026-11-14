# Sage Skills

Repository: https://github.com/sephnaoe/sage-skills

A monorepo of shareable AI skills and tools from the Sage AI Assistant Platform.

## Packages

| Package | Description | Grade |
|---------|-------------|-------|
| [impact-analyzer](packages/impact-analyzer/) | Fast change-impact analysis for Python codebases | B (88/100) |

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