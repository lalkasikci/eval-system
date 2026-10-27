"""Versioned rubric configuration shared by the UI, graders and run metadata."""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUBRIC_PATH = ROOT / "data" / "rubric.json"
EXPECTED_DIMENSIONS = (
    "data_math",
    "diagnosis",
    "evidence_uncertainty",
    "strategy",
    "economics_risk",
    "actionability",
    "clarity",
)


def validate_rubric(value):
    if not isinstance(value, dict):
        raise ValueError("rubric must be an object")
    version = value.get("version")
    if not isinstance(version, str) or not version.strip() or len(version) > 80:
        raise ValueError("rubric version must be a short non-empty string")
    threshold = value.get("threshold")
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or not 0 <= threshold <= 100:
        raise ValueError("rubric threshold must be between 0 and 100")
    dimensions = value.get("dimensions")
    if not isinstance(dimensions, list) or len(dimensions) != len(EXPECTED_DIMENSIONS):
        raise ValueError("rubric must contain seven dimensions")
    if tuple(item.get("id") for item in dimensions if isinstance(item, dict)) != EXPECTED_DIMENSIONS:
        raise ValueError("rubric dimension ids or order changed")
    total = 0
    for item in dimensions:
        weight = item.get("weight")
        if isinstance(weight, bool) or not isinstance(weight, (int, float)) or not 0 <= weight <= 100:
            raise ValueError(f"invalid rubric weight: {item.get('id')}")
        total += weight
        for key in ("name", "zero", "two", "four"):
            text = item.get(key)
            if not isinstance(text, str) or not text.strip() or len(text) > 500:
                raise ValueError(f"invalid rubric text: {item.get('id')}.{key}")
    if abs(total - 100) > 1e-9:
        raise ValueError(f"rubric weights must total 100, got {total}")
    return True


def load_rubric(path=RUBRIC_PATH):
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_rubric(value)
    return value


def next_version(current):
    match = re.fullmatch(r"(.+)-ui\.(\d+)", current)
    if match:
        return f"{match.group(1)}-ui.{int(match.group(2)) + 1}"
    return f"{current}-ui.1"


def with_next_version(value, current_version):
    updated = copy.deepcopy(value)
    updated["version"] = next_version(current_version)
    validate_rubric(updated)
    return updated


def rubric_markdown_section(value):
    validate_rubric(value)
    rows = ["| Boyut | Ağırlık | 0 | 2 | 4 |", "|---|---:|---|---|---|"]
    for item in value["dimensions"]:
        rows.append(
            f"| {item['name']} | {item['weight']:g} | {item['zero']} | {item['two']} | {item['four']} |"
        )
    threshold = value["threshold"]
    return "\n".join([
        "## 5. Puanlama rubric'i (arayüzden yönetilen ağırlıklar)",
        f"**Aktif sürüm:** `{value['version']}`",
        "",
        "Her boyuta **0,1,2,3,4** verilir. Puan = Σ(ağırlık × boyut_puanı / 4). "
        "Ağırlıklar ve eşikler uzman-uyumu çalışmasıyla kalibre edilmelidir.",
        "",
        *rows,
        "",
        "**Ara puan çıpası:** 1 = ağırlıkla başarısız, 3 = çoğunlukla doğru ama belirgin kusur var. "
        "Uygulanamaz boyutlar keyfi sıfırlanmaz; bir N/A politikası kalibrasyonda kararlaştırılır.",
        "",
        f"**Geçiş:** Başlangıç operasyonel eşiği `>= {threshold:g}/100` + doğru veya kabul edilebilir karar + "
        "**sıfır kritik hata** + en az `%75` senaryoya özgü kavram kapsaması + karar sınıfına uygun "
        "protokol + grounded evidence. `90+` üstün kalite işaretidir, üretime çıkış garantisi değildir. "
        "Her değişiklik sürümlenir.",
        "",
    ])


def replace_quality_standard_section(markdown, value):
    start = markdown.find("## 5.")
    end = markdown.find("## 6.", start)
    if start < 0 or end < 0:
        raise ValueError("QUALITY_STANDARD.md section 5/6 boundary not found")
    return markdown[:start] + rubric_markdown_section(value) + markdown[end:]


RUBRIC = load_rubric()
WEIGHTS = {item["id"]: item["weight"] for item in RUBRIC["dimensions"]}
PASS_THRESHOLD = RUBRIC["threshold"]
RUBRIC_VERSION = RUBRIC["version"]
