"""Build a single HTML file for review without Python or a local server.
Developer usage: python tools/build_browser_preview.py --output /path/Beacon.html
Optional --snapshots is a directory of previously verified per-sport JSON responses.
"""
from argparse import ArgumentParser
from base64 import b64encode
from hashlib import sha256
from pathlib import Path
import json
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1] / 'beacon-planner'


def build(output, snapshots=None, hosted_preview=False, save_on_device=False):
    if hosted_preview and save_on_device:
        raise ValueError("Choose either locked preview or device saving")
    html = (ROOT / 'index.html').read_text()
    academic = json.loads((ROOT / 'academic-calendar.json').read_text())
    sports = {}
    snapshots=snapshots or (ROOT/'schedules')
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
    triangle = 'data:image/png;base64,' + b64encode((ROOT / 'assets/tri-athlete-model.png').read_bytes()).decode()
    html = html.replace('assets/tri-athlete-model.png', triangle)
    payload = json.dumps({'academic': academic, 'sports': sports,'plan':json.loads((ROOT/'reading-plan.json').read_text()),'verses':json.loads((ROOT/'daily-verses.json').read_text())}, ensure_ascii=True).replace('<', '\\u003c')
    bootstrap = r'''<script>
(() => {
  const saved=PAYLOAD;
  window.BEACON_REVIEW_PRIVATE=HOSTED_PREVIEW;
  const respond=(body,status=200)=>Promise.resolve(new Response(JSON.stringify(body),{status,headers:{'Content-Type':'application/json'}}));
  const fetchOriginal=window.fetch.bind(window);
  window.fetch=(input,options)=>{
    const raw=typeof input==='string'?input:input.url;
    const url=new URL(raw,'https://beacon-preview.invalid/');
    if(url.pathname.endsWith('/academic-calendar.json'))return respond(saved.academic);
    if(url.pathname.endsWith('/reading-plan.json'))return respond(saved.plan);
    if(url.pathname.endsWith('/daily-verses.json'))return respond(saved.verses);
    const match=/\/schedules\/([a-z-]+)\.json$/.exec(url.pathname);
    if(match){
      if(saved.sports[match[1]])return respond(saved.sports[match[1]]);
      return respond({available:false,error:'A saved schedule is not available for this sport. Use the official athletics link.',events:[]},404);
    }
    return fetchOriginal(input,options);
  };
  document.addEventListener('DOMContentLoaded',()=>{
    const notice=document.createElement('div');notice.className='preview-notice';
    notice.textContent=window.BEACON_REVIEW_PRIVATE?'Private session · Changes are not saved.':'Saves on this device unless Private session is on.';
    document.querySelector('header').after(notice);
  });
})();
</script><style>.preview-notice{max-width:1446px;margin:0 auto 18px;padding:12px 16px;border-left:4px solid #b88a2c;background:#fff8e7;color:#655128;font:12px/1.6 system-ui,sans-serif}@media print{.preview-notice{display:none}}</style>'''.replace('PAYLOAD', payload).replace('HOSTED_PREVIEW','true' if hosted_preview else 'false')
    html = html.replace('<head>', '<head>' + bootstrap, 1)
    scripts=re.findall(r'<script>(.*?)</script>',html,re.S)
    hashes=' '.join("'sha256-"+b64encode(sha256(script.encode()).digest()).decode()+"'" for script in scripts)
    policy="default-src 'none'; script-src "+hashes+"; style-src 'unsafe-inline'; img-src data: blob:; connect-src 'none'; object-src 'none'; frame-src 'none'; base-uri 'none'; form-action 'none'"
    html=html.replace('<head>','<head><meta name="referrer" content="no-referrer"><meta http-equiv="Content-Security-Policy" content="'+policy+'">',1)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html)
    readme = '''BEACON TIME MANAGER - BROWSER REVIEW

Open Beacon-Time-Manager.html in a browser. No Python, installation, paid
hosting, Bible API, or account is needed by the reader. The self-contained
site includes saved official season schedules, supplied university dates,
public-domain KJV daily verses, and a licensed yearly passage-reference plan.
Schedules are snapshots: check their last-updated date and confirm changes
with athletics. Changes require a new site-data update.

Calendar files are parsed locally, never uploaded. PDF downloads are local.
Normal saving uses this browser profile and is not encrypted. On shared
computers use Private session. A --hosted-preview build locks Private session
on; the --save-on-device build allows local saving and an optional private session.
Clearing site data erases saved entries. No cloud backup or device sync exists.

The ordinary downloaded file may save personal activities if the browser
permits local-file storage. This chat may not support file downloads; use the
GitHub Pages review link instead. The review is not a school-approved student
release. Read SECURITY.md in the repository before a real rollout.
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
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--hosted-preview',action='store_true')
    mode.add_argument('--save-on-device',action='store_true',help='Allow browser-local saving with optional private sessions')
    args = parser.parse_args()
    print(build(args.output, args.snapshots, args.hosted_preview, args.save_on_device))
