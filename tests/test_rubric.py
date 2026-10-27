import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from madset_eval.rubric import RUBRIC, next_version, replace_quality_standard_section, validate_rubric
from madset_eval.ui_server import save_rubric


class RubricTests(unittest.TestCase):
    def test_default_rubric_is_valid(self):
        self.assertTrue(validate_rubric(RUBRIC))
        self.assertEqual(sum(item["weight"] for item in RUBRIC["dimensions"]), 100)

    def test_invalid_weight_total_is_rejected(self):
        changed = copy.deepcopy(RUBRIC)
        changed["dimensions"][0]["weight"] += 1
        with self.assertRaisesRegex(ValueError, "total 100"):
            validate_rubric(changed)

    def test_version_increments(self):
        self.assertEqual(next_version("1.1-provisional"), "1.1-provisional-ui.1")
        self.assertEqual(next_version("1.1-provisional-ui.9"), "1.1-provisional-ui.10")

    def test_quality_section_is_replaced(self):
        source = "# Standard\n\n## 5. Old\nold\n\n## 6. Critical\nkeep\n"
        result = replace_quality_standard_section(source, RUBRIC)
        self.assertIn("| Veri ve matematik | 20", result)
        self.assertIn("## 6. Critical\nkeep", result)
        self.assertNotIn("old", result)

    def test_save_updates_config_document_and_manifest(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            rubric_path = root / "rubric.json"
            quality_path = root / "QUALITY_STANDARD.md"
            manifest_path = root / "manifest.json"
            rubric_path.write_text(json.dumps(RUBRIC, ensure_ascii=False), encoding="utf-8")
            quality_path.write_text("# Standard\n\n## 5. Old\nold\n\n## 6. Critical\nkeep\n", encoding="utf-8")
            manifest_path.write_text(json.dumps({"files": {"docs/QUALITY_STANDARD.md": "old"}}), encoding="utf-8")

            changed = copy.deepcopy(RUBRIC)
            changed["threshold"] = 81
            saved = save_rubric(changed, rubric_path, quality_path, manifest_path)

            self.assertEqual(saved["version"], next_version(RUBRIC["version"]))
            self.assertEqual(json.loads(rubric_path.read_text(encoding="utf-8"))["threshold"], 81)
            self.assertIn("`>= 81/100`", quality_path.read_text(encoding="utf-8"))
            expected_hash = hashlib.sha256(quality_path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["files"]["docs/QUALITY_STANDARD.md"], expected_hash)


if __name__ == "__main__":
    unittest.main()
