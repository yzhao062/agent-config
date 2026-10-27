from pathlib import Path
import asyncio
import shutil
import cairosvg
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.svgPathPen import SVGPathPen
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'refined-b'
OUT.mkdir(exist_ok=True)
NAVY, TEAL = '#0F172A', '#4C9B91'
NAMES = ['agent-risk', 'agent-defs', 'agent-style', 'anywhere-agents', 'CatchBench', 'auditable']
FONT = instantiateVariableFont(TTFont(ROOT / 'concepts/fonts/Inter.ttf'), {'wght': 600, 'opsz': 32})
GLYPHS = FONT.getGlyphSet()
CMAP = FONT.getBestCmap()

def diamond(x, y, r=10, color='ACCENT'):
    return f'<path fill="{color}" d="M{x} {y-r} {x+r} {y} {x} {y+r} {x-r} {y}Z"/>'

def path(d, color='INK'):
    return f'<path fill="{color}" d="{d}"/>'

MARKS = [
    path('M96 22 108 44 53 144 79 144 91 166 42 166 30 146Z M108 64 138 116 157 116 170 138 125 138 96 86Z M110 121 136 166 182 166 169 144 149 144 123 99Z') + diamond(96,116,12),
    path('M36 56 56 36 76 36 76 54 63 54 54 63 54 76 36 76Z M124 36 144 36 164 56 164 76 146 76 146 63 137 54 124 54Z M36 124 54 124 54 137 63 146 76 146 76 164 56 164 36 144Z M124 146 137 146 146 137 146 124 164 124 164 144 144 164 124 164Z M66 70 134 70 142 78 142 86 58 86 58 78Z M58 94 134 94 142 102 142 110 58 110Z M58 118 100 118 100 134 66 134 58 126Z') + path('M110 118 142 118 126 134 110 134Z','ACCENT'),
    path('M86 24 114 24 125 67 146 110 113 174 104 174 104 126 122 108 104 90 104 46 96 46 96 90 78 108 96 126 96 174 87 174 54 110 75 67Z') + diamond(100,108,10),
    path('M88 38 110 60 110 85 90 85 90 68 80 58 56 58 46 68 46 94 56 104 74 104 74 124 48 124 26 102 26 60 48 38Z M126 76 152 76 174 98 174 140 152 162 112 162 90 140 90 115 110 115 110 132 120 142 144 142 154 132 154 106 144 96 126 96Z') + path('M69 108 108 69 122 83 83 122Z','ACCENT'),
    path('M70 30 132 30 164 62 164 78 144 78 144 70 124 50 78 50 50 78 50 122 78 150 124 150 144 130 144 122 164 122 164 138 132 170 70 170 30 130 30 70Z') + diamond(106,40,15,'WHITE') + diamond(106,40,10) + diamond(40,100,15,'WHITE') + diamond(40,100,10) + diamond(106,160,15,'WHITE') + diamond(106,160,10),
    path('M94 34 106 34 164 164 148 171 100 62 52 171 36 164Z M68 111 132 111 132 127 68 127Z') + diamond(100,36,14) + diamond(64,119,14,'INK') + diamond(136,119,14,'INK') + diamond(44,166,14,'INK') + diamond(156,166,14,'INK'),
]

def body(i, dark=False, mono=False):
    ink = '#FFFFFF' if dark else NAVY
    accent = ink if mono else ('#70C4B8' if dark else TEAL)
    # Cutouts remain transparent in the exported icon.
    s = MARKS[i].replace('INK', ink).replace('ACCENT', accent)
    if 'WHITE' in s:
        parts = s.split('<path fill="WHITE"')
        mask = '<rect width="200" height="200" fill="white"/>'
        for part in parts[1:]:
            mask += '<path fill="black"' + part.split('/>')[0] + '/>'
        ring = parts[0]
        accents = ''.join(part.split('/>', 1)[1] for part in parts[1:])
        s = f'<defs><mask id="cut">{mask}</mask></defs><g mask="url(#cut)">{ring}</g>{accents}'
    return s

def svg(i, dark=False, mono=False):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" role="img" aria-label="{NAMES[i]}"><title>{NAMES[i]}</title>{body(i,dark,mono)}</svg>'

def lettering(text, color):
    x = 0
    paths = []
    for c in text:
        glyph = GLYPHS[CMAP[ord(c)]]
        pen = SVGPathPen(GLYPHS)
        glyph.draw(pen)
        paths.append(f'<path transform="translate({x} 0)" d="{pen.getCommands()}"/>')
        x += glyph.width
    scale = 46 / FONT['head'].unitsPerEm
    return f'<g fill="{color}" transform="translate(188 114) scale({scale} {-scale})">'+''.join(paths)+'</g>', x*scale

def lockup(i, dark=False):
    letters, width = lettering(NAMES[i], '#FFFFFF' if dark else NAVY)
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {int(width+212)} 200" role="img" aria-label="{NAMES[i]}"><title>{NAMES[i]}</title><g transform="translate(4 20) scale(.8)">{body(i,dark)}</g>{letters}</svg>'

def export():
    for i, name in enumerate(NAMES):
        dest = OUT / name.lower()
        dest.mkdir(exist_ok=True)
        for variant, dark, mono in [('mark',False,False),('mark-dark',True,False),('mark-mono',False,True),('mark-white',True,True)]:
            content = svg(i,dark,mono)
            (dest/f'{variant}.svg').write_text(content)
            cairosvg.svg2png(bytestring=content.encode(),write_to=str(dest/f'{variant}.png'),output_width=512,output_height=512)
        for dark in [False,True]:
            content = lockup(i,dark)
            stem = 'logo-dark' if dark else 'logo'
            (dest/f'{stem}.svg').write_text(content)
            cairosvg.svg2png(bytestring=content.encode(),write_to=str(dest/f'{stem}.png'),output_height=200)
        favicon = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200"><title>{name}</title><path fill="{NAVY}" d="M24 0H176L200 24V176L176 200H24L0 176V24Z"/><g transform="translate(16 16) scale(.84)">{body(i,True)}</g></svg>'
        (dest/'favicon.svg').write_text(favicon)
        shutil.copy(ROOT/'concepts/fonts/Inter-OFL.txt',dest/'Inter-OFL.txt')

async def board():
    cards = ''.join(f'<article><img src="{n.lower()}/mark.svg"><h2>{n}</h2></article>' for n in NAMES)
    dark = ''.join(f'<div><img src="{n.lower()}/mark-dark.svg"><span>{n}</span></div>' for n in NAMES)
    sizes = ''.join(f'<div class="size"><b>{size}px</b>'+''.join(f'<img width="{size}" height="{size}" src="{n.lower()}/mark.svg">' for n in NAMES)+'</div>' for size in [16,24,32,64])
    html = f'''<!doctype html><html><meta charset="utf-8"><style>
@font-face{{font-family:Inter;src:url(../concepts/fonts/Inter.ttf);font-weight:100 900}}*{{box-sizing:border-box}}body{{margin:0;background:#e7ecef;font-family:Inter;color:#0f172a}}main{{width:1400px;margin:auto;background:white;padding:58px 66px 38px}}header{{border-bottom:1px solid #dce3e8;padding-bottom:28px}}.eyebrow{{font-size:12px;letter-spacing:2px;color:#4c817b;font-weight:650}}h1{{font-size:46px;letter-spacing:-2px;margin:16px 0 10px;font-weight:600}}header p{{color:#64748b;margin:0;font-size:15px}}.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;padding:24px 0 34px}}article{{text-align:center;padding:15px 0}}article img{{width:190px;height:190px}}h2{{font-size:28px;letter-spacing:-1px;font-weight:600;margin:8px 0}}.dark{{background:#0f172a;color:white;display:grid;grid-template-columns:repeat(6,1fr);padding:24px 16px}}.dark>div{{display:flex;align-items:center;flex-direction:column;gap:10px}}.dark img{{width:64px;height:64px}}.dark span{{font-size:13px;font-weight:600}}.size{{display:grid;grid-template-columns:90px repeat(6,1fr);align-items:center;justify-items:center;margin:18px 0}}.size b{{font-size:12px;color:#64748b;font-weight:500;justify-self:start}}.label{{font-size:11px;letter-spacing:1.5px;color:#64748b;margin-top:30px}}footer{{border-top:1px solid #dce3e8;margin-top:25px;padding-top:20px;display:flex;justify-content:space-between;font-size:11px;color:#64748b}}</style><main><header><div class="eyebrow">YUE ZHAO / OPEN-SOURCE LOGO FAMILY</div><h1>One family. Six distinct tools.</h1><p>B / 02 · 统一切角与开口 · auditable 五节点适配 · anywhere-agents 双接口 · Inter 600</p></header><section class="grid">{cards}</section><section class="dark">{dark}</section><div class="label">ACTUAL-SIZE CHECK / 原尺寸对照</div>{sizes}<footer><span>REFINED B / EDITABLE SVG MASTERS</span><span>SLATE #0F172A + TEAL #4C9B91 · INTER 600</span></footer></main></html>'''
    (OUT/'family.html').write_text(html)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width':1400,'height':1500},device_scale_factor=1.5)
        await page.goto((OUT/'family.html').as_uri())
        await page.evaluate('document.fonts.ready')
        await page.locator('main').screenshot(path=str(OUT/'family.png'))
        await browser.close()

if __name__ == '__main__':
    export()
    asyncio.run(board())
