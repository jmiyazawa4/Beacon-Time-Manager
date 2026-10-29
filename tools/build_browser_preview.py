"""Build a single HTML file for review without Python or a local server.
Developer usage: python tools/build_browser_preview.py --output /path/Beacon.html
Optional --snapshots is a directory of previously verified per-sport JSON responses.
"""
from argparse import ArgumentParser
from base64 import b64encode
from pathlib import Path
import json
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1] / 'beacon-planner'


def build(output, snapshots=None):
    html = (ROOT / 'index.html').read_text()
    academic = json.loads((ROOT / 'academic-calendar.json').read_text())
    sports = {}
    if snapshots:
        for path in Path(snapshots).glob('*.json'):
            response = json.loads(path.read_text())
            if isinstance(response.get('events'), list) and response.get('source', '').startswith('https://bushnellbeacons.com/sports/'):
                sports[path.stem] = response
    def inline_css(match):
        return '<style>' + (ROOT / match[1]).read_text() + '</style>'
    html = re.sub(r'<link rel="stylesheet" href="([^\"]+)">', inline_css, html)
    def inline_script(match):
        code = (ROOT / match[1]).read_text()
        code = re.sub(r'</script', r'<\\/script', code, flags=re.I)
        return '<script>' + code + '</script>'
    html = re.sub(r'<script src="([^\"]+)"></script>', inline_script, html)
    logo = 'data:image/png;base64,' + b64encode((ROOT / 'assets/beacon-b.png').read_bytes()).decode()
    html = html.replace('assets/beacon-b.png', logo)
    payload = json.dumps({'academic': academic, 'sports': sports}, ensure_ascii=True).replace('<', '\\u003c')
    bootstrap = '''<script>
(() => {
  const saved=PAYLOAD;
  const respond=(body,status=200)=>Promise.resolve(new Response(JSON.stringify(body),{status,headers:{'Content-Type':'application/json'}}));
  const fetchOriginal=window.fetch.bind(window);
  window.fetch=(input,options)=>{
    const raw=typeof input==='string'?input:input.url;
    const url=new URL(raw,'https://beacon-preview.invalid/');
    if(url.pathname.endsWith('/academic-calendar.json'))return respond(saved.academic);
    if(url.pathname==='/api/schedule'){
      const sport=url.searchParams.get('sport');
      if(saved.sports[sport])return respond(saved.sports[sport]);
      return respond({error:'No saved schedule for this sport in the downloaded preview.',detail:'Use the official schedule link. Live updates require the hosted website.'},503);
    }
    if(url.pathname==='/api/verse')return respond({error:'Live NIV verses require the hosted website. Use the Bible Gateway link to read today’s verse.'},503);
    if(url.pathname==='/api/import')return respond({error:'Calendar-file import requires the hosted website.'},503);
    return fetchOriginal(input,options);
  };
  document.addEventListener('DOMContentLoaded',()=>{
    const notice=document.createElement('div');notice.className='preview-notice';
    notice.textContent='Downloaded review version · Saved official schedules: baseball, men’s basketball, volleyball. Academic dates are included. Live schedule updates, NIV loading, and calendar-file import require the hosted website.';
    document.querySelector('header').after(notice);
  });
})();
</script><style>.preview-notice{max-width:1446px;margin:0 auto 18px;padding:12px 16px;border-left:4px solid #b88a2c;background:#fff8e7;color:#655128;font:12px/1.6 system-ui,sans-serif}@media print{.preview-notice{display:none}}</style>'''.replace('PAYLOAD', payload)
    html = html.replace('<head>', '<head>' + bootstrap, 1)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html)
    readme = '''BEACON TIME MANAGER - BROWSER REVIEW

1. Open Beacon-Time-Manager.html in Chrome, Edge, Firefox, or Safari.
2. Add or edit activities, choose colors, switch weeks, and try Print / Download.

No Python, installation, or account is needed. Keep using this same file and
browser for locally saved activities; clearing browser storage can erase them.
If your computer blocks downloaded HTML files, use an approved browser or ask
for a hosted link instead.

This is an interactive downloaded review, not a live public website.
Academic dates are included from the supplied 2026-2027 calendar.
Official baseball, men's basketball, and volleyball schedules were captured
on October 29, 2026. Check the official athletics site for later changes.
Other sports, live refresh, NIV loading, and .ics import need the hosted site.
PDF downloads work directly in your browser. NIV can be read using the card's
Bible Gateway link; no other translation is substituted.
'''
    (output.parent / 'READ-ME.txt').write_text(readme)
    with zipfile.ZipFile(output.with_suffix('.zip'), 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.write(output, 'Beacon-Time-Manager.html')
        archive.writestr('READ-ME.txt', readme)
    return output


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--snapshots')
    args = parser.parse_args()
    print(build(args.output, args.snapshots))
