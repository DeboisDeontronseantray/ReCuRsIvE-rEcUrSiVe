import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
with patch.dict(sys.modules, {"openai": types.ModuleType("openai")}):
    from app import model_routing


class ModelRoutingKeyTests(unittest.TestCase):
    FILE_KEY = "fake-file-key-for-tests"
    ENV_KEY = "fake-env-key-for-tests"
    DELETED_KEY = "fake-deleted-key-for-tests"

    def setUp(self):
        directory = self.enterContext(tempfile.TemporaryDirectory())
        self.default_path = Path(directory) / "default.key"
        self.override_path = Path(directory) / "override.key"
        self.enterContext(patch.object(
            model_routing, "DEFAULT_XAI_KEY_FILE", str(self.default_path)
        ))
        self.enterContext(patch.dict(os.environ, {}, clear=True))

    def assert_key_error(self, *expected):
        with self.assertRaises(RuntimeError) as raised:
            model_routing._require_xai_key()
        message = str(raised.exception)
        for text in expected:
            self.assertIn(text, message)
        for key in (self.FILE_KEY, self.ENV_KEY, self.DELETED_KEY):
            self.assertNotIn(key, message)

    def test_explicit_file_precedes_default_and_env(self):
        self.override_path.write_text(f" \n{self.FILE_KEY}\t\n")
        self.default_path.write_text("unused-default-key")
        os.environ.update(XAI_KEY_FILE=str(self.override_path), XAI_API_KEY=self.ENV_KEY)
        self.assertEqual(model_routing._require_xai_key(), self.FILE_KEY)

    def test_missing_explicit_file_does_not_fall_back(self):
        self.default_path.write_text(self.FILE_KEY)
        os.environ.update(XAI_KEY_FILE=str(self.override_path), XAI_API_KEY=self.ENV_KEY)
        self.assert_key_error("XAI_KEY_FILE", str(self.override_path))

    def test_unreadable_explicit_file_does_not_fall_back(self):
        os.environ.update(XAI_KEY_FILE=str(self.override_path), XAI_API_KEY=self.ENV_KEY)
        with patch.object(Path, "read_text", side_effect=PermissionError(self.FILE_KEY)):
            self.assert_key_error("XAI_KEY_FILE", str(self.override_path))

    def test_empty_explicit_file_does_not_fall_back(self):
        self.override_path.write_text(" \n\t")
        os.environ.update(XAI_KEY_FILE=str(self.override_path), XAI_API_KEY=self.ENV_KEY)
        self.assert_key_error("XAI_KEY_FILE", str(self.override_path), "empty")

    def test_empty_explicit_path_does_not_fall_back(self):
        os.environ.update(XAI_KEY_FILE="", XAI_API_KEY=self.ENV_KEY)
        self.assert_key_error("XAI_KEY_FILE")

    def test_default_file_precedes_env(self):
        self.default_path.write_text(f" \n{self.FILE_KEY}\t\n")
        os.environ["XAI_API_KEY"] = self.ENV_KEY
        self.assertEqual(model_routing._require_xai_key(), self.FILE_KEY)

    def test_empty_default_file_does_not_fall_back(self):
        self.default_path.write_text(" \n\t")
        os.environ["XAI_API_KEY"] = self.ENV_KEY
        self.assert_key_error(str(self.default_path), "empty")

    def test_unreadable_default_file_does_not_fall_back(self):
        self.default_path.write_text(self.FILE_KEY)
        os.environ["XAI_API_KEY"] = self.ENV_KEY
        with patch.object(Path, "read_text", side_effect=PermissionError(self.FILE_KEY)):
            self.assert_key_error(str(self.default_path))

    def test_invalid_encoding_does_not_expose_contents(self):
        self.override_path.write_bytes(self.FILE_KEY.encode() + b"\xff")
        os.environ.update(XAI_KEY_FILE=str(self.override_path), XAI_API_KEY=self.ENV_KEY)
        self.assert_key_error("XAI_KEY_FILE", str(self.override_path))

    def test_legacy_env_fallback(self):
        os.environ["XAI_API_KEY"] = self.ENV_KEY
        self.assertEqual(model_routing._require_xai_key(), self.ENV_KEY)

    def test_deleted_alias_is_ignored(self):
        os.environ["GROK_API_KEY"] = self.DELETED_KEY
        self.assert_key_error("xAI key missing", "XAI_KEY_FILE", "Do not invent a new key.")

    def test_missing_key(self):
        self.assert_key_error(
            "xAI key missing: set XAI_KEY_FILE to a key file, or put the render key at "
            "/workspace/private/keys/xai-render.key (XAI_API_KEY env is a legacy "
            "fallback). Do not invent a new key."
        )


if __name__ == "__main__":
    unittest.main()
