"""Send a script to the Mod Editor bridge and print its output. Usage: py run.py script.py [json-args] [timeout]"""
import json, sys, time, uuid
from pathlib import Path
bridge = Path(__file__).parent / 'bridge'
script = str(Path(sys.argv[1]).resolve())
args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
timeout = float(sys.argv[3]) if len(sys.argv) > 3 else 600
rid = str(uuid.uuid4())
(bridge / 'request.json').write_text(json.dumps({'id': rid, 'script': script, 'args': args}))
end = time.time() + timeout
while time.time() < end:
    time.sleep(0.3)
    try:
        r = json.loads((bridge / 'response.json').read_text())
    except Exception:
        continue
    if r.get('id') == rid:
        print(r.get('output', ''), end='')
        if not r['ok']:
            print(r['error']); sys.exit(1)
        sys.exit(0)
print('TIMEOUT waiting for editor'); sys.exit(2)
