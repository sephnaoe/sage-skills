"""Known-failure baseline: scoped suppression of findings by check + code."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - yaml optional for baseline authoring
    yaml = None


class BaselineError(ValueError):
    """Raised when a baseline file is malformed or cannot be loaded."""


@dataclass
class Entry:
    check: str
    codes: List[str] = field(default_factory=list)
    reasons: Dict[str, str] = field(default_factory=dict)

    @property
    def reason(self) -> str:
        """Backward-compatible entry-level reason: the first code's reason.

        Retained so existing callers that read ``entry.reason`` keep working;
        the authoritative, per-code reasons live in ``self.reasons``.
        """
        for code in self.codes:
            return self.reasons.get(code, "")
        return ""

    def reason_for(self, code: str) -> str:
        """Return the reason recorded for a specific code."""
        return self.reasons.get(code, "")

    def to_dict(self) -> dict:
        return {
            "check": self.check,
            "codes": list(self.codes),
            "reasons": dict(self.reasons),
            "reason": self.reason,
        }


@dataclass
class Baseline:
    baseline: List[Entry] = field(default_factory=list)

    def add(self, check: str, code: str, reason: str = "") -> None:
        """Mark (check, code) as a known failure, keeping the reason per code.

        A reason passed for a code already baselined under a different reason is
        kept as the newest reason for that code rather than discarded, and a new
        code on an existing check keeps its own reason instead of inheriting the
        entry's first one.
        """
        for entry in self.baseline:
            if entry.check != check:
                continue
            if code not in entry.codes:
                entry.codes.append(code)
            if reason:
                entry.reasons[code] = reason
            return
        self.baseline.append(
            Entry(check=check, codes=[code], reasons=({code: reason} if reason else {}))
        )

    def suppress(self, check: str, code: str) -> Optional[str]:
        """Return the reason for a known (check, code), else None."""
        for entry in self.baseline:
            if entry.check == check and code in entry.codes:
                return entry.reason_for(code) or None
        return None

    @classmethod
    def from_file(cls, path: Path) -> "Baseline":
        """Load a baseline from YAML.

        A missing file with no baseline yet is an empty baseline; a file that
        exists but cannot be parsed, or whose entries are malformed, raises
        BaselineError instead of silently yielding no suppression.
        """
        baseline = cls()
        if not path.exists():
            return baseline
        if yaml is None:
            raise RuntimeError(
                "PyYAML is required to read a baseline file; install PyYAML "
                "or pass no --baseline path."
            )
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (yaml.YAMLError, UnicodeDecodeError) as exc:
            raise BaselineError("baseline %s is not valid YAML: %s" % (path, exc)) from exc

        if data is None:
            return baseline
        if not isinstance(data, dict):
            raise BaselineError(
                "baseline %s must be a mapping with a 'baseline' list" % path
            )
        items = data.get("baseline", [])
        if items is None:
            items = []
        if not isinstance(items, list):
            raise BaselineError("baseline %s: 'baseline' must be a list" % path)

        for i, item in enumerate(items):
            if not isinstance(item, dict):
                raise BaselineError("baseline %s: entry %d is not a mapping" % (path, i))
            check = item.get("check")
            if not check or not isinstance(check, str):
                raise BaselineError(
                    "baseline %s: entry %d has no valid 'check'" % (path, i)
                )
            codes = item.get("codes", [])
            if codes is None:
                codes = []
            if not isinstance(codes, list) or any(not isinstance(c, str) for c in codes):
                raise BaselineError(
                    "baseline %s: entry %d 'codes' must be a list of strings" % (path, i)
                )
            entry = Entry(check=check, codes=list(codes))
            reasons = item.get("reasons")
            if isinstance(reasons, dict):
                for code, why in reasons.items():
                    if isinstance(why, str):
                        entry.reasons[code] = why
            # Legacy single 'reason' key applies to every code listed.
            legacy = item.get("reason")
            if isinstance(legacy, str) and legacy:
                for code in entry.codes:
                    entry.reasons.setdefault(code, legacy)
            baseline.baseline.append(entry)
        return baseline

    def to_dict(self) -> dict:
        return {"baseline": [e.to_dict() for e in self.baseline]}

    @classmethod
    def _dumps(cls, data: dict) -> str:
        if yaml is not None:
            return yaml.safe_dump(data, sort_keys=False)
        import json

        return json.dumps(data, indent=2)

    def write(self, path: Path) -> None:
        """Write the baseline atomically.

        A crash mid-write must not truncate the file into a baseline that
        suppresses nothing, and a baseline directory that does not exist yet is
        created rather than failing at the final step.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        data = self._dumps(self.to_dict())
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(data, encoding="utf-8")
        os.replace(tmp, path)