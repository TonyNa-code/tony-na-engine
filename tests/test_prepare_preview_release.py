from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "tools" / "release" / "prepare_preview_release.py"

spec = importlib.util.spec_from_file_location("prepare_preview_release", MODULE_PATH)
prepare_preview_release = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(prepare_preview_release)


class PreviewReleaseBodyTests(unittest.TestCase):
    def test_release_body_includes_public_download_guide(self) -> None:
        report = {
            "githubActions": {"checked": True, "status": "completed", "conclusion": "success"},
            "privacy": {"sensitiveFindings": []},
            "git": {"workingTreeClean": True},
            "artifacts": [
                {
                    "name": "TonyNaEngine-macos-preview.zip",
                    "kind": "editor-package",
                    "sizeLabel": "42.0 MB",
                    "sha256": "a" * 64,
                },
                {
                    "name": "SampleGame-native_runtime-preview.zip",
                    "kind": "native-runtime",
                    "sizeLabel": "18.0 MB",
                    "sha256": "b" * 64,
                },
                {
                    "name": "SampleGame-old-native_runtime-preview.zip",
                    "kind": "native-runtime",
                    "sizeLabel": "12.0 MB",
                    "sha256": "c" * 64,
                },
            ],
        }

        body = prepare_preview_release.render_release_body(report)

        self.assertIn("## Download Guide", body)
        self.assertIn("### Recommended Assets", body)
        self.assertIn("TonyNaEngine-macos-preview.zip", body)
        self.assertIn("SampleGame-native_runtime-preview.zip", body)
        self.assertNotIn("SampleGame-old-native_runtime-preview.zip", body)
        self.assertIn("Try the editor without cloning source", body)
        self.assertIn("Native Runtime packages include their own validation reports", body)
        self.assertIn("additional local artifact", body)
        self.assertIn("## Verification", body)
        self.assertIn("Privacy scan findings: `0`", body)

    def test_release_body_has_source_fallback_when_no_artifacts(self) -> None:
        report = {
            "githubActions": {"checked": False, "reason": "network skipped"},
            "privacy": {"sensitiveFindings": []},
            "git": {"workingTreeClean": True},
            "artifacts": [],
        }

        body = prepare_preview_release.render_release_body(report)

        self.assertIn("No binary package is attached", body)
        self.assertIn("Source code archive", body)
        self.assertIn("GitHub Actions: not checked", body)


if __name__ == "__main__":
    unittest.main()
