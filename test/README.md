# Contract tests

Run from the repository root with Python 3.12+ and Node 24. Install the development-only YAML and JSON Schema validators first:

```sh
python3 -m pip install -r test/requirements.txt
python3 -m unittest discover -s test -p 'test_extend_workflow.py' -v
```

The extension suite parses the canonical workflow with PyYAML and checks conditional scope schemas with jsonschema. It does not require Ruby or a browser. These dependencies are not copied into the installed Agent Skill and are not required by supported Design Studio runs. Broader browser/research suites retain their own prerequisites.

Milestone 0 ownership tests preserve the inventory at its pinned baseline revision. Explicit post-baseline step/schema sets detect additions without rewriting historical evidence; current ownership lives in `docs/method-authority-map.json` and `skills/design-studio/workflow.yaml`.
