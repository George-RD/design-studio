from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "probe_github_models.py"


def load_probe():
    spec = importlib.util.spec_from_file_location("probe_github_models", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load probe from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeRequester:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, *, method, url, token, api_version, payload=None):
        self.calls.append(
            {
                "method": method,
                "url": url,
                "token": token,
                "api_version": api_version,
                "payload": payload,
            }
        )
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


def multimodal_model(model_id="openai/gpt-4.1", version="2025-04-14"):
    return {
        "id": model_id,
        "name": model_id,
        "version": version,
        "capabilities": ["streaming", "tool-calling"],
        "supported_input_modalities": ["text", "image"],
        "supported_output_modalities": ["text"],
        "limits": {"max_input_tokens": 1000, "max_output_tokens": 100},
    }


def completion(content, usage=None):
    value = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": json.dumps(content),
                }
            }
        ]
    }
    if usage is not None:
        value["usage"] = usage
    return value


class GitHubModelsCapabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.probe = load_probe()

    def test_choose_model_prefers_declared_order(self) -> None:
        catalog = [
            multimodal_model("openai/gpt-4o"),
            multimodal_model("openai/gpt-4.1"),
        ]

        selected = self.probe.choose_model(
            catalog,
            preferred=("openai/gpt-4.1", "openai/gpt-4o"),
        )

        self.assertEqual("openai/gpt-4.1", selected["id"])

    def test_choose_model_falls_back_to_a_multimodal_text_output_model(self) -> None:
        catalog = [
            {
                **multimodal_model("vendor/text-only"),
                "supported_input_modalities": ["text"],
            },
            multimodal_model("vendor/vision-model"),
        ]

        selected = self.probe.choose_model(catalog, preferred=("missing/model",))

        self.assertEqual("vendor/vision-model", selected["id"])

    def test_choose_model_rejects_catalog_without_required_modalities(self) -> None:
        catalog = [
            {
                **multimodal_model("vendor/text-only"),
                "supported_input_modalities": ["text"],
            }
        ]

        with self.assertRaisesRegex(self.probe.ProbeContractError, "text-and-image"):
            self.probe.choose_model(catalog, preferred=())

    def test_text_payload_requests_strict_structured_output(self) -> None:
        payload = self.probe.build_text_payload("openai/gpt-4.1")

        self.assertEqual("openai/gpt-4.1", payload["model"])
        self.assertEqual("json_schema", payload["response_format"]["type"])
        schema = payload["response_format"]["json_schema"]
        self.assertTrue(schema["strict"])
        self.assertFalse(schema["schema"]["additionalProperties"])
        self.assertEqual(["probe", "status"], schema["schema"]["required"])

    def test_vision_payload_embeds_a_png_and_strict_schema(self) -> None:
        payload = self.probe.build_vision_payload("openai/gpt-4.1", b"\x89PNG\r\n\x1a\nbody")

        content = payload["messages"][0]["content"]
        self.assertEqual("text", content[0]["type"])
        self.assertEqual("image_url", content[1]["type"])
        self.assertTrue(
            content[1]["image_url"]["url"].startswith("data:image/png;base64,")
        )
        schema = payload["response_format"]["json_schema"]["schema"]
        self.assertEqual(["leftColor", "rightColor"], schema["required"])

    def test_split_image_has_png_signature(self) -> None:
        image = self.probe.build_split_color_png(width=16, height=8)

        self.assertTrue(image.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertGreater(len(image), 50)

    def test_completion_content_must_be_structured_json(self) -> None:
        response = completion({"probe": "github-models", "status": "ok"})

        parsed = self.probe.parse_completion_json(response, "structured-text")

        self.assertEqual({"probe": "github-models", "status": "ok"}, parsed)

        with self.assertRaisesRegex(self.probe.ProbeContractError, "choices"):
            self.probe.parse_completion_json({}, "structured-text")

    def test_result_validators_require_exact_probe_answers(self) -> None:
        self.probe.validate_text_result(
            {"probe": "github-models", "status": "ok"}
        )
        self.probe.validate_vision_result(
            {"leftColor": "red", "rightColor": "blue"}
        )

        with self.assertRaisesRegex(self.probe.ProbeContractError, "unexpected"):
            self.probe.validate_text_result({"probe": "other", "status": "ok"})
        with self.assertRaisesRegex(self.probe.ProbeContractError, "unexpected"):
            self.probe.validate_vision_result(
                {"leftColor": "blue", "rightColor": "red"}
            )

    def test_api_error_classification_distinguishes_blockers(self) -> None:
        self.assertEqual("blocked", self.probe.classify_api_status(403))
        self.assertEqual("blocked", self.probe.classify_api_status(429))
        self.assertEqual("failed", self.probe.classify_api_status(422))
        self.assertEqual("failed", self.probe.classify_api_status(500))

    def test_successful_probe_records_catalog_text_vision_and_usage(self) -> None:
        requester = FakeRequester(
            [
                [multimodal_model()],
                completion(
                    {"probe": "github-models", "status": "ok"},
                    usage={"prompt_tokens": 20, "completion_tokens": 8},
                ),
                completion(
                    {"leftColor": "red", "rightColor": "blue"},
                    usage={"prompt_tokens": 100, "completion_tokens": 8},
                ),
            ]
        )

        with tempfile.TemporaryDirectory() as temporary:
            output_dir = Path(temporary)
            report = self.probe.run_probe(
                token="secret-token",
                output_dir=output_dir,
                requester=requester,
                preferred_models=("openai/gpt-4.1",),
                now=lambda: "2026-07-30T00:00:00Z",
            )

            self.assertEqual("passed", report["status"])
            self.assertEqual("openai/gpt-4.1", report["model"]["id"])
            self.assertEqual("passed", report["checks"]["structuredText"]["status"])
            self.assertEqual("passed", report["checks"]["vision"]["status"])
            self.assertEqual(
                {"prompt_tokens": 20, "completion_tokens": 8},
                report["checks"]["structuredText"]["usage"],
            )
            self.assertTrue((output_dir / "capability-report.json").is_file())
            self.assertTrue((output_dir / "probe-image.png").is_file())
            self.assertTrue((output_dir / "catalog-response.json").is_file())
            self.assertTrue((output_dir / "structured-text-response.json").is_file())
            self.assertTrue((output_dir / "vision-response.json").is_file())

            all_text = "\n".join(
                path.read_text(errors="ignore")
                for path in output_dir.rglob("*")
                if path.is_file() and path.suffix != ".png"
            )
            self.assertNotIn("secret-token", all_text)

        self.assertEqual(["GET", "POST", "POST"], [call["method"] for call in requester.calls])

    def test_permission_failure_is_blocked_and_preserves_report(self) -> None:
        requester = FakeRequester(
            [
                self.probe.ApiRequestError(
                    status=403,
                    method="GET",
                    url=self.probe.CATALOG_URL,
                    body={"message": "GitHub Models is disabled"},
                )
            ]
        )

        with tempfile.TemporaryDirectory() as temporary:
            output_dir = Path(temporary)
            report = self.probe.run_probe(
                token="secret-token",
                output_dir=output_dir,
                requester=requester,
                now=lambda: "2026-07-30T00:00:00Z",
            )

            self.assertEqual("blocked", report["status"])
            self.assertEqual(403, report["error"]["httpStatus"])
            preserved = json.loads((output_dir / "capability-report.json").read_text())
            self.assertEqual(report, preserved)
            self.assertNotIn("secret-token", (output_dir / "capability-report.json").read_text())

    def test_vision_failure_preserves_partial_success(self) -> None:
        requester = FakeRequester(
            [
                [multimodal_model()],
                completion({"probe": "github-models", "status": "ok"}),
                self.probe.ApiRequestError(
                    status=422,
                    method="POST",
                    url=self.probe.INFERENCE_URL,
                    body={"message": "image content unsupported"},
                ),
            ]
        )

        with tempfile.TemporaryDirectory() as temporary:
            report = self.probe.run_probe(
                token="secret-token",
                output_dir=Path(temporary),
                requester=requester,
                now=lambda: "2026-07-30T00:00:00Z",
            )

        self.assertEqual("failed", report["status"])
        self.assertEqual("passed", report["checks"]["structuredText"]["status"])
        self.assertEqual("failed", report["checks"]["vision"]["status"])
        self.assertEqual(422, report["error"]["httpStatus"])


if __name__ == "__main__":
    unittest.main()
