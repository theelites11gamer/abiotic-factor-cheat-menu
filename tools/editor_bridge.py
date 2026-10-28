"""Run once in the Mod Editor (File > Execute Python Script).
Afterwards the editor runs any script named in tools/bridge/request.json and writes response.json."""
import unreal, json, traceback, io, contextlib
from pathlib import Path
try:
    base = Path(__file__).resolve().parent / 'bridge'
except NameError:  # pasted in some other way: fall back to the mounted project
    base = Path(unreal.PluginBlueprintLibrary.get_plugin_base_dir('ResearchDirectorI7yTl')).parent / 'tools' / 'bridge'
base.mkdir(parents=True, exist_ok=True)
old = globals().get('_cm_bridge_handle')
if old is not None:
    unreal.unregister_slate_post_tick_callback(old)
# A request left over from an earlier editor session (say, one that quit the editor) must not run again.
(base / 'request.json').unlink(missing_ok=True)
globals()['_cm_bridge_last'] = None

def _cm_bridge_tick(delta):
    request = base / 'request.json'
    if not request.exists():
        return
    try:
        data = json.loads(request.read_text(encoding='utf-8-sig'))
    except Exception:
        return
    if data.get('id') == globals().get('_cm_bridge_last'):
        return
    globals()['_cm_bridge_last'] = data.get('id')
    out = io.StringIO()
    try:
        code = Path(data['script']).read_text(encoding='utf-8-sig')
        with contextlib.redirect_stdout(out):
            exec(compile(code, data['script'], 'exec'), {'__name__': '__bridge__', 'ARGS': data.get('args', {})})
        result = {'id': data['id'], 'ok': True, 'output': out.getvalue()}
    except Exception:
        result = {'id': data['id'], 'ok': False, 'output': out.getvalue(), 'error': traceback.format_exc()}
    (base / 'response.json').write_text(json.dumps(result, indent=1))

globals()['_cm_bridge_handle'] = unreal.register_slate_post_tick_callback(_cm_bridge_tick)
(base / 'response.json').write_text(json.dumps({'id': 'ready', 'ok': True, 'output': 'bridge ready'}))
print('CHEATMENU_BRIDGE_READY')
