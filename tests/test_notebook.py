import json
import unittest
from pathlib import Path


class NotebookTests(unittest.TestCase):
    def test_notebook_is_thin_unexecuted_and_bounded(self):
        path = Path("notebooks/01_pilot_colab.ipynb")
        notebook = json.loads(path.read_text())
        self.assertEqual(notebook["nbformat"], 4)
        cells = [c for c in notebook["cells"] if c["cell_type"] == "code"]
        for cell in cells:
            self.assertEqual(cell["outputs"], [])
            self.assertIsNone(cell["execution_count"])
            compile("".join(cell["source"]), str(path), "exec")
        parameters = "".join(cells[0]["source"])
        self.assertIn('PRESET = "smoke"', parameters)
        self.assertIn('STAGE = "smoke"', parameters)
        self.assertIn('RESUME = False', parameters)
        for name in ("REPO_URL", "GIT_REF", "RUN_ID", "SCRATCH_ROOT", "PERSISTENT_ROOT"):
            self.assertIn(name, parameters)
        self.assertNotIn("AutoModelForCausalLM", str(notebook))
