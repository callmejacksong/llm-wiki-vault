#!/usr/bin/env python3
"""Fetch Supadata captions and export/check one original Markdown file. Python 3.9+, stdlib only."""
import argparse
from datetime import date, datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import time
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, urlencode, urlparse
from urllib.request import Request, urlopen

API = 'https://api.supadata.ai/v1/transcript'
VIDEO_ID = re.compile(r'^[A-Za-z0-9_-]{11}$')
TRANSCRIPT_ROOT = Path('01-原始资料/02-转录')
WORKSPACE_MARKER = '.youtube-transcript-workspace.json'


class ApiError(ValueError):
    pass


def load_api_key():
    """Prefer the environment; ~/.superdata contains a single plain-text key."""
    key = os.environ.get('SUPADATA_API_KEY', '').strip()
    if key:
        return key
    path = Path.home() / '.superdata'
    try:
        key = path.read_text(encoding='utf-8').strip()
    except FileNotFoundError:
        key = ''
    except (OSError, UnicodeError):
        raise ValueError('无法读取 ~/.superdata；请检查文件权限和 UTF-8 编码。') from None
    if not key:
        raise ValueError('请配置 SUPADATA_API_KEY 环境变量或 ~/.superdata 单行 Key 文件；不要把 Key 写进 skill。')
    if '\n' in key or '\r' in key:
        raise ValueError('~/.superdata 必须只包含一行纯文本 API Key，不能包含其他配置。')
    return key


def extract_video_id(value):
    value = value.strip()
    if VIDEO_ID.fullmatch(value):
        return value
    parsed = urlparse(value)
    if parsed.scheme not in ('http', 'https') or parsed.username or parsed.password:
        raise ValueError('请提供有效的 YouTube 视频链接或 11 位视频 ID。')
    host = (parsed.hostname or '').lower()
    parts = parsed.path.strip('/').split('/')
    candidate = ''
    if host == 'youtu.be' and len(parts) == 1:
        candidate = parts[0]
    elif host in ('youtube.com', 'www.youtube.com', 'm.youtube.com', 'music.youtube.com'):
        if parsed.path.rstrip('/') == '/watch':
            values = parse_qs(parsed.query).get('v', [])
            candidate = values[0] if len(values) == 1 else ''
        elif len(parts) == 2 and parts[0] in ('embed', 'shorts', 'live'):
            candidate = parts[1]
    elif host in ('youtube-nocookie.com', 'www.youtube-nocookie.com'):
        if len(parts) == 2 and parts[0] == 'embed':
            candidate = parts[1]
    if not VIDEO_ID.fullmatch(candidate):
        raise ValueError('无法从该链接提取 YouTube 视频 ID；播放列表或频道链接不能代替视频链接。')
    return candidate


def request_json(url, api_key, timeout=30):
    request = Request(url, headers={'x-api-key': api_key, 'Accept': 'application/json'})
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status, json.load(response)
    except HTTPError as exc:
        messages = {
            401: 'Supadata API Key 无效。',
            402: 'Supadata 额度不足。',
            403: '视频访问受限或 API 请求被拒绝。',
            404: '视频、字幕或任务不存在；已完成的任务也可能已过期。',
            429: 'Supadata 限流；稍后重试，未自动重复提交请求。',
        }
        raise ApiError(messages.get(exc.code, f'Supadata HTTP {exc.code}。')) from None
    except (URLError, TimeoutError, OSError):
        raise ApiError('Supadata 网络请求失败或超时；检查网络后重试。') from None
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise ApiError('Supadata 返回了无效 JSON。') from None


def fetch(video_id, api_key, lang=None, mode='native', job_id=None,
          poll_interval=1, max_polls=40):
    if job_id is None:
        params = {'url': f'https://www.youtube.com/watch?v={video_id}',
                  'text': 'false', 'mode': mode}
        if lang:
            params['lang'] = lang
        status, data = request_json(API + '?' + urlencode(params), api_key)
        if status == 206:
            raise ApiError('未获取完整原生字幕（HTTP 206）；不会输出残缺字幕或自动改用 AI 转录。')
        if status == 200:
            return status, data
        if status != 202 or not isinstance(data, dict) or not data.get('jobId'):
            raise ApiError(f'Supadata 返回了意外响应（HTTP {status}）。')
        job_id = data['jobId']
    print(f'Supadata jobId={job_id}；正在轮询，可用 --job-id 继续。', file=sys.stderr)
    for _ in range(max_polls):
        time.sleep(poll_interval)
        status, data = request_json(API + '/' + quote(str(job_id), safe=''), api_key)
        if status != 200 or not isinstance(data, dict):
            raise ApiError(f'轮询响应无效；jobId={job_id}，请用 --job-id 恢复。')
        state = data.get('status')
        if state == 'completed':
            result = data.get('result', data)
            if not isinstance(result, dict):
                raise ApiError('已完成的任务没有有效字幕结果。')
            return status, result
        if state == 'failed':
            raise ApiError(f'字幕任务失败；jobId={job_id}。')
        if state not in ('queued', 'active'):
            raise ApiError(f'字幕任务状态未知；jobId={job_id}。')
    raise ApiError(f'轮询超时；jobId={job_id}。使用 --job-id 继续轮询，避免重新提交。')


def normalize(data):
    content = data.get('content') if isinstance(data, dict) else None
    if not isinstance(content, list) or not content:
        raise ValueError('没有非空的带时间戳源字幕；无法校验和输出有效正文。')
    cues = []
    for index, chunk in enumerate(content, 1):
        if not isinstance(chunk, dict) or not isinstance(chunk.get('text'), str) or not chunk['text'].strip():
            raise ValueError(f'第 {index} 条字幕缺少文本。')
        offset, duration = chunk.get('offset'), chunk.get('duration')
        for name, value in [('offset', offset), ('duration', duration)]:
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError(f'第 {index} 条字幕的 {name} 无效，时间单位应为毫秒。')
        start, end = round(offset), round(offset + duration)
        if end <= start:
            raise ValueError(f'第 {index} 条字幕没有有效时长。')
        if cues and start < cues[-1]['offset']:
            raise ValueError('字幕时间顺序异常；请检查源数据。')
        # Preserve caption text, speaker markers and millisecond timing.
        cues.append({'id': index, 'text': chunk['text'], 'offset': start,
                     'duration': end - start, 'lang': chunk.get('lang', data.get('lang'))})
    return cues


def timestamp(ms):
    seconds, millis = divmod(ms, 1000)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return f'{hours:02}:{minutes:02}:{seconds:02},{millis:03}'


def srt(cues):
    blocks = []
    for cue in cues:
        # Blank lines delimit SRT blocks. Normalize only line endings/blank separators.
        lines = cue['text'].replace('\r\n', '\n').replace('\r', '\n').split('\n')
        text = '\n'.join(line for line in lines if line.strip())
        blocks.append(f"{cue['id']}\n{timestamp(cue['offset'])} --> "
                      f"{timestamp(cue['offset'] + cue['duration'])}\n{text}")
    return '\n\n'.join(blocks) + '\n\n'


def write_new(path, text):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(text)


def json_text(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def save_source(root, video_id, data, status, mode='native'):
    cues = normalize(data)
    out = root / video_id
    out.mkdir(parents=True, exist_ok=True)
    files = ['source.json', 'segments.json', 'original.srt']
    if any((out / name).exists() for name in files):
        raise ValueError(f'{out} 已有源字幕；请复用，或选择新的 --output 目录。')
    write_new(out / 'source.json', json_text({
        'video_id': video_id, 'url': f'https://www.youtube.com/watch?v={video_id}',
        'fetched_at': datetime.now(timezone.utc).isoformat(),
        'http_status': status, 'mode': mode, 'response': data,
    }))
    write_new(out / 'segments.json', json_text({'lang': data.get('lang'), 'segments': cues}))
    return out


def render_translation(cues, translations):
    segments = translations.get('segments') if isinstance(translations, dict) else None
    if not isinstance(segments, list) or len(segments) != len(cues):
        raise ValueError('翻译条数与原文不一致；必须完整覆盖所有字幕。')
    translated = []
    for cue, item in zip(cues, segments):
        if not isinstance(item, dict) or type(item.get('id')) is not int or item['id'] != cue['id']:
            raise ValueError('翻译 ID 缺失、重复或顺序错误。')
        if not isinstance(item.get('text'), str) or not item['text'].strip():
            raise ValueError(f"第 {cue['id']} 条译文为空。")
        translated.append(dict(cue, text=item['text']))
    return srt(translated)


def load_json(path):
    with Path(path).open(encoding='utf-8') as stream:
        return json.load(stream)


def merge_translations(paths):
    segments = []
    for path in paths:
        data = load_json(path)
        if not isinstance(data, dict) or not isinstance(data.get('segments'), list):
            raise ValueError(f'{path} 需要包含 segments 数组。')
        segments.extend(data['segments'])
    return {'segments': segments}


def source_cues(directory):
    return normalize(load_json(directory / 'source.json')['response'])


def paragraphs(texts, chinese=False):
    """Join caption fragments into readable paragraphs, preserving their content."""
    result, current = [], ''
    for value in texts:
        value = ' '.join(value.split())
        separator = ' '
        if chinese and current:
            separator = ' ' if re.search(r'[A-Za-z0-9]$', current) or re.match(r'[A-Za-z0-9]', value) else ''
        current += (separator if current else '') + value
        if len(current) >= (180 if chinese else 360) and re.search(r'[.!?。！？]["”\']?$', current):
            result.append(current)
            current = ''
    if current:
        result.append(current)
    return '\n\n'.join(result)


def display_width(value):
    return sum(2 if unicodedata.east_asian_width(char) in ('W', 'F') else 1 for char in value)


def wrap_markdown(text, width=88):
    """Wrap CJK by display width, keeping Latin words/URLs intact and visible line breaks."""
    tokens = re.findall(r"https?://\S+|[A-Za-z0-9]+(?:[._'’/-][A-Za-z0-9]+)*|\s+|[^\s]", text)
    lines, pending = [], []
    for token in tokens:
        if token.isspace():
            token = ' '
        if pending and display_width(''.join(pending) + token) > width:
            clause_breaks = [i + 1 for i, part in enumerate(pending) if part in '，。；！？、,.!?;:']
            word_breaks = [i + 1 for i, part in enumerate(pending) if part == ' ']
            split = (clause_breaks or word_breaks or [len(pending)])[-1]
            if not clause_breaks and not word_breaks and token in '，。；！？、,.!?;:' and len(pending) > 1:
                split = len(pending) - 1
            lines.append(''.join(pending[:split]).rstrip())
            pending = pending[split:]
            while pending and pending[0] == ' ':
                pending.pop(0)
            if pending and display_width(''.join(pending) + token) > width:
                lines.append(''.join(pending).rstrip())
                pending = []
        if not pending and token == ' ':
            continue
        pending.append(token)
    if ''.join(pending).strip():
        lines.append(''.join(pending).rstrip())
    return '  \n'.join(lines)


def markdown_body(body, summary=False):
    blocks = []
    for block in re.split(r'\n\s*\n', body.strip()):
        lines = block.splitlines()
        if summary and len(lines[0]) < 65 and (len(lines) > 1 or not re.search(r'[。！？.!?:：]', lines[0])):
            blocks.append('### ' + lines[0])
            if len(lines) > 1:
                blocks.append(wrap_markdown(' '.join(lines[1:])))
        else:
            blocks.append(wrap_markdown(' '.join(lines)))
    # Speaker markers are text, not Markdown blockquotes.
    return re.sub(r'(?m)^>>', r'\\>\\>', '\n\n'.join(blocks))


def chapter_list(metadata):
    chapters = metadata.get('chapters')
    if chapters is None:
        chapters = []
        for line in metadata['description'].splitlines():
            match = re.match(r'^\s*((?:\d+:)?\d{1,2}:\d{2})\s+(?:[|·–—-]\s*)?(.+?)\s*$', line)
            if match:
                parts = [int(part) for part in match[1].split(':')]
                seconds = 0
                for part in parts:
                    seconds = seconds * 60 + part
                chapters.append({'offset': seconds * 1000, 'title': match[2]})
    if not isinstance(chapters, list):
        raise ValueError('chapters 必须为数组，offset 使用毫秒。')
    previous = -1
    for chapter in chapters:
        if not isinstance(chapter, dict):
            raise ValueError('章节必须包含 offset 和 title。')
        offset = chapter.get('offset')
        if type(offset) is not int or offset < 0 or offset <= previous:
            raise ValueError('章节 offset 必须为递增的非负整数毫秒。')
        for field in ['title', 'title_zh']:
            value = chapter.get(field)
            if field == 'title_zh' and value is None:
                continue
            if not isinstance(value, str) or not value.strip() or '\n' in value or '\r' in value:
                raise ValueError(f'章节 {field} 必须为非空单行文本。')
        previous = offset
    return chapters


def transcript_body(cues, chapters, chinese=False):
    blocks, index = [], 0
    for cue in cues:
        while index < len(chapters) and chapters[index]['offset'] <= cue['offset']:
            chapter = chapters[index]
            heading = chapter.get('title_zh') if chinese else None
            blocks.append('### ' + (heading or chapter['title']))
            index += 1
        seconds = cue['offset'] // 1000
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        stamp = f'{hours}:{minutes:02}:{seconds:02}' if hours else f'{minutes}:{seconds:02}'
        text = ' '.join(cue['text'].split())
        blocks.append(f'**{stamp}** · {text}')
    return '\n\n'.join(blocks)


def markdown_document(metadata, section, body):
    for field in ['title', 'channel', 'url', 'description']:
        if not isinstance(metadata.get(field), str):
            raise ValueError(f'视频元数据缺少字符串字段 {field}。未知字段请显式填“未知”。')
    for field in ['title', 'channel', 'url']:
        if '\n' in metadata[field] or '\r' in metadata[field] or not metadata[field].strip():
            raise ValueError(f'视频元数据的 {field} 必须为非空单行文本。')
    description = metadata['description'].strip()
    if not body.strip():
        raise ValueError(f'{section} 正文为空。')
    published = metadata.get('published')
    if published in ('', '未知'):
        published = None
    created = metadata.get('created', date.today().isoformat())
    for field, value in [('published', published), ('created', created)]:
        if field == 'published' and value is None:
            continue
        if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
            raise ValueError(f'{field} 必须为 YYYY-MM-DD 日期。')
        date.fromisoformat(value)
    scalar = lambda value: json.dumps(value, ensure_ascii=False)
    url = f"https://www.youtube.com/watch?v={extract_video_id(metadata['url'])}"
    author = ('author: []' if metadata['channel'] == '未知' else
              'author:\n  - ' + scalar('[[' + metadata['channel'] + ']]'))
    header = (f"---\ntitle: {scalar(metadata['title'])}\nsource: {scalar(url)}\n"
              f"{author}\npublished: {published or 'null'}\ncreated: {created}\n"
              f"description: {scalar(description)}\ntags:\n  - \"clippings\"\n---\n")
    description = '\n'.join(line.rstrip() + '  ' if line.strip() else ''
                            for line in description.splitlines()).rstrip()
    return f'{header}![]({url})\n\n{description}\n\n## {section}\n\n{body.strip()}\n'


def original_document(directory, metadata):
    cues = source_cues(directory)
    source = load_json(directory / 'source.json')
    if extract_video_id(metadata.get('url', '')) != source['video_id']:
        raise ValueError('元数据 URL 与字幕视频 ID 不一致。')
    metadata = dict(metadata)
    metadata.setdefault('created', datetime.fromisoformat(source['fetched_at']).astimezone().date().isoformat())
    chapters = chapter_list(metadata)
    return markdown_document(metadata, 'Transcript', transcript_body(cues, chapters))


def title_folder(title):
    if not isinstance(title, str):
        raise ValueError('简短视频标题必须为字符串。')
    name = re.sub(r'[^\w]+', '_', unicodedata.normalize('NFKC', title)).strip('_')
    name = '_'.join(part for part in name.split('_') if part)[:80].rstrip('_')
    if not name or name == '未知':
        raise ValueError('请提供可用于文件名的简短视频标题。')
    return name


def delivery_file(metadata, short_title=None, root=None):
    title = short_title or metadata.get('short_title')
    if not title:
        title = ' '.join(metadata.get('title', '').split()[:8])
    if root is None:
        root = Path('01-原始资料/02-转录')
    return root / (title_folder(title) + '.md')


def cleanup_workspace(directory, destination):
    """Only remove a marked, dedicated workspace after delivery verification."""
    work = directory.absolute()
    root = work.parent
    marker = root / WORKSPACE_MARKER
    if (work.is_symlink() or root.is_symlink() or marker.is_symlink()
            or root.parent.resolve() != TRANSCRIPT_ROOT.resolve()
            or not root.name.startswith('youtube-transcript-')
            or not VIDEO_ID.fullmatch(work.name) or not marker.is_file()):
        raise ValueError('拒绝清理：不是带任务标记的专用转录工作目录。')
    if load_json(marker) != {'video_id': work.name}:
        raise ValueError('拒绝清理：任务标记与视频不匹配。')
    if destination.resolve() == root.resolve() or root.resolve() in destination.resolve().parents:
        raise ValueError('拒绝清理：交付文件位于工作目录内。')
    if {p.name for p in root.iterdir()} != {work.name, WORKSPACE_MARKER}:
        raise ValueError('拒绝清理：工作目录含其他任务文件。')
    allowed = {'source.json', 'segments.json', 'metadata.json', 'summary-body.txt'}
    for path in work.iterdir():
        if (path.is_symlink() or not path.is_file()
                or (path.name not in allowed and not re.fullmatch(r'translation-[\w-]+\.json', path.name))):
            raise ValueError(f'拒绝清理：含未识别的工作文件 {path.name}。')
    shutil.rmtree(root)
    print(f'已清理工作目录：{root}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    identity = sub.add_parser('id', help='提取/校验视频 ID，不调用 API')
    identity.add_argument('url')
    get = sub.add_parser('fetch', help='获取字幕，优先读取 SUPADATA_API_KEY，否则读取 ~/.superdata')
    get.add_argument('url')
    get.add_argument('--output', type=Path, help='自定义工作数据根目录；默认在 01-原始资料/02-转录 新建 youtube-transcript-*')
    get.add_argument('--lang', help='明确指定源字幕语言时才设置；默认不强制英文')
    get.add_argument('--mode', choices=['native', 'auto', 'generate'], default='native')
    get.add_argument('--job-id', help='恢复已有任务，不重新提交')
    get.add_argument('--input-json', type=Path, help='从已保存的 API 响应导入，离线且无需 Key')
    read = sub.add_parser('read', help='分段读取源字幕，每次最多指定条数')
    read.add_argument('directory', type=Path)
    read.add_argument('--start', type=int, default=1, help='起始 ID，含此条')
    read.add_argument('--count', type=int, default=80)
    render = sub.add_parser('render', help='输出单份 Obsidian 剪藏格式的原始字幕 Markdown')
    render.add_argument('directory', type=Path)
    render.add_argument('--metadata', type=Path, required=True, help='title/channel/url/description 字段的 JSON')
    render.add_argument('--short-title', help='概括视频主题的简短标题，空格/标点自动转为下划线')
    render.add_argument('--output', type=Path, help='输出目录，默认 01-原始资料/02-转录；直接保存短标题.md')
    check = sub.add_parser('check', help='校验原始字幕 Markdown、元数据、章节和时间戳')
    check.add_argument('directory', type=Path)
    check.add_argument('--metadata', type=Path, required=True)
    check.add_argument('--short-title')
    check.add_argument('--output', type=Path)
    check.add_argument('--cleanup', action='store_true', help='校验通过后清理本次专用工作目录')
    args = parser.parse_args()
    try:
        if args.command == 'id':
            print(extract_video_id(args.url))
        elif args.command == 'fetch':
            video_id = extract_video_id(args.url)
            # Check before making a potentially billable request.
            out = args.output / video_id if args.output else None
            if out and any((out / name).exists() for name in ['source.json', 'segments.json', 'original.srt']):
                raise ValueError(f'{out} 已有源字幕；请复用，或指定新目录。')
            if args.input_json:
                if args.job_id:
                    raise ValueError('--input-json 与 --job-id 不能同时使用。')
                status, data = 200, load_json(args.input_json)
            else:
                key = load_api_key()
                status, data = fetch(video_id, key, args.lang, args.mode, args.job_id)
            normalize(data)  # Do not create a workspace for an unusable response.
            if args.output is None:
                TRANSCRIPT_ROOT.mkdir(parents=True, exist_ok=True)
                work_root = Path(tempfile.mkdtemp(prefix='youtube-transcript-', dir=TRANSCRIPT_ROOT))
                write_new(work_root / WORKSPACE_MARKER, json_text({'video_id': video_id}))
            else:
                work_root = args.output
            out = save_source(work_root, video_id, data, status, args.mode)
            print(json_text({'directory': str(out.resolve()), 'lang': data.get('lang'),
                             'segments': len(data['content']), 'source': str((out / 'source.json').resolve())}))
        elif args.command == 'read':
            cues = source_cues(args.directory)
            if args.start < 1 or args.count < 1 or args.start > len(cues):
                raise ValueError('--start/--count 超出有效范围。')
            batch = cues[args.start - 1:args.start - 1 + args.count]
            next_id = batch[-1]['id'] + 1 if batch[-1]['id'] < len(cues) else None
            print(json_text({'total': len(cues), 'next_id': next_id, 'segments': batch}))
        else:
            metadata = load_json(args.metadata)
            original = original_document(args.directory, metadata)
            destination = delivery_file(metadata, args.short_title, args.output)
            if args.command == 'render':
                if destination.exists() or destination.is_symlink():
                    raise ValueError('同名 Markdown 已存在；请指定带版本号或视频 ID 的 --short-title，不覆盖已有资料。')
                destination.parent.mkdir(parents=True, exist_ok=True)
                write_new(destination, original)
                print(str(destination.resolve()))
            else:
                if destination.read_text(encoding='utf-8') != original:
                    raise ValueError(f'{destination.name} 与原始字幕及元数据不一致。')
                print(f'通过校验：{len(source_cues(args.directory))} 条原始字幕、章节、时间戳和元数据一致，单份 Markdown 齐全。未核验视频音轨与字幕识别准确性。')
                if args.cleanup:
                    cleanup_workspace(args.directory, destination)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f'错误：{exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
