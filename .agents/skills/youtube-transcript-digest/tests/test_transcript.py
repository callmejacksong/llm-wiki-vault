import importlib.util
import json
import os
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'transcript.py'
spec = importlib.util.spec_from_file_location('transcript', SCRIPT)
m = importlib.util.module_from_spec(spec)
if SCRIPT.exists():
    spec.loader.exec_module(m)

RAW = {'lang': 'en', 'availableLangs': ['en'], 'content': [
    {'text': '>> Sam Altman in San Francisco.', 'offset': 1234, 'duration': 2766},
    {'text': 'Growth was 20%, not 200%.', 'offset': 4000, 'duration': 3000},
]}


class TranscriptTests(unittest.TestCase):
    def test_key_environment_takes_priority_over_file(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(m.Path, 'home', return_value=Path(tmp)), patch.dict(os.environ, {'SUPADATA_API_KEY': ' env-test-key '}):
            (Path(tmp) / '.superdata').write_text('file-test-key\n')
            self.assertEqual(m.load_api_key(), 'env-test-key')

    def test_key_file_fallback_when_environment_missing_or_blank(self):
        for env in [{}, {'SUPADATA_API_KEY': '  '}]:
            with tempfile.TemporaryDirectory() as tmp, patch.object(m.Path, 'home', return_value=Path(tmp)), patch.dict(os.environ, env, clear=True):
                (Path(tmp) / '.superdata').write_text(' file-test-key\n')
                self.assertEqual(m.load_api_key(), 'file-test-key')

    def test_missing_empty_and_multiline_key_are_rejected(self):
        for content in [None, '', ' \n', 'first-secret\nsecond-secret']:
            with tempfile.TemporaryDirectory() as tmp, patch.object(m.Path, 'home', return_value=Path(tmp)), patch.dict(os.environ, {}, clear=True):
                if content is not None:
                    (Path(tmp) / '.superdata').write_text(content)
                with self.assertRaises(ValueError) as error:
                    m.load_api_key()
                self.assertNotIn('first-secret', str(error.exception))

    def test_key_file_read_error_does_not_expose_contents(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(m.Path, 'read_text', side_effect=PermissionError('private details')):
            with self.assertRaisesRegex(ValueError, '读取') as error:
                m.load_api_key()
            self.assertNotIn('private details', str(error.exception))

    def test_script_exists(self):
        self.assertTrue(SCRIPT.exists(), 'Python transcript helper is missing')

    def test_video_url_variants(self):
        for url in [
            'https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=abc&t=42',
            'https://youtu.be/dQw4w9WgXcQ?si=abc',
            'https://m.youtube.com/shorts/dQw4w9WgXcQ',
            'https://www.youtube.com/embed/dQw4w9WgXcQ',
            'https://youtube.com/live/dQw4w9WgXcQ',
            'https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ',
            'dQw4w9WgXcQ',
        ]:
            with self.subTest(url=url):
                self.assertEqual(m.extract_video_id(url), 'dQw4w9WgXcQ')

    def test_rejects_non_video_or_spoofed_urls(self):
        for url in ['https://youtube.com.evil.test/watch?v=dQw4w9WgXcQ',
                    'https://evil.test/embed/dQw4w9WgXcQ',
                    'https://youtube.com/playlist?list=abc',
                    'https://youtube.com/watch?v=bad',
                    'file:///watch?v=dQw4w9WgXcQ']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                m.extract_video_id(url)

    def test_export_preserves_original_text_and_milliseconds(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = m.save_source(Path(tmp), 'dQw4w9WgXcQ', RAW, 200)
            self.assertFalse((out / 'original.srt').exists())
            self.assertEqual(json.loads((out / 'source.json').read_text())['response'], RAW)
            cues = json.loads((out / 'segments.json').read_text())['segments']
            self.assertEqual([x['id'] for x in cues], [1, 2])
            self.assertEqual(cues[1]['text'], RAW['content'][1]['text'])
            self.assertEqual(cues[0]['offset'], 1234)
            self.assertEqual(cues[0]['text'], '>> Sam Altman in San Francisco.')

    def test_translation_requires_every_id_in_order(self):
        source = m.normalize(RAW)
        good = {'segments': [{'id': 1, 'text': 'Sam Altman 在 San Francisco。'},
                             {'id': 2, 'text': '增长是 20%，不是 200%。'}]}
        srt = m.render_translation(source, good)
        self.assertIn('00:00:01,234 --> 00:00:04,000', srt)
        self.assertIn('增长是 20%，不是 200%。', srt)
        for bad in [{'segments': good['segments'][:1]},
                    {'segments': list(reversed(good['segments']))},
                    {'segments': [{'id': 1, 'text': ''}, good['segments'][1]]}]:
            with self.assertRaises(ValueError):
                m.render_translation(source, bad)

    def test_rejects_empty_plain_and_invalid_timing(self):
        for bad in [{'content': []}, {'content': 'untimed plain text'},
                    {'content': [{'text': 'x', 'offset': -1, 'duration': 2}]},
                    {'content': [{'text': 'x', 'offset': 1}]},
                    {'content': [{'text': 'x', 'offset': 1, 'duration': 0}]},
                    {'content': [{'text': '', 'offset': 1, 'duration': 2}]}]:
            with self.assertRaises(ValueError):
                m.normalize(bad)

    def test_native_request_omits_language_by_default(self):
        with patch.object(m, 'request_json', return_value=(200, RAW)) as req:
            status, response = m.fetch('dQw4w9WgXcQ', 'dummy')
        self.assertEqual(response, RAW)
        from urllib.parse import parse_qs, urlparse
        params = parse_qs(urlparse(req.call_args.args[0]).query)
        self.assertEqual(params['mode'], ['native'])
        self.assertEqual(params['text'], ['false'])
        self.assertEqual(params['url'], ['https://www.youtube.com/watch?v=dQw4w9WgXcQ'])
        self.assertNotIn('lang', params)

    def test_job_polling_supports_flat_and_nested_result(self):
        for final in [dict(RAW, status='completed'), {'status': 'completed', 'result': RAW}]:
            with patch.object(m, 'request_json', side_effect=[
                (202, {'jobId': 'job-1'}), (200, {'status': 'active'}), (200, final)
            ]), patch.object(m.time, 'sleep'):
                status, data = m.fetch('dQw4w9WgXcQ', 'dummy', poll_interval=0)
            self.assertEqual(data['content'], RAW['content'])

    def test_partial_response_is_not_accepted(self):
        with patch.object(m, 'request_json', return_value=(206, RAW)):
            with self.assertRaises(m.ApiError):
                m.fetch('dQw4w9WgXcQ', 'dummy')

    def test_no_transcript_response_does_not_create_deliverable(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                m.save_source(Path(tmp), 'dQw4w9WgXcQ', {'content': []}, 200)
            self.assertEqual(list(Path(tmp).glob('**/original.srt')), [])

    def test_job_resume_never_submits_again(self):
        with patch.object(m, 'request_json', return_value=(200, dict(RAW, status='completed'))) as req, patch.object(m.time, 'sleep'):
            m.fetch('dQw4w9WgXcQ', 'dummy', job_id='saved-job')
        self.assertEqual(req.call_args.args[0], m.API + '/saved-job')
        self.assertEqual(req.call_count, 1)

    def test_job_timeout_exposes_resumable_id(self):
        with patch.object(m, 'request_json', return_value=(200, {'status': 'active'})), patch.object(m.time, 'sleep'):
            with self.assertRaisesRegex(m.ApiError, 'saved-job'):
                m.fetch('dQw4w9WgXcQ', 'dummy', job_id='saved-job', max_polls=2)

    def test_offline_cli_single_original_file_and_cleanup(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture = root / 'fixture.json'
            fixture.write_text(json.dumps(RAW))

            def run(*args):
                return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                                      capture_output=True, text=True, cwd=root,
                                      env=dict(os.environ, TMPDIR=str(root)))

            result = run('fetch', 'https://youtu.be/dQw4w9WgXcQ?si=ignore',
                         '--input-json', fixture)
            self.assertEqual(result.returncode, 0, result.stderr)
            out = Path(json.loads(result.stdout)['directory'])
            self.assertEqual(out.parent.parent, (root / '01-原始资料/02-转录').resolve())
            self.assertTrue(out.parent.name.startswith('youtube-transcript-'))
            self.assertFalse(list(root.rglob('99-工作文件')))
            read = run('read', out, '--start', 1, '--count', 1)
            self.assertEqual(json.loads(read.stdout)['next_id'], 2)
            read = run('read', out, '--start', 2, '--count', 1)
            self.assertIsNone(json.loads(read.stdout)['next_id'])
            metadata = out / 'metadata.json'
            metadata.write_text(json.dumps({'title': 'Test Video', 'channel': 'Test Channel',
                'url': 'https://youtube.com/watch?v=dQw4w9WgXcQ',
                'description': 'Example description.\n00:00 Intro\n00:04 Ideas',
                'published': '2026-03-11', 'created': '2026-10-15',
                'chapters': [{'offset': 0, 'title': 'Intro', 'title_zh': '开场'},
                             {'offset': 4000, 'title': 'Ideas', 'title_zh': '观点'}]}))
            document_args = ['--metadata', metadata, '--short-title', 'Test Video']
            output_root = root / '01-原始资料/02-转录'
            delivery = output_root / 'Test_Video.md'
            rendered = run('render', out, *document_args)
            self.assertEqual(rendered.returncode, 0, rendered.stderr)
            for section in ['Transcript']:
                text = delivery.read_text()
                self.assertTrue(text.startswith('---\ntitle: "Test Video"\n'))
                self.assertIn('  - "[[Test Channel]]"', text)
                self.assertIn('published: 2026-03-11\ncreated: 2026-10-15', text)
                self.assertIn('![](https://www.youtube.com/watch?v=dQw4w9WgXcQ)', text)
                self.assertIn('\n## ' + section + '\n', text)
                self.assertIn('00:00 Intro', text)
                self.assertNotIn('-->', text)
            original = delivery.read_text()
            self.assertIn('### Intro\n\n**0:01** · >> Sam Altman in San Francisco.', original)
            self.assertIn('### Ideas\n\n**0:04** · Growth was 20%, not 200%.', original)
            self.assertEqual({p.name for p in output_root.iterdir()}, {out.parent.name, 'Test_Video.md'})
            checked = run('check', out, *document_args)
            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertTrue(out.exists(), '普通校验不清理')
            self.assertEqual(run('render', out, *document_args).returncode, 1)
            self.assertEqual(delivery.read_text(), original, '重名不得覆盖')
            custom = root / 'custom'
            self.assertEqual(run('render', out, *document_args, '--output', custom).returncode, 0)
            self.assertEqual({p.name for p in custom.iterdir()}, {'Test_Video.md'})
            self.assertEqual(run('check', out, *document_args, '--output', custom).returncode, 0)
            self.assertEqual(run('fetch', 'dQw4w9WgXcQ', '--input-json', fixture,
                                 '--output', out.parent).returncode, 1)
            delivery.write_text('corrupted')
            self.assertEqual(run('check', out, *document_args).returncode, 1)
            self.assertEqual(run('check', out, *document_args, '--cleanup').returncode, 1)
            self.assertTrue(out.exists(), '校验失败时必须保留恢复数据')
            delivery.write_text(original)
            extra = out / 'other-task.txt'
            extra.write_text('不可删除')
            self.assertEqual(run('check', out, *document_args, '--cleanup').returncode, 1)
            self.assertTrue(extra.exists())
            extra.unlink()
            self.assertFalse((out / 'original.md').exists())
            cleaned = run('check', out, *document_args, '--cleanup')
            self.assertEqual(cleaned.returncode, 0, cleaned.stderr)
            self.assertFalse(out.parent.exists())
            self.assertEqual({p.name for p in output_root.iterdir()}, {'Test_Video.md'})
            self.assertEqual(delivery.read_text(), original)

    def test_cleanup_rejects_unmarked_historical_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(m, 'TRANSCRIPT_ROOT', Path(tmp)):
                root = Path(tmp) / 'youtube-transcript-history'
                out = m.save_source(root, 'dQw4w9WgXcQ', RAW, 200)
                with self.assertRaises(ValueError):
                    m.cleanup_workspace(out, Path(tmp) / 'delivery')
                self.assertTrue((out / 'source.json').exists())

    def test_cleanup_rejects_nested_delivery_and_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(m, 'TRANSCRIPT_ROOT', Path(tmp)):
                root = Path(tmp) / 'youtube-transcript-test'
                out = m.save_source(root, 'dQw4w9WgXcQ', RAW, 200)
                (root / m.WORKSPACE_MARKER).write_text(json.dumps({'video_id': out.name}))
                with self.assertRaises(ValueError):
                    m.cleanup_workspace(out, out / 'delivery')
                external = Path(tmp) / 'external.json'
                external.write_text('保留')
                link = out / 'translation-001.json'
                link.symlink_to(external)
                with self.assertRaises(ValueError):
                    m.cleanup_workspace(out, Path(tmp) / 'delivery')
                self.assertTrue(out.exists())
                self.assertEqual(external.read_text(), '保留')

    def test_description_chapters_and_hour_timestamps(self):
        raw = {'content': [{'text': 'Start', 'offset': 0, 'duration': 1000},
                           {'text': 'Later', 'offset': 3601234, 'duration': 1000}]}
        with tempfile.TemporaryDirectory() as tmp:
            work = m.save_source(Path(tmp), 'dQw4w9WgXcQ', raw, 200)
            metadata = {'title': 'A "quoted": title', 'channel': '未知',
                        'url': 'https://youtu.be/dQw4w9WgXcQ',
                        'description': '00:00 | Intro\n1:00:01 - Later'}
            original = m.original_document(work, metadata)
            self.assertIn('published: null', original)
            self.assertIn('author: []', original)
            self.assertIn('### Later\n\n**1:00:01** · Later', original)
            self.assertEqual(m.delivery_file(metadata),
                             Path('01-原始资料/02-转录') / 'A_quoted_title.md')

    def test_title_folder_is_safe_and_keeps_chinese(self):
        self.assertEqual(m.title_folder('Notion + Codex: AI Second Brain'), 'Notion_Codex_AI_Second_Brain')
        self.assertEqual(m.title_folder('../../中文 标题 / Codex'), '中文_标题_Codex')
        with self.assertRaises(ValueError):
            m.title_folder('...///')

    def test_markdown_wrap_preserves_words_and_limits_display_width(self):
        text = '这是一段用于检验阅读宽度的中文。' * 30 + ' Notion Quick Note preserves complete words. ' * 15
        result = m.wrap_markdown(text)
        self.assertEqual(''.join(result.split()), ''.join(text.split()))
        for line in result.splitlines():
            self.assertLessEqual(m.display_width(line.rstrip()), 88)
        self.assertNotIn('preser\n', result)
        self.assertIn('  \n', result)

    def test_markdown_wrap_prefers_clause_breaks(self):
        text = '这是前半句，' + '这是后半句的文字' * 8 + '。接下来是另一句话。'
        result = m.wrap_markdown(text)
        self.assertEqual(result.splitlines()[0].rstrip(), '这是前半句，')
        self.assertFalse(any(line.startswith(('。', '，', '；')) for line in result.splitlines()))


if __name__ == '__main__':
    unittest.main()
