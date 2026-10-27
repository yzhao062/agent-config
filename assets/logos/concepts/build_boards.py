from pathlib import Path
import asyncio
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent
NAMES = ['agent-risk', 'agent-defs', 'agent-style', 'anywhere-agents', 'CatchBench', 'auditable']
ROLES = ['CHANGE / RISK', 'SCAN / DEFINITIONS', 'WRITE / CLARITY', 'CONFIG / PORTABILITY', 'DETECT / TIMING', 'AUDIT / METHODS']

def mark(i, direction, small=False):
    if i == 5:
        return '<div class="art original"><img src="auditable-original.svg" alt="Original auditable mark"></div>'
    source = 'generated-a-v2.png' if direction == 'a' else 'generated-b.png'
    return f'<div class="art generated" style="background-image:url({source});background-position:{i%3*50}% {i//3*100}%" role="img" aria-label="{NAMES[i]} concept"></div>'

def board(direction):
    title, subtitle = ('Connected geometry', '圆端点 · 连续曲线 · 连接关系') if direction == 'a' else ('Cut & open geometry', '统一切角 · 清晰开口 · 负空间')
    cards = ''.join(f'<article>{mark(i,direction)}<h2>{n}</h2><p>{ROLES[i]}</p></article>' for i,n in enumerate(NAMES))
    micro = ''.join(f'<div>{mark(i,direction)}<span>{n}</span></div>' for i,n in enumerate(NAMES))
    samples = ''.join(f'<div class="sample {font.lower()}"><b>{font}</b>'+''.join(f'<span>{n}</span>' for n in NAMES)+'</div>' for font in ['Inter','Manrope'])
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Logo family {direction.upper()}</title><style>
@font-face{{font-family:Inter;src:url(fonts/Inter.ttf)}}@font-face{{font-family:Manrope;src:url(fonts/Manrope.ttf)}}
*{{box-sizing:border-box}}body{{margin:0;background:#edf0f2;color:#0f172a;font-family:Inter,sans-serif}}.board{{width:1400px;background:#fff;padding:56px 70px 40px;margin:auto}}header{{display:flex;justify-content:space-between;align-items:start;border-bottom:1px solid #dce3e8;padding-bottom:28px}}.eyebrow{{font-size:12px;letter-spacing:2px;font-weight:650;color:#52716f}}h1{{font-size:43px;letter-spacing:-1.7px;margin:14px 0 10px;font-weight:600}}.sub{{font-size:15px;color:#64748b}}.edition{{font-size:94px;font-weight:500;line-height:1;color:#0f172a}}.grid{{display:grid;grid-template-columns:repeat(3,1fr);margin:16px 0 20px}}article{{height:285px;display:flex;flex-direction:column;align-items:center;justify-content:center}}.art{{width:220px;height:220px;flex-shrink:0}}.generated{{background-size:300% 200%;background-repeat:no-repeat}}.original{{display:flex;align-items:center;justify-content:center}}.original img{{width:140px;height:140px}}h2{{font-size:27px;font-weight:600;letter-spacing:-.9px;margin:-4px 0 9px}}article p{{font-size:10px;letter-spacing:1.8px;color:#71808f;margin:0}}.section{{border-top:1px solid #dce3e8;padding-top:20px}}.section-label{{font-size:11px;letter-spacing:1.4px;color:#62717e;font-weight:600}}.micro{{display:grid;grid-template-columns:repeat(6,1fr);margin:10px 0 22px}}.micro>div{{display:flex;align-items:center;flex-direction:column}}.micro .art{{width:58px;height:58px}}.micro .original img{{width:36px;height:36px}}.micro span{{font-size:11px;color:#64748b;margin-top:6px}}.sample{{display:grid;grid-template-columns:95px repeat(6,1fr);align-items:center;margin-top:17px;gap:9px}}.sample b{{font-family:Inter;font-weight:500;font-size:11px;letter-spacing:1px;color:#64748b}}.sample span{{font-size:17px;font-weight:600;letter-spacing:-.45px}}.manrope{{font-family:Manrope}}.inter{{font-family:Inter}}footer{{border-top:1px solid #dce3e8;margin-top:29px;padding-top:18px;display:flex;justify-content:space-between;font-size:11px;color:#7b8794}}.swatches{{display:flex;gap:8px;align-items:center}}.swatch{{display:inline-block;width:14px;height:14px;border-radius:50%}}.note{{font-size:11px;color:#71808f;margin-top:15px;line-height:1.6}}
</style></head><body><main class="board"><header><div><div class="eyebrow">YUE ZHAO / OPEN-SOURCE LOGO FAMILY</div><h1>{title}</h1><div class="sub">{subtitle} · 六个项目，同一品牌家族</div></div><div class="edition">{direction.upper()}</div></header><section class="grid">{cards}</section><section class="section"><div class="section-label">SMALL-SIZE LINEUP / 缩小对照</div><div class="micro">{micro}</div></section><section class="section"><div class="section-label">REAL TYPEFACE STUDIES / 真实字体对照</div>{samples}<div class="note">auditable 使用原始 SVG。其余五项为生成式视觉概念，尚未重建为矢量或完成 favicon 验收。</div></section><footer><span>CONCEPT {direction.upper()} / 01 · 2026-10-22</span><div class="swatches"><i class="swatch" style="background:#0f172a"></i><i class="swatch" style="background:#4c9b91"></i><span>SLATE + TEAL / SHARED PALETTE</span></div><span>Typography: Inter 600 · alternate Manrope 600</span></footer></main></body></html>'''

async def main():
    for d in ['a','b']:
        html = board(d).replace('<footer>', '<div style="display:flex;align-items:center;gap:20px;margin-top:18px;font-size:11px;color:#71808f"><span>AUDITABLE / 适配研究</span><img src="auditable-original.svg" width="46" height="46" alt="Original"><span>原件</span><img src="auditable-unboxed-study.svg" width="70" height="70" alt="Unboxed color study"><span>同色无底框试样 · 节点与连线保持不变 · 尚未选定</span></div><footer>')
        (ROOT / f'board-{d}.html').write_text(html, encoding='utf-8')
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width':1400,'height':1400},device_scale_factor=1.5)
        for d in ['a','b']:
            await page.goto((ROOT / f'board-{d}.html').as_uri())
            await page.evaluate('document.fonts.ready')
            await page.locator('.board').screenshot(path=str(ROOT / f'board-{d}.png'))
            print(d, await page.locator('.board').bounding_box())
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
