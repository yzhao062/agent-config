"""Copy approved family assets into clean publishing checkouts; never commit or push."""
from pathlib import Path
import shutil

SOURCE = Path(__file__).resolve().parent / 'refined-b'
CHECKOUTS = Path('/tmp/logo-publish-20261023')
NAMES = ['agent-risk', 'agent-defs', 'agent-style', 'anywhere-agents', 'catchbench', 'auditable']

def picture(name, prefix, width):
    return f'''<picture>
  <source media="(prefers-color-scheme: dark)" srcset="{prefix}/logo-dark.svg">
  <img src="{prefix}/logo.svg" alt="{name}" width="{width}">
</picture>'''

for repo in NAMES:
    root = CHECKOUTS / repo
    name = 'CatchBench' if repo == 'catchbench' else repo
    target = root / 'docs/assets/brand'
    target.mkdir(parents=True, exist_ok=True)
    for asset in (SOURCE/repo).iterdir():
        shutil.copy(asset, target/asset.name)
    width = 440 if repo == 'anywhere-agents' else 350
    for readme in [root/'README.md', *root.glob('README.*.md')]:
        text = readme.read_text()
        if '<!-- logo-family -->' not in text:
            insertion = f'\n<!-- logo-family -->\n{picture(name,"docs/assets/brand",width)}\n'
            anchor = '<div align="center">'
            if anchor in text:
                text = text.replace(anchor+'\n\n', anchor+'\n'+insertion+'\n', 1)
            else:
                text = insertion+'\n'+text
            readme.write_text(text)
    config = root/'mkdocs.yml'
    if config.exists():
        text = config.read_text()
        if repo == 'auditable':
            text = text.replace('logo: assets/auditable-mark.svg','logo: assets/brand/mark-white.svg').replace('favicon: assets/favicon.ico','favicon: assets/brand/favicon.svg')
        else:
            text = text.replace('  name: material\n','  name: material\n  logo: assets/brand/mark-white.svg\n  favicon: assets/brand/favicon.svg\n',1)
        config.write_text(text)
    (target/'README.md').write_text(f'''# {name} brand assets

The B family uses cut corners, open geometry, slate (#0F172A), and teal (#4C9B91). The dark variant uses white and lighter teal (#70C4B8). Wordmarks use Inter SemiBold (600), converted to vector paths so rendering does not require an installed font. The Inter license is included.

Use `logo.svg` on light backgrounds and `logo-dark.svg` on dark backgrounds. `mark.svg` and `mark-dark.svg` are transparent icons; `mark-mono.svg` and `mark-white.svg` are single-color versions. PNG exports are included. `favicon.svg` has an opaque cut-corner tile for browser tabs. Prefer at least 24 px for icon details; at 16 px the silhouette carries identity.

Editable geometry and the shared generator are maintained in yzhao062/agent-config under `assets/logos/`. The original auditable mark, where present, remains at its existing path.
''')
    print(repo, 'prepared', len(list(target.iterdir())), 'assets')
