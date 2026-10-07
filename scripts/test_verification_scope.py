"""Impact selection fails broad when shared CSS, coverage or test boundaries are uncertain."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from verification_scope import css_impact, changed_test_cases, frontend_impact, render_only, render_cases, DOMAINS


class ScopeTests(unittest.TestCase):
    def test_css_domains_and_shared_fallback(self):
        for before, after, expected in [
            ('.billing-records {height:1px}', '.billing-records {height:2px}', {'billing'}),
            ('', '.admin-table {height:2px}', {'admin'}),
            ('.billing-a {height:1px}', '', {'billing'}),
            ('', '.billing-a, .shared {height:2px}', None),
            ('', ':root {--color:red}', None),
            ('@media (min-width:1px) {.billing-a {color:red}}', '@media (min-width:2px) {.billing-a {color:red}}', {'billing'}),
            ('@keyframes spin {to {opacity:1}}', '@keyframes spin {to {opacity:0}}', None),
            ('', '.billing-a { content:"}"; }', None),
        ]:
            self.assertEqual(css_impact(before, after), expected, (before, after))

    def test_actual_case_lines_and_setup_fallback(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            subprocess.run(['git', 'init', '-q', temp], check=True)
            subprocess.run(['git', '-C', temp, 'config', 'user.email', 'fixture@example.com'], check=True)
            subprocess.run(['git', '-C', temp, 'config', 'user.name', 'Fixture'], check=True)
            path = 'example.spec.ts'
            old = 'const shared = 1;\ntest("first", async () => {\n    expect(1);\n});\ntest("second", async () => {\n    expect(2);\n});\n'
            (root/path).write_text(old)
            subprocess.run(['git', '-C', temp, 'add', '.'], check=True)
            subprocess.run(['git', '-C', temp, '-c', 'core.hooksPath=/dev/null', 'commit', '-qm', 'fixture'], check=True)
            def read(repo, ref, name):
                return (repo/name).read_text()
            (root/path).write_text(old.replace('expect(2)', 'expect(3)'))
            self.assertEqual(changed_test_cases(root, 'HEAD', None, path, read), {path+':5'})
            (root/path).write_text(old.replace('shared = 1', 'shared = 2'))
            self.assertEqual(changed_test_cases(root, 'HEAD', None, path, read), {path})
            (root/path).write_text(old.replace('    expect(2);\n', ''))
            self.assertEqual(changed_test_cases(root, 'HEAD', None, path, read), {path})

    def test_domain_mapping_requires_existing_coverage(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            read = lambda *_: ''
            files = ['src/pages/billing/BillingSettingsPage.tsx']
            self.assertIsNone(frontend_impact(root, 'HEAD', None, files, read))
            for path in DOMAINS['billing']['unit'] + DOMAINS['billing']['browser']:
                target = root/path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.touch()
            result = frontend_impact(root, 'HEAD', None, files, read)
            self.assertEqual(result['domains'], ['billing'])
            self.assertEqual(result['browser'], ['tests/e2e/billing.spec.ts'])
            self.assertIsNone(frontend_impact(root, 'HEAD', None, files+['src/components/ui/Button.tsx'], read))


class RenderImpactTests(unittest.TestCase):
    def test_only_render_region_can_select_render_cases(self):
        before = 'import { Button } from "../../ui";\nfunction Page() {\n    const data = useData();\n    return (\n        <Button />\n    );\n}\n'
        after = before.replace('<Button />', '<Button disabled />')
        self.assertTrue(render_only(before, after))
        self.assertTrue(render_only(before, after.replace('{ Button }', '{ Button, Spinner }')))
        self.assertFalse(render_only(before, after.replace('useData()', 'useOtherData()')))
        self.assertFalse(render_only(before, after + 'const sideEffect = run();\n'))
        self.assertFalse(render_only('not a component', 'changed'))

    def test_missing_or_renamed_case_falls_back(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.assertIsNone(render_cases(root, {'src/pages/admin/AdminPage.tsx'}, lambda *_: 'test("renamed", () => {});', None))
            self.assertIsNone(render_cases(root, {'src/unknown.tsx'}, lambda *_: '', None))
