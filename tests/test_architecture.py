"""Guard the narrow dependency boundary and maintainable repository contract."""
import ast
from pathlib import Path
import re
import sys
import tomllib
import unittest

from reference.core import VERSION
from reference.demo import run

ROOT = Path(__file__).resolve().parents[1]


class ArchitectureConformance(unittest.TestCase):
    def test_core_imports_only_standard_library(self):
        tree = ast.parse((ROOT / 'reference/core.py').read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                self.assertEqual(node.level, 0, 'No hidden relative adapter imports in core')
                names = [node.module]
            else:
                continue
            for name in names:
                self.assertIn(name.split('.')[0], sys.stdlib_module_names)

    def test_version_matches_metadata(self):
        metadata = tomllib.loads((ROOT / 'pyproject.toml').read_text(encoding='utf-8'))
        self.assertEqual(metadata['project']['version'], VERSION)
        self.assertEqual(metadata['project']['dependencies'], [])

    def test_required_documents_and_local_links_exist(self):
        required = ('README.md', 'PHILOSOPHY.md', 'SPECIFICATION.md', 'ARCHITECTURE_PRINCIPLES.md',
                    'AGENTS.md', 'whats_and_hows_log.md', 'handoff.md', 'goals_and_dreams.md',
                    'ERRORS.md', 'error_history_log.md', 'CONTRIBUTING.md', 'CHANGELOG.md',
                    'SECURITY.md', 'CONFORMANCE.md', 'DEPRECATION.md', 'reference/CONTRACT.md')
        for filename in required:
            path = ROOT / filename
            self.assertTrue(path.is_file(), filename)
            content = path.read_text(encoding='utf-8')
            self.assertGreater(len(content.strip()), 100, filename)
            for target in re.findall(r'\]\(([^)]+)\)', content):
                if '://' not in target and not target.startswith('#'):
                    self.assertTrue((path.parent / target.split('#')[0]).exists(), f'{filename}: {target}')

    def test_synthetic_story_keeps_correction_after_reanalysis(self):
        result = run()
        self.assertEqual(result['revision_before_human_action'], 0)
        self.assertEqual(result['revision_after_correction_and_reanalysis'], 2)
        self.assertEqual(result['authoritative_note']['quarter_units'], '1/2')
        self.assertEqual(result['material_origin'], 'human')
        self.assertFalse(result['stale_operation']['authoritative_state_modified'])
        self.assertGreater(result['evidence_bytes'], 44)


if __name__ == '__main__':
    unittest.main()
