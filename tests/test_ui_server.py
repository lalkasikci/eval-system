import copy
import json
import tempfile
import unittest
from pathlib import Path

from madset_eval.contracts import load_json
from madset_eval.ui_server import eval_catalog, save_dev_scenario


class UiServerTests(unittest.TestCase):
    def test_eval_catalog_exposes_saved_results_without_api_call(self):
        catalog = eval_catalog()
        self.assertEqual(catalog["external_api_calls"], 0)
        kinds = {item["kind"] for item in catalog["sources"]}
        self.assertIn("comparison", kinds)
        self.assertIn("reliability", kinds)

    def test_save_dev_scenario_updates_all_local_indexes(self):
        record = copy.deepcopy(load_json(Path(__file__).parents[1] / "data" / "dev" / "scenarios.json")[0])
        record["id"] = "ADV-999"
        record["input"]["scenario_id"] = "ADV-999"
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            scenarios = root / "scenarios.json"
            manifest = root / "manifest.json"
            index = root / "scenario_index.csv"
            scenarios.write_text("[]\n", encoding="utf-8")
            manifest.write_text(json.dumps({"files": {}, "split": {}}), encoding="utf-8")
            index.write_text("id,group,sector,platform,objective,decision,set\n", encoding="utf-8")

            result = save_dev_scenario(record, scenarios, manifest, index)

            self.assertEqual(result["scenario"], "ADV-999")
            self.assertEqual(json.loads(scenarios.read_text(encoding="utf-8"))[0]["id"], "ADV-999")
            self.assertIn("ADV-999", index.read_text(encoding="utf-8"))
            saved_manifest = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(saved_manifest["split"]["dev"], 1)
            self.assertIn("data/dev/scenarios.json", saved_manifest["files"])

    def test_save_dev_scenario_rejects_duplicate(self):
        record = copy.deepcopy(load_json(Path(__file__).parents[1] / "data" / "dev" / "scenarios.json")[0])
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            scenarios = root / "scenarios.json"
            manifest = root / "manifest.json"
            index = root / "scenario_index.csv"
            scenarios.write_text(json.dumps([record], ensure_ascii=False), encoding="utf-8")
            manifest.write_text(json.dumps({"files": {}, "split": {}}), encoding="utf-8")
            index.write_text("id,group,sector,platform,objective,decision,set\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "already exists"):
                save_dev_scenario(record, scenarios, manifest, index)


if __name__ == "__main__":
    unittest.main()
