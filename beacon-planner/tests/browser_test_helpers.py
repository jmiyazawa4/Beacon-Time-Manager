"""Poll using DevTools function calls without weakening the site's CSP."""
from time import monotonic

def wait_js(page, expression, timeout=30000):
    deadline=monotonic()+timeout/1000
    last=None
    while monotonic()<deadline:
        last=page.evaluate('() => ('+expression+')')
        if last:return last
        page.wait_for_timeout(50)
    raise AssertionError('Browser condition timed out: '+expression+'; last='+repr(last))
