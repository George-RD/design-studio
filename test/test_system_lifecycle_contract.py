"""Lane-neutral lifecycle integration and receipt shape; host publication is an explicit contract."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator
import yaml

from test_system_lifecycle import invoke, request_for

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills/design-studio'
LEAF = 'references/design-authority/lifecycle.md'


class SystemLifecycleContractTests(unittest.TestCase):
    def test_rolled_back_receipt_requires_a_nonempty_failure(self):
        schema = json.loads((SKILL / 'references/design-authority/lifecycle.schema.json').read_text())
        validator = Draft202012Validator(schema)
        receipt = json.loads(invoke(request_for()).stdout)
        receipt['status'] = 'rolled-back'
        self.assertTrue(list(validator.iter_errors(receipt)), 'A rollback must retain its concrete failure')
        receipt['failure'] = ''
        self.assertTrue(list(validator.iter_errors(receipt)))
        receipt['failure'] = 'Write failed; incumbent restored and readback verified.'
        validator.validate(receipt)

    def test_runtime_viewport_policy_matches_workflow(self):
        workflow = yaml.safe_load((SKILL / 'workflow.yaml').read_text())['workflow']
        script = 'import {SYSTEM_ACCEPTANCE_VIEWPORTS} from ' + json.dumps((SKILL / 'runtime/system-lifecycle/index.mjs').as_uri()) + ';'
        script += 'console.log(JSON.stringify(SYSTEM_ACCEPTANCE_VIEWPORTS));'
        result = subprocess.run(['node', '--input-type=module', '-e', script], text=True,
                                capture_output=True, check=True, timeout=15)
        actual = json.loads(result.stdout)
        expected = [dict(width=size[0], height=size[1]) for size in workflow['defaults']['viewports'].values()]
        self.assertEqual(expected, actual)

    def test_schema_validates_runtime_receipt_and_system_acceptance(self):
        schema = json.loads((SKILL / 'references/design-authority/lifecycle.schema.json').read_text())
        Draft202012Validator.check_schema(schema)
        request = request_for()
        result = invoke(request)
        self.assertEqual(0, result.returncode, result.stderr)
        receipt = json.loads(result.stdout)
        Draft202012Validator(schema).validate(receipt)
        approval_schema = {'$ref': '#/$defs/systemAcceptance', '$defs': schema['$defs']}
        Draft202012Validator(approval_schema).validate(json.loads(request['approval']['content']))
        for field in schema['required']:
            broken = dict(receipt)
            broken.pop(field)
            self.assertTrue(list(Draft202012Validator(schema).iter_errors(broken)), field)

    def test_studio_stages_then_verifies_and_publishes_only_the_accepted_effect(self):
        workflow = yaml.safe_load((SKILL / 'workflow.yaml').read_text())['workflow']
        steps = {row['id']: row for row in workflow['steps']}
        self.assertEqual('verify_system_transition', steps['codify']['branches'][0]['next'])
        self.assertEqual([
            {'when': 'finishAcceptance.systemEffect == extend', 'next': 'codify'},
            {'when': 'default', 'next': 'verify_system_transition'},
        ], steps['complete_extension']['branches'])
        gate = steps['verify_system_transition']
        self.assertEqual(LEAF, gate['procedure'])
        self.assertEqual([
            {'when': 'designSystemTransition.status == unchanged', 'next': 'report'},
            {'when': 'designSystemTransition.status == verified-transition', 'next': 'publish_codification'},
            {'when': 'default', 'next': 'halt'},
        ], gate['branches'])
        self.assertIn('systemAcceptance', workflow['paths'])
        self.assertIn('designSystemTransition', gate['outputs'])
        actions = '\n'.join(steps['publish_codification']['actions'])
        self.assertIn('verify_design_system_publication', actions)
        self.assertIn('rollback', actions)
        self.assertIn('designSystemTransition.status == verified-transition', actions)

    def test_publication_verification_holds_lock_and_can_trigger_recovery(self):
        steps = yaml.safe_load((SKILL / 'workflow.yaml').read_text())['workflow']['steps']
        actions = next(row for row in steps if row['id'] == 'publish_codification')['actions']
        verification = next(i for i, action in enumerate(actions) if 'invoke verify_design_system_publication' in action)
        release = next(i for i, action in enumerate(actions) if 'Release exclusive access' in action)
        recovery = next(action for action in actions if action.startswith('On any write'))
        self.assertGreater(release, verification)
        self.assertIn('lifecycle verification failure', recovery)
        self.assertNotIn('mark designAuthorityPublication published', '\n'.join(actions[:verification]))

    def test_shared_lifecycle_is_disclosed_at_acceptance_not_at_activation(self):
        router = json.loads((SKILL / 'method-router.json').read_text())
        self.assertNotIn(LEAF, router['coreAuthorities'])
        self.assertIn(LEAF, [row['path'] for row in router['leaves']])
        for lane in ['references/review/polish.md', 'references/document/document.md', 'references/extend.md']:
            self.assertIn('design-authority/lifecycle.md', (SKILL / lane).read_text(), lane)
        text = (SKILL / LEAF).read_text()
        self.assertIn('without loading Studio', text)
        self.assertIn('does not perform filesystem writes', text)
        self.assertIn('system-acceptance.json', text)
        for operation in ['verify_design_system_transition', 'verify_design_system_publication']:
            self.assertIn(f'`{operation}`', (SKILL / 'runtime-contract.md').read_text())
        self.assertIn('test_system_lifecycle.py', (ROOT / '.github/workflows/runtime-portability.yml').read_text())
        self.assertIn('test_system_lifecycle_contract.py', (ROOT / '.github/workflows/design-intent-contract.yml').read_text())

    def test_staleness_is_publication_scoped_and_preserves_other_domains(self):
        composition = json.loads((SKILL / 'composition-contract.json').read_text())
        rule = next(row for row in composition['stalenessRules'] if row['trigger'] == 'accepted-visual-system-changes')
        self.assertEqual('verified-system-publication', rule['activation'])
        self.assertEqual(['confirmed product truth', 'approved offer/copy'], rule['preserves'])
        self.assertIn('system-publication', ' '.join(composition['artifactRoles'][2]['authorityEvidence']))


if __name__ == '__main__':
    unittest.main()
