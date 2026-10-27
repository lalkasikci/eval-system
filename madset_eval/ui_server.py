"""Local-only UI server that safely persists rubric edits into the project."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import mimetypes
import os
import re
import subprocess
import sys
import shutil
import tempfile
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from .rubric import (
    ROOT,
    RUBRIC_PATH,
    load_rubric,
    replace_quality_standard_section,
    validate_rubric,
    with_next_version,
)
from .contracts import validate_expectation, validate_input

UI_ROOT = ROOT / "ui"
QUALITY_STANDARD = ROOT / "docs" / "QUALITY_STANDARD.md"
MANIFEST = ROOT / "data" / "manifest.json"
MAX_BODY = 64 * 1024
DEV_SCENARIOS = ROOT / "data" / "dev" / "scenarios.json"
SCENARIO_INDEX = ROOT / "data" / "scenario_index.csv"


def _atomic_write(path, text):
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def _manifest_hash(path):
    content = Path(path).read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(content).hexdigest()


def save_rubric(value, rubric_path=RUBRIC_PATH, quality_standard=QUALITY_STANDARD, manifest_path=MANIFEST):
    validate_rubric(value)
    rubric_path = Path(rubric_path)
    quality_standard = Path(quality_standard)
    manifest_path = Path(manifest_path)
    current = load_rubric(rubric_path)
    updated = with_next_version(value, current["version"])
    original_markdown = quality_standard.read_text(encoding="utf-8")
    updated_markdown = replace_quality_standard_section(original_markdown, updated)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    _atomic_write(rubric_path, json.dumps(updated, ensure_ascii=False, indent=2) + "\n")
    _atomic_write(quality_standard, updated_markdown)
    manifest["files"]["data/rubric.json"] = _manifest_hash(rubric_path)
    manifest["files"]["docs/QUALITY_STANDARD.md"] = _manifest_hash(quality_standard)
    _atomic_write(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return updated


def refresh_offline_artifacts():
    """Re-run key-free eval outputs and reports. Never invokes Claude or product APIs."""
    rubric = load_rubric()
    test_count = unittest.defaultTestLoader.discover(str(ROOT / "tests")).countTestCases()
    report_path = ROOT / "docs" / "FINAL_REPORT.md"
    report = report_path.read_text(encoding="utf-8")
    report = re.sub(r"Geçiş için en az \d+(?:\.\d+)?/100", f"Geçiş için en az {rubric['threshold']:g}/100", report)
    report = re.sub(r"\d+ anahtarsız test", f"{test_count} anahtarsız test", report)
    _atomic_write(report_path, report)
    decisions_path = ROOT / "docs" / "DECISIONS.md"
    decisions = decisions_path.read_text(encoding="utf-8")
    decisions = re.sub(r"\*\*Eşikler:\*\* \d+(?:\.\d+)?/100", f"**Eşikler:** {rubric['threshold']:g}/100", decisions)
    _atomic_write(decisions_path, decisions)
    pdf_python = sys.executable
    try:
        __import__("reportlab")
    except ImportError:
        bundled = Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "python" / "python.exe"
        if bundled.is_file():
            pdf_python = str(bundled)
    logs = []
    with tempfile.TemporaryDirectory(prefix="madset-ui-refresh-") as temporary:
        temp_output = Path(temporary) / "demo"
        commands = [
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
            [sys.executable, "-m", "madset_eval", "demo", "--out", str(temp_output)],
            [pdf_python, "scripts/build_final_report.py"],
        ]
        for command in commands:
            completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=120)
            logs.append({"command": " ".join(command[1:]), "returncode": completed.returncode})
            if completed.returncode:
                detail = (completed.stderr or completed.stdout)[-1000:]
                raise RuntimeError(f"refresh command failed: {' '.join(command[1:])}: {detail}")
        demo_output = ROOT / "outputs" / "demo"
        demo_output.mkdir(parents=True, exist_ok=True)
        for filename in ("SUMMARY.json", "DASHBOARD.html", "FINAL_REPORT.md"):
            shutil.copyfile(temp_output / filename, demo_output / filename)
    return {
        "rubric_version": rubric["version"],
        "test_count": test_count,
        "updated": ["outputs/demo/SUMMARY.json", "outputs/demo/DASHBOARD.html", "outputs/demo/FINAL_REPORT.md", "docs/DECISIONS.md", "docs/FINAL_REPORT.md", "docs/FINAL_REPORT.pdf"],
        "commands": logs,
        "external_api_calls": 0,
    }


def _read_json(path, default=None):
    path = Path(path)
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def eval_catalog():
    """Return compact, already-recorded eval results; never starts an API call."""
    sources = []
    offline = _read_json(ROOT / "outputs" / "demo" / "SUMMARY.json")
    if offline:
        sources.append({"id": "offline", "label": "Offline V1/V2/V3", "kind": "comparison", "data": offline})
    reliability = _read_json(ROOT / "outputs" / "claude_judge_reliability" / "SUMMARY.json")
    if reliability:
        sources.append({"id": "reliability", "label": "Claude güvenilirlik · 3 tekrar", "kind": "reliability", "data": reliability})
    candidates = sorted((ROOT / "outputs" / "claude_judge").rglob("*_regraded.json"), key=lambda p: p.stat().st_mtime, reverse=True) if (ROOT / "outputs" / "claude_judge").is_dir() else []
    if candidates:
        latest = _read_json(candidates[0], {})
        sources.append({
            "id": "latest-claude",
            "label": "Son Claude yargıç koşusu",
            "kind": "single",
            "path": candidates[0].relative_to(ROOT).as_posix(),
            "data": {"summary": latest.get("summary", {}), "metadata": latest.get("metadata", {})},
        })
    return {"sources": sources, "external_api_calls": 0}


def scenario_catalog():
    dev = _read_json(DEV_SCENARIOS, [])
    holdout = _read_json(ROOT / "data" / "holdout" / "inputs.json", [])
    holdout_v2 = _read_json(ROOT / "data" / "holdout_v2" / "inputs.json", [])
    return {
        "counts": {"dev": len(dev), "holdout": len(holdout), "holdout_v2": len(holdout_v2)},
        "dev": [{
            "id": row["id"], "group": row.get("group", ""),
            "sector": row["input"].get("sector", ""), "platform": row["input"].get("platform", ""),
            "objective": row["input"].get("objective", ""),
            "decision": "/".join(row["expectation"].get("allowed_decisions", [])),
        } for row in dev],
        "holdout_policy": "Kör setler bu ekrandan değiştirilemez. Yeni model sürümü için bağımsız kişi yeni holdout üretmelidir.",
    }


def save_dev_scenario(record, scenarios_path=DEV_SCENARIOS, manifest_path=MANIFEST, index_path=SCENARIO_INDEX):
    if not isinstance(record, dict) or not re.fullmatch(r"ADV-\d{3}", str(record.get("id", ""))):
        raise ValueError("id ADV-000 biçiminde olmalı")
    if not isinstance(record.get("group"), str) or not record["group"].strip():
        raise ValueError("group gerekli")
    scenario_id = record["id"]
    if not isinstance(record.get("input"), dict) or not isinstance(record.get("expectation"), dict):
        raise ValueError("input ve expectation nesneleri gerekli")
    if record["input"].get("scenario_id") != scenario_id:
        raise ValueError("input.scenario_id ile id aynı olmalı")
    validate_input(record["input"])
    validate_expectation(record["expectation"])
    scenarios_path, manifest_path, index_path = map(Path, (scenarios_path, manifest_path, index_path))
    scenarios = _read_json(scenarios_path, [])
    known = {row.get("id") for row in scenarios}
    if scenarios_path == DEV_SCENARIOS:
        for split_path in (ROOT / "data" / "holdout" / "inputs.json", ROOT / "data" / "holdout_v2" / "inputs.json"):
            known.update(row.get("id") or row.get("scenario_id") for row in _read_json(split_path, []))
    if scenario_id in known:
        raise ValueError(f"scenario id already exists: {scenario_id}")
    scenarios.append(record)
    _atomic_write(scenarios_path, json.dumps(scenarios, ensure_ascii=False, indent=2) + "\n")
    if index_path.exists():
        with index_path.open("a", encoding="utf-8", newline="") as handle:
            csv.writer(handle).writerow([scenario_id, record["group"], record["input"]["sector"], record["input"]["platform"], record["input"]["objective"], "/".join(record["expectation"]["allowed_decisions"]), "dev"])
    manifest = _read_json(manifest_path, {"files": {}, "split": {}})
    manifest.setdefault("files", {})["data/dev/scenarios.json"] = _manifest_hash(scenarios_path)
    manifest.setdefault("split", {})["dev"] = len(scenarios)
    _atomic_write(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return {"scenario": scenario_id, "dev_count": len(scenarios), "files_changed": ["data/dev/scenarios.json", "data/scenario_index.csv", "data/manifest.json"]}


class Handler(BaseHTTPRequestHandler):
    server_version = "MadsetUI/1.0"

    def _json(self, status, value):
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _origin_allowed(self):
        origin = self.headers.get("Origin")
        return origin is None or origin.startswith("http://127.0.0.1:") or origin.startswith("http://localhost:")

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/rubric":
            return self._json(200, {"rubric": load_rubric(), "persistence": "project-files"})
        if path == "/api/eval-results":
            return self._json(200, eval_catalog())
        if path == "/api/scenarios":
            return self._json(200, scenario_catalog())
        if path == "/api/integration-status":
            return self._json(200, {"adapter_ready": (ROOT / "examples" / "madset_adapter.py").is_file(), "endpoint_configured": bool(os.environ.get("MADSET_ADVISE_ENDPOINT")), "real_data_connected": False})
        relative = "index.html" if path in ("", "/") else unquote(path.lstrip("/"))
        target = (UI_ROOT / relative).resolve()
        try:
            target.relative_to(UI_ROOT.resolve())
        except ValueError:
            return self.send_error(403)
        if not target.is_file():
            return self.send_error(404)
        body = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", (mimetypes.guess_type(target.name)[0] or "application/octet-stream") + ("; charset=utf-8" if target.suffix in (".html", ".json", ".md") else ""))
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_PUT(self):
        if urlparse(self.path).path != "/api/rubric":
            return self.send_error(404)
        if not self._origin_allowed():
            return self._json(403, {"error": "origin not allowed"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 1 or length > MAX_BODY:
                raise ValueError("invalid request size")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            updated = save_rubric(payload)
            return self._json(200, {
                "rubric": updated,
                "files_changed": ["data/rubric.json", "docs/QUALITY_STANDARD.md", "data/manifest.json"],
            })
        except (ValueError, json.JSONDecodeError) as exc:
            return self._json(400, {"error": str(exc)})
        except Exception as exc:
            return self._json(500, {"error": f"save failed: {exc}"})

    def do_POST(self):
        path = urlparse(self.path).path
        if path not in ("/api/refresh", "/api/scenarios/dev"):
            return self.send_error(404)
        if not self._origin_allowed():
            return self._json(403, {"error": "origin not allowed"})
        try:
            if path == "/api/scenarios/dev":
                length = int(self.headers.get("Content-Length", "0"))
                if length < 1 or length > MAX_BODY:
                    raise ValueError("invalid request size")
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                return self._json(201, save_dev_scenario(payload))
            return self._json(200, refresh_offline_artifacts())
        except (ValueError, json.JSONDecodeError) as exc:
            return self._json(400, {"error": str(exc)})
        except Exception as exc:
            return self._json(500, {"error": f"refresh failed: {exc}"})

    def log_message(self, fmt, *args):
        print(f"[madset-ui] {self.address_string()} {fmt % args}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Madset UI and rubric persistence server")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Madset UI: http://127.0.0.1:{args.port}", flush=True)
    print("Rubrik kaydı proje dosyalarını günceller. Durdurmak için Ctrl+C.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
