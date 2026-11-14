# Deprecation Policy — Impact Analyzer

## Versioning
- Semantic versioning (MAJOR.MINOR.PATCH)
- Breaking changes only in MAJOR versions
- Deprecation warnings added 1 MINOR version before removal

## Deprecation Process
1. Mark deprecated with @deprecated decorator and docstring warning
2. Add deprecation notice to CHANGELOG
3. Maintain deprecated API for at least 1 MINOR version
4. Remove in next MAJOR version

## Currently Deprecated
- None (v1.0.0 initial release)