"""Acceptance-controlled effects through the installed runtime seam (#93)."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills/design-studio'
RUNTIME = SKILL / 'runtime/system-lifecycle/index.mjs'
KEYS = ('design', 'designDna', 'tokensCss', 'skillDesign', 'skillTokensCss',
        'skillIndex', 'skillDesignDna', 'documentVisualContract', 'skillDocumentVisualContract')


def text(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False) + '\n'


def digest(value):
    return hashlib.sha256(value.replace('\r\n', '\n').replace('\r', '\n').encode()).hexdigest()


def artifact(path, value):
    return {'path': path, 'content': text(value)}


def reference(record):
    return {'path': record['path'], 'sha256': digest(record['content'])}


def manifest(bundle):
    return {key: digest(bundle[key]) if bundle[key] is not None else None for key in KEYS}


def invoke(request, operation='verify'):
    return subprocess.run(['node', str(RUNTIME), operation], input=json.dumps(request),
                          text=True, encoding='utf-8', capture_output=True, timeout=15)


def intent_for(mode, effect):
    contract = json.loads((SKILL / 'design-intent-contract.json').read_text())
    intent = copy.deepcopy(next(case['result'] for case in contract['classificationExamples']
                                if case['result']['designMode'] == mode))
    intent.update(systemEffect=effect, compositionState='ready', unresolved=[])
    return intent


def bundle_for(acceptance, change=None):
    design = (ROOT / 'test/fixtures/design-authority/DESIGN.md').read_text()
    parts = design.split('---', 2)
    profile = json.loads(parts[1])
    profile['provenance'].update(runId='lifecycle', acceptedIteration=2, acceptance=reference(acceptance))
    if change:
        change(profile)
    design = '---\n' + json.dumps(profile, indent=2) + '\n---' + parts[2]
    # Use the existing public deterministic export, not a reimplemented CSS exporter.
    script = 'import {deriveDesignAuthority} from ' + json.dumps((SKILL / 'runtime/design-authority/index.mjs').as_uri()) + ';'
    script += 'let s="";for await(const c of process.stdin)s+=c; console.log(JSON.stringify(deriveDesignAuthority(s)));'
    exported = subprocess.run(['node', '--input-type=module', '-e', script], input=design,
                              text=True, capture_output=True, check=True, timeout=15)
    css = json.loads(exported.stdout)['tokensCss']
    dna = (ROOT / 'test/fixtures/design-authority/design-dna.md').read_text()
    return dict(design=design, designDna=dna, tokensCss=css, skillDesign=design,
                skillTokensCss=css, skillIndex='# Project\n\nRead [DESIGN.md](DESIGN.md).\n',
                skillDesignDna=dna, documentVisualContract=None, skillDocumentVisualContract=None)


def seal(request, status='accepted', reusable=None):
    decision = dict(schemaVersion=1, status=status, runId='lifecycle',
                    intentDigest=digest(text(request['intent']).rstrip('\n')),
                    systemEffect=request['intent']['systemEffect'],
                    before=manifest(request['before']),
                    candidate=manifest(request['candidate']) if request['candidate'] else None,
                    surfaceAcceptance=reference(request['acceptance']),
                    evidence=[reference(row) for row in request['evidence']],
                    reusableRule=reusable, retainsVisualWorld=bool(reusable))
    request['approval'] = artifact('harness-output/runs/lifecycle/finish/system-acceptance.json', decision)
    return request


def request_for(mode='create', effect='establish'):
    tree = artifact('harness-output/runs/lifecycle/finish/tree-manifest.json',
                    {'treePath': 'harness-output/runs/lifecycle/finish/selected-site',
                     'files': {'index.html': 'b' * 64}})
    mechanical = artifact('harness-output/runs/lifecycle/finish/mechanical.json',
                          {'snapshotId': 'c' * 64, 'passes': [{'kind': 'source', 'completed': True},
                           {'kind': 'browser', 'completed': True}], 'findings': []})
    rendered = artifact('harness-output/runs/lifecycle/finish/rendered.json',
                        {'kind': 'browser', 'treeManifest': reference(tree), 'status': 'verified',
                         'viewports': [{'width': 1440, 'height': 900}, {'width': 390, 'height': 844}],
                         'evidence': ['desktop.png', 'mobile.png']})
    acceptance = artifact('harness-output/runs/lifecycle/finish/acceptance.json',
                           dict(status='accepted', selectedTree=json.loads(tree['content'])['treePath'],
                                sourceIteration=2, treeManifest=tree['path'], serveValidated=True,
                                mechanicalSnapshotId='c' * 64, viewportEvidence=[rendered['path']],
                                iterationIntegrity=True))
    request = dict(schemaVersion=1, intent=intent_for(mode, effect),
                   before={key: None for key in KEYS}, candidate=bundle_for(acceptance),
                   acceptance=acceptance, evidence=[tree, mechanical, rendered])
    return seal(request)


def document_request():
    request = request_for('document-create', 'establish')
    accepted = json.loads(request['acceptance']['content'])
    accepted.pop('serveValidated')
    accepted['artifactValidated'] = True
    request['acceptance'] = artifact(request['acceptance']['path'], accepted)
    mechanical = json.loads(request['evidence'][1]['content'])
    mechanical['passes'][1]['kind'] = 'page-artifact'
    request['evidence'][1] = artifact(request['evidence'][1]['path'], mechanical)
    rendered = json.loads(request['evidence'][2]['content'])
    rendered.pop('viewports')
    rendered.update(kind='page-artifact', pageCount=2,
                    pageSizes=[{'widthMm': 210, 'heightMm': 297}] * 2,
                    evidence=['page-1.png', 'page-2.png'])
    request['evidence'][2] = artifact(request['evidence'][2]['path'], rendered)
    document = json.loads((ROOT / 'test/fixtures/document-artifact/horaxon-foundation-sprint/document-visual-contract.json').read_text())
    document['sharedTokenBindings'] = {'colour.roles.ink': 'color.ink'}
    document['colour']['roles']['ink'] = '{color.ink}'
    document_text = text(document)
    request['candidate'] = bundle_for(request['acceptance'], lambda p: p['links'].update(documentVisualContract={
        'path': 'harness-output/design-system/document-visual-contract.json', 'sha256': digest(document_text)}))
    request['candidate'].update(documentVisualContract=document_text, skillDocumentVisualContract=document_text)
    seal(request)
    return request


class SystemLifecycleTests(unittest.TestCase):
    def test_establish_requires_surface_and_system_acceptance_for_the_exact_candidate(self):
        request = request_for()
        result = invoke(request)
        self.assertEqual(0, result.returncode, result.stderr)
        receipt = json.loads(result.stdout)
        self.assertEqual('verified-transition', receipt['status'])
        self.assertEqual('establish', receipt['plannedEffect'])
        self.assertEqual('none', receipt['systemEffect'], 'Staging is not publication')
        self.assertEqual(manifest(request['before']), receipt['authorityAfter'])
        self.assertEqual(manifest(request['candidate']), receipt['derivedOutputs'])
        for mutate in [lambda r: r.pop('acceptance'),
                       lambda r: r['candidate'].update(skillIndex='# Changed\n[DESIGN.md](DESIGN.md)')]:
            changed = copy.deepcopy(request)
            mutate(changed)
            rejected = invoke(changed)
            self.assertEqual(2, rejected.returncode, rejected.stderr)


    def test_local_preserve_and_none_leave_every_global_output_unchanged(self):
        for effect in ('preserve', 'none'):
            request = request_for('polish', effect)
            request['before'] = request['candidate']
            request['candidate'] = None
            seal(request)
            result = invoke(request)
            self.assertEqual(0, result.returncode, result.stderr)
            receipt = json.loads(result.stdout)
            self.assertEqual('unchanged', receipt['status'])
            self.assertEqual(effect, receipt['systemEffect'])
            self.assertEqual(manifest(request['before']), receipt['authorityAfter'])
            self.assertEqual({}, receipt['derivedOutputs'])
            self.assertEqual([], receipt['invalidatedDownstream'])
            request['candidate'] = copy.deepcopy(request['before'])
            request['candidate']['skillIndex'] += '\nChanged global instructions.\n'
            seal(request)
            self.assertEqual(2, invoke(request).returncode)


    def test_reusable_extend_and_polish_need_separate_bound_system_approval(self):
        for mode in ('extend', 'polish'):
            request = request_for(mode, 'extend')
            request['before'] = copy.deepcopy(request['candidate'])
            request['candidate'] = bundle_for(request['acceptance'], lambda p: p['tokens'].update({
                'space.panel': {'type': 'dimension', 'role': 'layout.panel', 'css': '--panel', 'value': '1rem'}}))
            seal(request, reusable='Use the accepted panel spacing for reusable settings panels.')
            result = invoke(request)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual('extend', json.loads(result.stdout)['plannedEffect'])
            seal(request)
            self.assertEqual(2, invoke(request).returncode, 'Surface approval alone must not globalise the panel')
            seal(request, status='rejected', reusable='Rejected shared panel change')
            receipt = json.loads(invoke(request).stdout)
            self.assertEqual('rejected', receipt['status'])
            self.assertEqual('none', receipt['systemEffect'])
            self.assertEqual(manifest(request['before']), receipt['authorityAfter'])


    def test_overhaul_rejection_and_extraction_candidate_never_retire_incumbent(self):
        for mode, effect in [('overhaul', 'replace'), ('polish', 'extract')]:
            request = request_for(mode, effect)
            request['before']['design'] = '# Legacy system\nKeep the established hierarchy.\n'
            request['before']['tokensCss'] = ':root { --legacy: 1rem; }\n'
            for status in ('candidate', 'rejected'):
                seal(request, status=status)
                result = invoke(request)
                self.assertEqual(0, result.returncode, result.stderr)
                receipt = json.loads(result.stdout)
                self.assertEqual(status, receipt['status'])
                self.assertEqual('none', receipt['systemEffect'])
                self.assertEqual(manifest(request['before']), receipt['authorityAfter'])
                self.assertEqual({}, receipt['derivedOutputs'])
            seal(request)
            if effect == 'extract':
                self.assertEqual(2, invoke(request).returncode, 'Inferred values alone are not accepted authority')
                source = artifact('harness-output/runs/lifecycle/finish/source-inspection.json', {
                    'kind': 'source-inspection', 'status': 'verified',
                    'treeManifest': reference(request['evidence'][0]),
                    'candidateRevision': digest(request['candidate']['design']),
                    'files': {'src/theme.css': 'd' * 64}})
                request['evidence'].append(source)
                seal(request)
            result = invoke(request)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(effect, json.loads(result.stdout)['plannedEffect'])
            self.assertEqual(manifest(request['before']), json.loads(result.stdout)['authorityAfter'])


    def test_only_verified_published_readback_advances_authority_and_staleness(self):
        request = request_for('overhaul', 'replace')
        request['before'] = copy.deepcopy(request['candidate'])
        request['candidate'] = bundle_for(request['acceptance'], lambda p: p['tokens']['color.ink'].update(value='#222222'))
        seal(request)
        plan = json.loads(invoke(request).stdout)
        journal = dict(schemaVersion=1, status='published', transitionDigest=digest(text(plan).rstrip('\n')),
                       before=manifest(request['before']), after=manifest(request['candidate']),
                       exclusiveAccess=True, incumbentRechecked=True, stageRechecked=True, rollbackReady=True, failure=None)
        publication = artifact('harness-output/runs/lifecycle/finish/publication.json', journal)
        result = invoke(dict(request=request, observed=request['candidate'], publication=publication), 'publication')
        self.assertEqual(0, result.returncode, result.stderr)
        receipt = json.loads(result.stdout)
        self.assertEqual('published', receipt['status'])
        self.assertEqual('replace', receipt['systemEffect'])
        self.assertEqual(manifest(request['candidate']), receipt['authorityAfter'])
        self.assertEqual(digest(request['candidate']['design']), receipt['authorityRevisionAfter'])
        self.assertEqual('visual-design', receipt['invalidatedDownstream'][0]['role'])
        observed = copy.deepcopy(request['candidate'])
        observed['skillTokensCss'] += '/* stale */'
        self.assertEqual(2, invoke(dict(request=request, observed=observed, publication=publication), 'publication').returncode)
        journal.update(status='rolled-back', failure='Host write failed; restored from journal.')
        publication = artifact(publication['path'], journal)
        result = invoke(dict(request=request, observed=request['before'], publication=publication), 'publication')
        self.assertEqual(0, result.returncode, result.stderr)
        receipt = json.loads(result.stdout)
        self.assertEqual('rolled-back', receipt['status'])
        self.assertEqual('none', receipt['systemEffect'])
        self.assertEqual(manifest(request['before']), receipt['authorityAfter'])
        self.assertEqual([], receipt['invalidatedDownstream'])
        self.assertEqual(2, invoke(dict(request=request, observed=observed, publication=publication), 'publication').returncode)
        journal.update(status='recovery-incomplete')
        publication = artifact(publication['path'], journal)
        self.assertEqual(2, invoke(dict(request=request, observed=request['before'], publication=publication), 'publication').returncode)


    def test_document_acceptance_uses_page_proof_and_symbolic_shared_token_bindings(self):
        request = document_request()
        document_text = request['candidate']['documentVisualContract']
        document = json.loads(document_text)
        result = invoke(request)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(digest(document_text), json.loads(result.stdout)['derivedOutputs']['documentVisualContract'])
        # A literal duplicated value, even one matching today's token, is not a shared binding.
        document['colour']['roles']['ink'] = '#14222e'
        document_text = text(document)
        request['candidate'] = bundle_for(request['acceptance'], lambda p: p['links'].update(documentVisualContract={
            'path': 'harness-output/design-system/document-visual-contract.json', 'sha256': digest(document_text)}))
        request['candidate'].update(documentVisualContract=document_text, skillDocumentVisualContract=document_text)
        seal(request)
        self.assertEqual(2, invoke(request).returncode)


    def test_legacy_document_extraction_remains_page_scoped(self):
        request = document_request()
        request['intent'] = intent_for('document-review', 'extract')
        request['before']['design'] = '# Legacy page system\nRetain the approved page geometry.\n'
        request['before']['documentVisualContract'] = request['candidate']['documentVisualContract']
        request['evidence'].append(artifact('harness-output/runs/lifecycle/finish/inspection.json', {
            'kind': 'source-inspection', 'status': 'verified',
            'treeManifest': reference(request['evidence'][0]),
            'candidateRevision': digest(request['candidate']['design']), 'files': {'src/theme.css': 'd' * 64}}))
        seal(request)
        result = invoke(request)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual('extract', json.loads(result.stdout)['plannedEffect'])
        self.assertNotIn('workflow.yaml', request['intent']['selectedProcedures'])

    def test_polish_extension_requires_accepted_visual_authority(self):
        request = request_for('polish', 'extend')
        request['before'] = copy.deepcopy(request['candidate'])
        request['candidate'] = bundle_for(request['acceptance'], lambda p: p['tokens']['color.ink'].update(value='#222222'))
        for authority in ['none', 'selected-direction']:
            request['intent']['visualAuthority'] = authority
            seal(request, reusable='A reusable accepted ink role.')
            self.assertEqual(2, invoke(request).returncode)

    def test_duplicate_approval_keys_and_unknown_fields_fail_closed(self):
        request = request_for()
        request['approval']['content'] = request['approval']['content'].replace(
            '"status":"accepted"', '"status":"rejected","status":"accepted"')
        result = invoke(request)
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn('duplicate JSON key', result.stderr)
        seal(request)
        approval = json.loads(request['approval']['content'])
        approval['unrecognisedAuthorityOverride'] = True
        request['approval'] = artifact(request['approval']['path'], approval)
        self.assertEqual(2, invoke(request).returncode)

    def test_mutation_requires_new_authority_and_journal_cannot_overwrite_proof(self):
        request = request_for('overhaul', 'replace')
        request['before'] = copy.deepcopy(request['candidate'])
        request['candidate']['skillIndex'] += '\nCosmetic index-only change.\n'
        seal(request)
        self.assertEqual(2, invoke(request).returncode)
        request = request_for()
        verified = json.loads(invoke(request).stdout)
        journal = dict(schemaVersion=1, status='published', transitionDigest=digest(text(verified).rstrip('\n')),
                       before=manifest(request['before']), after=manifest(request['candidate']),
                       exclusiveAccess=True, incumbentRechecked=True, stageRechecked=True, rollbackReady=True, failure=None)
        for path in [request['approval']['path'], request['acceptance']['path'], request['evidence'][0]['path']]:
            publication = artifact(path, journal)
            self.assertEqual(2, invoke(dict(request=request, observed=request['candidate'], publication=publication), 'publication').returncode)

    def test_representative_effect_and_publication_fixtures(self):
        cases = json.loads((ROOT / 'test/fixtures/system-lifecycle/scenarios.json').read_text())['scenarios']
        for case in cases:
            with self.subTest(case=case['id']):
                request = request_for(case['mode'], case['effect'])
                if case['incumbent'] == 'profiled':
                    request['before'] = copy.deepcopy(request['candidate'])
                elif case['incumbent'] == 'legacy':
                    request['before']['design'] = '# Retained legacy authority\n'
                if case['effect'] == 'preserve':
                    request['candidate'] = None
                elif case['incumbent'] == 'profiled':
                    request['candidate'] = bundle_for(request['acceptance'], lambda p: p['tokens']['color.ink'].update(value='#222222'))
                if case['effect'] == 'extract':
                    request['evidence'].append(artifact('harness-output/runs/lifecycle/finish/inspection.json', {
                        'kind': 'source-inspection', 'status': 'verified',
                        'treeManifest': reference(request['evidence'][0]),
                        'candidateRevision': digest(request['candidate']['design']), 'files': {'src/theme.css': 'd' * 64}}))
                seal(request, status=case['approval'], reusable='Accepted reusable ink refinement.' if case['effect'] == 'extend' else None)
                result = invoke(request)
                self.assertEqual(0, result.returncode, result.stderr)
                receipt = json.loads(result.stdout)
                if case['publication']:
                    self.assertEqual('none', receipt['systemEffect'])
                    journal = dict(schemaVersion=1, status=case['publication'], transitionDigest=digest(text(receipt).rstrip('\n')),
                                   before=manifest(request['before']), after=manifest(request['candidate']),
                                   exclusiveAccess=True, incumbentRechecked=True, stageRechecked=True, rollbackReady=True,
                                   failure='Host restored verified incumbent after write failure.' if case['publication'] == 'rolled-back' else None)
                    observed = request['before'] if case['publication'] == 'rolled-back' else request['candidate']
                    result = invoke(dict(request=request, observed=observed,
                                         publication=artifact('harness-output/runs/lifecycle/finish/publication.json', journal)), 'publication')
                    self.assertEqual(0, result.returncode, result.stderr)
                    receipt = json.loads(result.stdout)
                    self.assertEqual(case['publication'], receipt['status'])
                self.assertEqual(case['expectedEffect'], receipt['systemEffect'])
                expected = request['candidate'] if case['publication'] == 'published' else request['before']
                self.assertEqual(manifest(expected), receipt['authorityAfter'])
                if case['publication'] != 'published':
                    self.assertEqual([], receipt['invalidatedDownstream'])

    def test_import_from_stdin_is_inert(self):
        script = 'import {verifyDesignSystemTransition} from ' + json.dumps(RUNTIME.as_uri()) + ';'
        script += 'console.log(typeof verifyDesignSystemTransition);'
        result = subprocess.run(['node', '--input-type=module', '-'], input=script,
                                text=True, capture_output=True, timeout=15)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual('function', result.stdout.strip())


    def test_evidence_paths_and_typed_approval_cannot_conflict(self):
        request = request_for()
        for change in [lambda r: r['approval'].update(path=r['acceptance']['path']),
                       lambda r: r['evidence'].append(copy.deepcopy(r['evidence'][0]))]:
            broken = copy.deepcopy(request)
            change(broken)
            if len(broken['evidence']) > 3:
                seal(broken)
            self.assertEqual(2, invoke(broken).returncode)
        pending = copy.deepcopy(request)
        seal(pending, status='candidate')
        decision = json.loads(pending['approval']['content'])
        decision['retainsVisualWorld'] = 'yes'
        pending['approval'] = artifact(pending['approval']['path'], decision)
        self.assertEqual(2, invoke(pending).returncode)

    def test_interactive_acceptance_cannot_create_or_change_document_rules(self):
        request = request_for()
        document = (ROOT / 'test/fixtures/document-artifact/horaxon-foundation-sprint/document-visual-contract.json').read_text()
        request['candidate'] = bundle_for(request['acceptance'], lambda p: p['links'].update(documentVisualContract={
            'path': 'harness-output/design-system/document-visual-contract.json', 'sha256': digest(document)}))
        request['candidate'].update(documentVisualContract=document, skillDocumentVisualContract=document)
        seal(request)
        self.assertEqual(2, invoke(request).returncode, 'Browser approval does not approve page rules')

    def test_incomplete_wrong_tree_or_primary_findings_block_system_acceptance(self):
        request = request_for()
        cases = [
            (0, lambda row: row.update(treePath='another-tree')),
            (1, lambda row: row['passes'][0].update(completed=False)),
            (1, lambda row: row.update(passes=[None])),
            (1, lambda row: row.update(findings=[None])),
            (1, lambda row: row.update(findings=[{'status': 'open', 'severity': 'primary', 'signature': 'unacknowledged'}])),
            (2, lambda row: row.update(evidence=[])),
            (2, lambda row: row['viewports'][0].update(width=0)),
            (2, lambda row: row['treeManifest'].update(sha256='e' * 64)),
        ]
        for index, change in cases:
            broken = copy.deepcopy(request)
            row = json.loads(broken['evidence'][index]['content'])
            change(row)
            broken['evidence'][index] = artifact(broken['evidence'][index]['path'], row)
            seal(broken)
            result = invoke(broken)
            self.assertEqual(2, result.returncode, result.stderr)

    def test_legacy_preserve_and_installed_copy_keep_runtime_portable(self):
        request = request_for('polish', 'preserve')
        request['before']['design'] = '# Legacy authority\nKeep these accepted rules.\n'
        request['candidate'] = None
        request['intent']['assumptions'] = ['Élan — keep the accepted visual world.']
        seal(request)
        result = invoke(request)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual('unchanged', json.loads(result.stdout)['status'])
        with tempfile.TemporaryDirectory() as directory:
            installed = Path(directory) / 'installed skill'
            shutil.copytree(SKILL, installed)
            files_before = sorted(path.relative_to(installed).as_posix() for path in installed.rglob('*'))
            result = subprocess.run(['node', str(installed / 'runtime/system-lifecycle/index.mjs'), 'verify'],
                                    input=json.dumps(request), text=True, encoding='utf-8', capture_output=True,
                                    cwd=directory, timeout=15)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(files_before, sorted(path.relative_to(installed).as_posix() for path in installed.rglob('*')))
            self.assertEqual([installed.name], [path.name for path in Path(directory).iterdir()])


if __name__ == '__main__':
    unittest.main()
