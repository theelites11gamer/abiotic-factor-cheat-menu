"""Run once in the Mod Editor, right after opening the Cheat Menu project, before opening any of its assets.
Type into the Cmd box at the bottom of the editor:
    py "<this repo>/setup/copy_game_commands.py"

The menu's commands are the Mod Editor's own cheat-command Blueprints. They belong to the game, so this repo
doesn't ship them. This script copies each one (from game-commands.json, parents first) out of your own Mod Editor
install into /ResearchDirectorI7yTl/Commands, reparents each copy onto the copied parent, compiles and saves it.
It skips copies that already exist, so running it twice is harmless."""
import unreal, json
from pathlib import Path

PLUGIN = 'ResearchDirectorI7yTl'
ROOT = Path(unreal.PluginBlueprintLibrary.get_plugin_base_dir(PLUGIN)).parent
order = json.loads((ROOT / 'setup' / 'game-commands.json').read_text())['commands']
tools = unreal.AssetToolsHelpers.get_asset_tools()
copies, made = {}, []

for c in order:
    name, dest = c['copy'], f"/{PLUGIN}/Commands/{c['copy']}"
    bp = unreal.load_object(None, f'{dest}.{name}') if unreal.EditorAssetLibrary.does_asset_exist(dest) else None
    if bp is None:
        src = c['source']
        source = unreal.load_object(None, src + '.' + src.rsplit('/', 1)[1])
        assert isinstance(source, unreal.Blueprint), f'not found in this Mod Editor: {src}'
        bp = tools.duplicate_asset(name, f'/{PLUGIN}/Commands', source)
        assert isinstance(bp, unreal.Blueprint), dest
        if c['parent']:
            unreal.BlueprintEditorLibrary.reparent_blueprint(bp, copies[c['parent']].generated_class())
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        assert unreal.EditorAssetLibrary.save_loaded_asset(bp, False), dest
        made.append(name)
    copies[c['source']] = bp

print(f'CHEATMENU_SETUP: {len(copies)} command Blueprints present, {len(made)} copied now.')
if made:
    print('CHEATMENU_SETUP: close the editor (choose Don\'t Save if it asks about anything else) and open the project again.')
