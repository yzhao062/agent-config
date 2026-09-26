import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / 'skills/editable-figure/scripts/build_gallery.py'
SPEC = importlib.util.spec_from_file_location('build_gallery', SCRIPT)
GALLERY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GALLERY)


class GalleryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'gallery'
        self.root.mkdir()
        (self.root.parent / 'outside.png').write_bytes(b'outside')
        (self.root / 'example.png').write_bytes(b'fixture')
        self.record = dict(id='09-example', title='A < B', role='A & B',
                           copied_file='example.png', preview='example.png',
                           sha256=hashlib.sha256(b'fixture').hexdigest())
        self.manifest = dict(updated_on='2026-09-25', figures=[self.record])
        self.save()
        (self.root / 'preferences.md').write_text('## 09 Example\n\n**作者反馈：** 配色好 < 清晰\n', encoding='utf-8')

    def save(self):
        (self.root / 'sources.json').write_text(json.dumps(self.manifest), encoding='utf-8')

    def test_new_entry_and_feedback_reach_page(self):
        self.manifest['figures'].append(dict(self.record, id='10-new', title='New'))
        self.save()
        page = GALLERY.render(self.root)
        self.assertIn('2 张', page)
        self.assertIn('figure-10', page)
        self.assertIn('候选参考', page)
        self.assertIn('A &lt; B', page)
        self.assertIn('配色好 &lt; 清晰', page)
        with (self.root / 'preferences.md').open('a', encoding='utf-8') as f:
            f.write('\n## 10 New\n\n**作者反馈：** 喜欢层次\n')
        self.assertIn('你的反馈：喜欢层次', GALLERY.render(self.root))

    def test_check_detects_stale_page(self):
        command = [sys.executable, str(SCRIPT), '--gallery', str(self.root)]
        subprocess.run(command, check=True, capture_output=True)
        page = self.root / 'index.html'
        self.assertNotIn(b'\r\n', page.read_bytes())
        subprocess.run(command + ['--check'], check=True, capture_output=True)
        page.write_bytes(page.read_bytes().replace(b'\n', b'\r\n'))
        self.assertEqual(subprocess.run(command + ['--check'], capture_output=True).returncode, 1)
        subprocess.run(command, check=True, capture_output=True)
        (self.root / 'preferences.md').write_text('## 09 Example\n\n**作者反馈：** 新反馈\n', encoding='utf-8')
        result = subprocess.run(command + ['--check'], capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 1)
        self.assertIn('Stale gallery page', result.stderr)

    def test_rejects_invalid_records(self):
        for update in ({'sha256': 'bad'}, {'preview': '../outside.png'}):
            with self.subTest(update=update):
                self.manifest['figures'] = [dict(self.record, **update)]
                self.save()
                with self.assertRaisesRegex(ValueError, 'Checksum mismatch|nonlocal asset'):
                    GALLERY.render(self.root)
        self.manifest['figures'] = [self.record, self.record]
        self.save()
        with self.assertRaisesRegex(ValueError, 'unique numeric prefixes'):
            GALLERY.render(self.root)

    def test_dropped_image_requires_registration(self):
        (self.root / 'dropped.png').write_bytes(b'new')
        with self.assertRaisesRegex(ValueError, 'Add sources.json records for: dropped.png'):
            GALLERY.render(self.root)

    def test_followup_feedback_and_malformed_marker(self):
        path = self.root / 'preferences.md'
        with path.open('a', encoding='utf-8') as f:
            f.write('\n**作者反馈：** 2026-10-15: 保留旧反馈，补充层次偏好\n')
        self.assertIn('你的反馈：配色好 &lt; 清晰 2026-10-15: 保留旧反馈，补充层次偏好',
                      GALLERY.render(self.root))
        original = path.read_text(encoding='utf-8')
        path.write_text(original + '\n## 09 Duplicate\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'unique numeric headings'):
            GALLERY.render(self.root)
        path.write_text(original + '\n**作者反馈:** malformed\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'exact feedback marker'):
            GALLERY.render(self.root)

    def test_feedback_format_errors_do_not_silently_drop_text(self):
        path = self.root / 'preferences.md'
        original = path.read_text(encoding='utf-8')
        for marker in ('- **作者反馈：** text', '> **作者反馈：** text',
                       '  **作者反馈：** text', '作者反馈：text'):
            with self.subTest(marker=marker):
                path.write_text(original + '\n' + marker + '\n', encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'exact feedback marker'):
                    GALLERY.render(self.root)
        path.write_text(original + 'continued text\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'one line'):
            GALLERY.render(self.root)

    def test_filenames_are_url_encoded(self):
        name = 'example #%.png'
        (self.root / 'example.png').rename(self.root / name)
        self.record.update(copied_file=name, preview=name)
        self.save()
        page = GALLERY.render(self.root)
        self.assertIn('<img src="example%20%23%25.png"', page)
        self.assertIn('<a href="example%20%23%25.png">', page)

    def test_committed_gallery_is_current(self):
        result = subprocess.run([sys.executable, str(SCRIPT), '--check'],
                                capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
