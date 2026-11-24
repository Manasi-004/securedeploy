#!/usr/bin/env python3
"""Turn a SARIF file into GitHub Actions annotations (works on private repos,
no paid code-scanning feature needed) and a short job summary.

usage: sarif_to_annotations.py <file.sarif> "<Tool name>"
"""
import json
import os
import pathlib
import sys

MAX_ANNOTATIONS = 40  # GitHub shows only the first ~50 per job
LEVELS = {"error": "error", "warning": "warning", "note": "notice", "none": "notice"}


def esc(text: str) -> str:
    return text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def esc_prop(text: str) -> str:
    return esc(text).replace(":", "%3A").replace(",", "%2C")


def resolve(uri: str):
    """Find the repo-relative path for a path found in a SARIF file."""
    p = uri
    if p.startswith("file://"):
        p = p[len("file://"):]
    p = p.replace("\\", "/")
    ws = (os.environ.get("GITHUB_WORKSPACE") or os.getcwd()).replace("\\", "/")
    if p.startswith(ws):
        p = p[len(ws):]
    p = p.lstrip("/")
    root = pathlib.Path(".")
    if p and (root / p).is_file():
        return p
    parts = [x for x in p.split("/") if x]
    for i in range(len(parts)):
        suffix = "/".join(parts[i:])
        found = sorted(
            str(m).replace("\\", "/")
            for m in root.rglob(parts[-1])
            if str(m).replace("\\", "/").endswith(suffix)
            and ".git/" not in str(m).replace("\\", "/")
            and ".terraform" not in str(m)
        )
        if found:
            return found[0]
    return None


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: sarif_to_annotations.py <file.sarif> <tool name>")
        return 2
    path, tool = sys.argv[1], sys.argv[2]
    if not os.path.isfile(path):
        print(f"::notice title={tool}::No results file ({path}); the tool may not have run.")
        return 0
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as exc:
        print(f"::warning title={tool}::Could not read {path}: {exc}")
        return 0

    findings = []
    for run in data.get("runs", []):
        rules = {}
        for rule in run.get("tool", {}).get("driver", {}).get("rules", []) or []:
            rules[rule.get("id")] = rule
        for res in run.get("results", []) or []:
            rule_id = res.get("ruleId", "unknown-rule")
            level = res.get("level")
            if not level:
                level = (rules.get(rule_id, {}).get("defaultConfiguration", {}) or {}).get("level", "warning")
            text = (res.get("message", {}) or {}).get("text", "").strip() or rule_id
            file_path, line = None, 1
            locs = res.get("locations") or []
            if locs:
                phys = locs[0].get("physicalLocation", {}) or {}
                uri = (phys.get("artifactLocation", {}) or {}).get("uri")
                if uri:
                    file_path = resolve(uri)
                line = (phys.get("region", {}) or {}).get("startLine", 1) or 1
            findings.append((LEVELS.get(level, "warning"), rule_id, text, file_path, line))

    print(f"{tool}: {len(findings)} finding(s)")
    for kind, rule_id, text, file_path, line in findings[:MAX_ANNOTATIONS]:
        props = f"title={esc_prop(tool + ' | ' + rule_id)}"
        if file_path:
            props = f"file={esc_prop(file_path)},line={line}," + props
        print(f"::{kind} {props}::{esc(text)}")
    if len(findings) > MAX_ANNOTATIONS:
        print(f"::notice title={tool}::{len(findings) - MAX_ANNOTATIONS} more finding(s) not shown. Download the SARIF artifact.")

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(f"### {tool}: {len(findings)} finding(s)\n\n")
            if findings:
                fh.write("| Level | Rule | File | Line |\n|---|---|---|---|\n")
                for kind, rule_id, _t, file_path, line in findings[:100]:
                    fh.write(f"| {kind} | `{rule_id}` | {file_path or '-'} | {line} |\n")
                fh.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
