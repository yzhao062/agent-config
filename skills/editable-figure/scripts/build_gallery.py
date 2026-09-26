"""Build or check the portable gallery from its source records and feedback."""

import argparse
import hashlib
import html
import json
from pathlib import Path
import re
from urllib.parse import quote


GALLERY = Path(__file__).resolve().parents[1] / 'references' / 'gallery'
REDIRECT = '''<!doctype html>
<html lang="zh-CN"><meta charset="utf-8">
<meta http-equiv="refresh" content="0; url=index.html">
<title>Overview figure 审美图库</title>
<p><a href="index.html">打开最新图库</a></p></html>
'''
STYLE = '''
*{box-sizing:border-box}body{margin:0;background:#f5f6f5;color:#22312a;font:16px/1.55 system-ui,sans-serif}header,main,footer{max-width:1400px;margin:auto;padding:24px}h1{margin:8px 0;font-size:30px}header p{margin:8px 0;color:#526159}nav{display:flex;gap:12px;flex-wrap:wrap}a{color:#28644b}main{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px;padding-top:0}article{padding:20px;background:white;border:1px solid #dce3de;border-radius:12px}h2{font-size:18px;margin:0 0 16px}h2 span{display:inline-block;padding:3px 8px;background:#deeee4;border-radius:6px;margin-right:7px}.image{display:flex;align-items:center;justify-content:center;min-height:220px;height:360px;background:white}.image img{max-width:100%;max-height:100%;object-fit:contain}p{margin:14px 0 0}.status,details{font-size:14px;color:#617268}details{margin-top:12px}.source{overflow-wrap:anywhere;font-family:monospace;font-size:12px}footer{font-size:13px;color:#617268}@media(max-width:850px){main{grid-template-columns:1fr}.image{height:auto;min-height:0}h1{font-size:25px}}
'''


def render(gallery):
    manifest = json.loads((gallery / 'sources.json').read_text(encoding='utf-8'))
    records = manifest['figures']
    feedback = {}
    headings = set()
    current = None
    after_feedback = False
    for line in (gallery / 'preferences.md').read_text(encoding='utf-8').splitlines():
        if after_feedback and line.strip():
            raise ValueError('Keep each feedback paragraph on one line, followed by a blank line')
        after_feedback = False
        if line.startswith('## '):
            match = re.match(r'## (\d+) ', line)
            current = match[1] if match else None
            if current is not None:
                if current in headings:
                    raise ValueError('Feedback needs unique numeric headings')
                headings.add(current)
        if '作者反馈' in line and not line.startswith('**作者反馈：** '):
            raise ValueError('Use the exact feedback marker: **作者反馈：** ')
        if line.startswith('**作者反馈：** '):
            if current is None:
                raise ValueError('Feedback needs a numeric heading')
            feedback.setdefault(current, []).append(line.removeprefix('**作者反馈：** '))
            after_feedback = True
    cards, navigation, credits, numbers = [], [], [], set()
    esc = html.escape
    for record in records:
        number = record['id'].split('-', 1)[0]
        if not number.isdigit() or number in numbers:
            raise ValueError('Source IDs need unique numeric prefixes')
        numbers.add(number)
        for key in ('copied_file', 'preview'):
            asset = (gallery / record[key]).resolve()
            if not asset.is_relative_to(gallery.resolve()) or not asset.is_file():
                raise ValueError(f'Missing or nonlocal asset: {record[key]}')
        original = gallery / record['copied_file']
        if hashlib.sha256(original.read_bytes()).hexdigest() != record['sha256']:
            raise ValueError(f'Checksum mismatch: {record["id"]}')
        status = ('你的反馈：' + ' '.join(feedback[number])) if number in feedback else '候选参考：尚未记录偏好反馈。'
        source = record.get('source_url') or '/'.join(filter(None, (
            record.get('repository') or record.get('project'), record.get('source_path'))))
        navigation.append(f'<a href="#figure-{number}">{number}</a>')
        cards.append(f'''<article id="figure-{number}">
<h2><span>{number}</span> {esc(record['title'])}</h2>
<a class="image" href="{esc(quote(record['preview']))}" target="_blank"><img src="{esc(quote(record['preview']))}" alt="{esc(record['role'])}"></a>
<p>{esc(record['role'])}</p><p class="status">{esc(status)}</p>
<details><summary>来源与原文件</summary><p><a href="{esc(quote(record['copied_file']))}">打开原文件</a></p><p class="source">{esc(source)}</p></details>
</article>''')
        if 'attribution' in record:
            credits.append(f'<p>{number}: {esc(record["attribution"])} '
                           f'<a href="{esc(record["license_url"])}">{esc(record["license"])}</a>. '
                           f'{esc(record["changes"])}</p>')
    assets = {(gallery / r[k]).resolve() for r in records for k in ('copied_file', 'preview')}
    extra = sorted(p.relative_to(gallery).as_posix() for p in gallery.rglob('*')
                   if p.is_file() and p.suffix.lower() in {'.png', '.jpg', '.jpeg', '.pdf'}
                   and p.resolve() not in assets)
    if extra:
        raise ValueError('Add sources.json records for: ' + ', '.join(extra))
    if headings - numbers:
        raise ValueError('Feedback contains IDs missing from sources.json')
    return f'''<!doctype html>
<html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Overview figure 审美图库</title><style>{STYLE}</style>
<header><h1>Overview figure 审美图库</h1><p>{len(records)} 张 · Paper / proposal overview · {esc(manifest['updated_on'])}</p>
<p>Yue Zhao 的逐图反馈。点击图片查看大图；后续可按编号补充或修正。候选参考单独标明。</p>
<nav>{''.join(navigation)}<a href="preferences.md">偏好与设计解读</a><a href="index.md">图库索引</a><a href="sources.json">来源清单</a></nav></header>
<main>{''.join(cards)}</main><footer>{''.join(credits)}</footer></html>
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gallery', type=Path, default=GALLERY)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    outputs = {'index.html': render(args.gallery), 'gallery-9-figures.html': REDIRECT}
    for name, content in outputs.items():
        path = args.gallery / name
        if args.check:
            if not path.is_file() or path.read_bytes() != content.encode('utf-8'):
                parser.exit(1, f'Stale gallery page: {path}\nRun build_gallery.py to regenerate.\n')
        else:
            path.write_bytes(content.encode('utf-8'))
    print('Gallery pages and source assets verified.' if args.check else 'Gallery pages updated.')


if __name__ == '__main__':
    main()
