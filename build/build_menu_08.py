"""Builds the v0.8 (right-side panel + ALL tab) widget trees (layout only) for W_DirectorMenu, W_DirectorItemEntry
and W_DirectorCmdEntry. Run inside the Mod Editor. The event graphs come from generate_graphs_08.py and are pasted afterwards."""
import unreal
import json
from pathlib import Path

PLUGIN = 'ResearchDirectorI7yTl'
ROOT = Path(unreal.PluginBlueprintLibrary.get_plugin_base_dir(PLUGIN)).parent / 'build'
SPEC = json.loads((ROOT / 'menu-spec-08.json').read_text())
system = unreal.get_default_object(unreal.SystemLibrary)
FONT = unreal.load_asset('/Game/Blueprints/Widgets/Fonts/texgyreadventor_Font')

C = {k: unreal.LinearColor(*v) for k, v in SPEC['colors'].items()}

def widget_bp(name):
    path = f'/{PLUGIN}/Widgets/{name}'
    wb = unreal.load_asset(path)
    if wb is None:
        factory = unreal.WidgetBlueprintFactory()
        factory.set_editor_property('ParentClass', unreal.UserWidget.static_class())
        wb = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, f'/{PLUGIN}/Widgets', unreal.WidgetBlueprint, factory)
    return wb, path

class Tree:
    def __init__(self, wb, path):
        self.wb, self.path = wb, path
        self.tree = unreal.load_object(None, f'{path}.{path.rsplit("/", 1)[1]}:WidgetTree')
        self.made = set()

    def obj(self, cls, name, var=False):
        assert name not in self.made, name
        self.made.add(name)
        w = unreal.load_object(None, f'{self.tree.get_path_name()}.{name}')
        if w is None or not isinstance(w, cls):
            w = unreal.new_object(cls, outer=self.tree, name=name)
        system.call_method('SetBoolPropertyByName', (w, 'bIsVariable', var))
        if isinstance(w, unreal.PanelWidget):
            w.clear_children()
        return w

    def root(self, w):
        system.call_method('SetObjectPropertyByName', (self.tree, 'RootWidget', w))

def font(size, bold=False):
    f = unreal.SlateFontInfo()
    f.set_editor_property('font_object', FONT)
    f.set_editor_property('typeface_font_name', 'Bold' if bold else 'Default')
    f.set_editor_property('size', size)
    return f

def brush(color, radius=6, outline=None, width=0.0):
    b = unreal.SlateBrush()
    b.set_editor_property('draw_as', unreal.SlateBrushDrawType.ROUNDED_BOX)
    b.set_editor_property('tint_color', unreal.SlateColor(specified_color=color))
    o = unreal.SlateBrushOutlineSettings()
    o.set_editor_property('corner_radii', unreal.Vector4(radius, radius, radius, radius))
    o.set_editor_property('rounding_type', unreal.SlateBrushRoundingType.FIXED_RADIUS)
    if outline is not None:
        o.set_editor_property('color', unreal.SlateColor(specified_color=outline))
        o.set_editor_property('width', width)
    b.set_editor_property('outline_settings', o)
    return b

def text(t, name, value, size=15, bold=False, color='text', var=False, justify=None):
    w = t.obj(unreal.TextBlock, name, var)
    w.set_text(value)
    w.set_font(font(size, bold))
    w.set_color_and_opacity(unreal.SlateColor(specified_color=C[color]))
    if justify:
        w.set_editor_property('justification', justify)
    return w

def style_button(b, base, radius=6):
    # Neutral brush tints; the colour comes from BackgroundColor so the graph can recolour at runtime.
    st = b.get_editor_property('widget_style')
    st.set_editor_property('normal', brush(unreal.LinearColor(1, 1, 1, 1), radius, C['outline'], 1.0))
    st.set_editor_property('hovered', brush(unreal.LinearColor(1.9, 1.9, 1.9, 1), radius, C['accent'], 1.0))
    st.set_editor_property('pressed', brush(unreal.LinearColor(2.8, 2.8, 2.8, 1), radius, C['accent'], 1.0))
    st.set_editor_property('disabled', brush(unreal.LinearColor(.5, .5, .5, .6), radius))
    st.set_editor_property('normal_padding', unreal.Margin(12, 8, 12, 8))
    st.set_editor_property('pressed_padding', unreal.Margin(12, 9, 12, 7))
    b.set_editor_property('widget_style', st)
    b.set_background_color(C[base])

def button(t, name, label, base='button', size=15, tip=None, center=True):
    b = t.obj(unreal.Button, name, True)
    style_button(b, base)
    lbl = text(t, name + '_Label', label, size, True, 'text', justify=unreal.TextJustify.CENTER if center else None)
    slot = b.set_content(lbl)
    slot.set_horizontal_alignment(unreal.HorizontalAlignment.H_ALIGN_CENTER if center else unreal.HorizontalAlignment.H_ALIGN_LEFT)
    slot.set_vertical_alignment(unreal.VerticalAlignment.V_ALIGN_CENTER)
    if not center:
        slot.set_padding(unreal.Margin(10, 0, 0, 0))
    if tip:
        b.set_tool_tip_text(tip)
    return b

def toggle(t, name, label, tip):
    b = t.obj(unreal.Button, 'T_' + name, True)
    style_button(b, 'toggle_off')
    row = t.obj(unreal.HorizontalBox, 'TR_' + name)
    s = row.add_child_to_horizontal_box(text(t, 'TL_' + name, label, 14, True))
    s.set_size(unreal.SlateChildSize(1.0, unreal.SlateSizeRule.FILL))
    s.set_vertical_alignment(unreal.VerticalAlignment.V_ALIGN_CENTER)
    s = row.add_child_to_horizontal_box(text(t, 'TS_' + name, 'OFF', 12, True, 'dim', var=True))
    s.set_padding(unreal.Margin(8, 0, 0, 0))
    s.set_vertical_alignment(unreal.VerticalAlignment.V_ALIGN_CENTER)
    slot = b.set_content(row)
    slot.set_horizontal_alignment(unreal.HorizontalAlignment.H_ALIGN_FILL)
    slot.set_vertical_alignment(unreal.VerticalAlignment.V_ALIGN_CENTER)
    slot.set_padding(unreal.Margin(6, 0, 6, 0))
    b.set_tool_tip_text(tip)
    return b

def vbox_add(box, w, pad=(0, 0, 0, 0), fill=False, halign=None):
    s = box.add_child_to_vertical_box(w)
    s.set_padding(unreal.Margin(*pad))
    if fill:
        s.set_size(unreal.SlateChildSize(1.0, unreal.SlateSizeRule.FILL))
    if halign:
        s.set_horizontal_alignment(halign)
    return s

def hbox_add(box, w, pad=(0, 0, 0, 0), fill=None, valign=unreal.VerticalAlignment.V_ALIGN_FILL):
    s = box.add_child_to_horizontal_box(w)
    s.set_padding(unreal.Margin(*pad))
    if fill:
        s.set_size(unreal.SlateChildSize(fill, unreal.SlateSizeRule.FILL))
    s.set_vertical_alignment(valign)
    return s

def sized(t, name, w, width=None, height=None):
    sb = t.obj(unreal.SizeBox, name)
    if width:
        sb.set_width_override(width)
    if height:
        sb.set_height_override(height)
    sb.set_content(w)
    return sb

def grid(t, name, items, cols, pad=5, height=None):
    g = t.obj(unreal.UniformGridPanel, name)
    g.set_slot_padding(unreal.Margin(pad, pad, pad, pad))
    if height:
        g.set_min_desired_slot_height(height)
    for i, w in enumerate(items):
        s = g.add_child_to_uniform_grid(w, i // cols, i % cols)
        s.set_horizontal_alignment(unreal.HorizontalAlignment.H_ALIGN_FILL)
        s.set_vertical_alignment(unreal.VerticalAlignment.V_ALIGN_FILL)
    return g

def section(t, name, label):
    return text(t, name, label, 13, True, 'accent')

def panel(t, name, color, pad, radius=8, outline=None):
    b = t.obj(unreal.Border, name)
    b.set_editor_property('background', brush(C[color], radius, C[outline] if outline else None, 1.0 if outline else 0.0))
    b.set_padding(unreal.Margin(*pad))
    return b

def compile_save(wb):
    unreal.BlueprintEditorLibrary.compile_blueprint(wb)
    assert unreal.EditorAssetLibrary.save_loaded_asset(wb, False)

# ---------------------------------------------------------------- item entry
ewb, epath = widget_bp('W_DirectorItemEntry')
t = Tree(ewb, epath)
eb = t.obj(unreal.Button, 'EntryButton', True)
style_button(eb, 'entry', 5)
row = t.obj(unreal.HorizontalBox, 'EntryRow')
icon = t.obj(unreal.Image, 'EntryIcon', True)
hbox_add(row, sized(t, 'EntryIconSize', icon, 40, 40), (0, 0, 12, 0), valign=unreal.VerticalAlignment.V_ALIGN_CENTER)
col = t.obj(unreal.VerticalBox, 'EntryText')
vbox_add(col, text(t, 'EntryName', 'Item name', 15, True, var=True))
vbox_add(col, text(t, 'EntryId', 'item_id', 12, False, 'dim', var=True))
hbox_add(row, col, fill=1.0, valign=unreal.VerticalAlignment.V_ALIGN_CENTER)
slot = eb.set_content(row)
slot.set_horizontal_alignment(unreal.HorizontalAlignment.H_ALIGN_FILL)
t.root(eb)
compile_save(ewb)

# ---------------------------------------------------------------- command / option entry (ALL tab)
cwb, cpath = widget_bp('W_DirectorCmdEntry')
t = Tree(cwb, cpath)
cb = t.obj(unreal.Button, 'EntryButton', True)
style_button(cb, 'entry', 5)
col = t.obj(unreal.VerticalBox, 'EntryText')
vbox_add(col, text(t, 'EntryName', 'Command', 14, True, var=True))
d = text(t, 'EntryDesc', 'What it does', 11, False, 'dim', var=True)
d.set_auto_wrap_text(True)
vbox_add(col, d)
k = text(t, 'EntryKey', '', 8, False, 'dim', var=True)
k.set_visibility(unreal.SlateVisibility.COLLAPSED)
vbox_add(col, k)
slot = cb.set_content(col)
slot.set_horizontal_alignment(unreal.HorizontalAlignment.H_ALIGN_FILL)
t.root(cb)
compile_save(cwb)

# ---------------------------------------------------------------- main menu
wb, path = widget_bp('W_DirectorMenu')
t = Tree(wb, path)
canvas = t.obj(unreal.CanvasPanel, 'MenuCanvas')
t.root(canvas)

# Full-screen invisible button: swallows clicks outside the panel so the game doesn't get them.
shade = t.obj(unreal.Button, 'Backdrop')
st = shade.get_editor_property('widget_style')
for k in ['normal', 'hovered', 'pressed']:
    st.set_editor_property(k, brush(C['backdrop'], 0))
shade.set_editor_property('widget_style', st)
shade.set_editor_property('is_focusable', False)
s = canvas.add_child_to_canvas(shade)
s.set_anchors(unreal.Anchors(unreal.Vector2D(0, 0), unreal.Vector2D(1, 1)))
s.set_offsets(unreal.Margin(0, 0, 0, 0))

frame = panel(t, 'Frame', 'panel', (0, 0, 0, 0), 10, 'outline')
s = canvas.add_child_to_canvas(frame)
W, H = SPEC['size']
# Docked to the right edge, full height.
M = SPEC['margin']
s.set_anchors(unreal.Anchors(unreal.Vector2D(1, 0), unreal.Vector2D(1, 1)))
s.set_alignment(unreal.Vector2D(0, 0))
s.set_offsets(unreal.Margin(-(W + M), M, W, M))
main = t.obj(unreal.VerticalBox, 'Main')
frame.set_content(main)

# header
head = panel(t, 'Header', 'header', (22, 14, 16, 14), 10)
hrow = t.obj(unreal.HorizontalBox, 'HeaderRow')
htxt = t.obj(unreal.VerticalBox, 'HeaderText')
vbox_add(htxt, text(t, 'Title', 'CHEAT MENU', 24, True, 'accent'))
vbox_add(htxt, text(t, 'Subtitle', SPEC['subtitle'], 13, False, 'dim'))
hbox_add(hrow, htxt, fill=1.0, valign=unreal.VerticalAlignment.V_ALIGN_CENTER)
hbox_add(hrow, button(t, 'CloseButton', 'CLOSE', 'danger', 14), valign=unreal.VerticalAlignment.V_ALIGN_CENTER)
head.set_content(hrow)
vbox_add(main, head)

# body: tabs + pages
body = t.obj(unreal.VerticalBox, 'SideBody')
vbox_add(main, body, fill=True)
tabs = t.obj(unreal.HorizontalBox, 'TabRow')
for i, (key, label) in enumerate(SPEC['tabs']):
    b = button(t, 'Tab_' + key, label, 'tab', 14)
    hbox_add(tabs, sized(t, 'TabBox_' + key, b, height=42), (0 if i == 0 else 6, 0, 0, 0), fill=1.0)
vbox_add(body, tabs, (14, 12, 14, 4))
pages = t.obj(unreal.WidgetSwitcher, 'Pages', True)
vbox_add(body, pages, (14, 10, 14, 12), fill=True)

def page(name):
    box = t.obj(unreal.VerticalBox, 'Page_' + name)
    pages.add_child(box)
    return box

# PLAYER
p = page('Player')
vbox_add(p, section(t, 'Sec_Cheats', 'CHEATS  -  click to switch on or off'), (5, 0, 0, 4))
vbox_add(p, grid(t, 'ToggleGrid', [toggle(t, k, lbl, tip) for k, lbl, tip in SPEC['toggles']], 2, 5, 50))
vbox_add(p, section(t, 'Sec_Actions', 'QUICK ACTIONS  -  press 1-0 or scroll to pick the item in your hand'), (5, 14, 0, 4))
vbox_add(p, grid(t, 'ActionGrid', [button(t, 'A_' + k, lbl, tip=tip) for k, lbl, tip in SPEC['actions']], 2, 5, 46))

# SURVIVAL
p = page('Survival')
vbox_add(p, sized(t, 'RestoreSize', button(t, 'S_RestoreAll', 'RESTORE EVERYTHING', 'good', 17, SPEC['restore_tip']), height=54), (5, 0, 5, 6))
vbox_add(p, text(t, 'RestoreHint', 'Heals you, fills every need and clears radiation.', 12, False, 'dim'), (6, 0, 0, 14))
vbox_add(p, section(t, 'Sec_Stats', 'STATS'), (5, 0, 0, 6))
for key, label, actions, color in SPEC['stats']:
    r = t.obj(unreal.HorizontalBox, 'StatLine_' + key)
    top = t.obj(unreal.HorizontalBox, 'StatTop_' + key)
    hbox_add(top, text(t, 'StatLabel_' + key, label, 15, True), fill=1.0, valign=unreal.VerticalAlignment.V_ALIGN_CENTER)
    bar = t.obj(unreal.ProgressBar, 'Bar_' + key, True)
    bar.set_fill_color_and_opacity(unreal.LinearColor(*color))
    bst = bar.get_editor_property('widget_style')
    bst.set_editor_property('background_image', brush(C['track'], 4))
    fill_brush = brush(unreal.LinearColor(1, 1, 1, 1), 4)
    bst.set_editor_property('fill_image', fill_brush)
    bar.set_editor_property('widget_style', bst)
    bar.set_percent(.5)
    hbox_add(r, sized(t, 'BarSize_' + key, bar, height=14), (0, 0, 10, 0), fill=1.0, valign=unreal.VerticalAlignment.V_ALIGN_CENTER)
    hbox_add(top, text(t, 'Val_' + key, '- / -', 13, False, 'dim', var=True), valign=unreal.VerticalAlignment.V_ALIGN_CENTER)
    for suffix, lbl, _ in actions:
        hbox_add(r, sized(t, f'S_{key}_{suffix}_Size', button(t, f'S_{key}_{suffix}', lbl, 'good' if suffix == 'Max' else 'button', 13), width=84 if suffix == 'Max' else 54, height=34), (6, 0, 0, 0), valign=unreal.VerticalAlignment.V_ALIGN_CENTER)
    blk = t.obj(unreal.VerticalBox, 'StatBlock_' + key)
    vbox_add(blk, top, (0, 0, 0, 2))
    vbox_add(blk, r)
    vbox_add(p, blk, (5, 4, 5, 10))

# ITEMS
p = page('Items')
r = t.obj(unreal.HorizontalBox, 'SearchRow')
search = t.obj(unreal.EditableTextBox, 'ItemSearch', True)
search.set_hint_text(SPEC['search_hint'])
sst = search.get_editor_property('widget_style')
sst.set_editor_property('background_image_normal', brush(C['field'], 5, C['outline'], 1.0))
sst.set_editor_property('background_image_hovered', brush(C['field'], 5, C['accent'], 1.0))
sst.set_editor_property('background_image_focused', brush(C['field'], 5, C['accent'], 1.0))
ts = sst.get_editor_property('text_style')
ts.set_editor_property('font', font(16))
sst.set_editor_property('text_style', ts)
sst.set_editor_property('foreground_color', unreal.SlateColor(specified_color=C['text']))
sst.set_editor_property('padding', unreal.Margin(12, 10, 12, 10))
search.set_editor_property('widget_style', sst)
hbox_add(r, search, (0, 0, 8, 0), fill=1.0)
hbox_add(r, sized(t, 'SearchGoSize', button(t, 'ItemSearchGo', 'SEARCH', 'accent_btn', 14), width=96))
vbox_add(p, r, (0, 0, 0, 6))
vbox_add(p, text(t, 'SearchHint', 'Press Enter or SEARCH, then click a result to select it.', 12, False, 'dim'), (2, 0, 0, 8))
results_bg = panel(t, 'ResultsBg', 'well', (6, 6, 6, 6), 6)
scroll = t.obj(unreal.ScrollBox, 'ResultsScroll')
results = t.obj(unreal.VerticalBox, 'ItemResults', True)
scroll.add_child(results)
results_bg.set_content(scroll)
vbox_add(p, results_bg, fill=True)
sel = t.obj(unreal.HorizontalBox, 'SelectedRow')
hbox_add(sel, text(t, 'SelectedLabel', 'Selected:', 14, True, 'dim'), (0, 0, 8, 0), valign=unreal.VerticalAlignment.V_ALIGN_CENTER)
hbox_add(sel, text(t, 'SelectedItemName', 'nothing yet', 15, True, 'accent', var=True), (0, 0, 8, 0), valign=unreal.VerticalAlignment.V_ALIGN_CENTER)
hbox_add(sel, text(t, 'SelectedItemId', '', 12, False, 'dim', var=True), fill=1.0, valign=unreal.VerticalAlignment.V_ALIGN_CENTER)
vbox_add(p, sel, (2, 10, 0, 6))
qrow = t.obj(unreal.HorizontalBox, 'QtyRow')
hbox_add(qrow, text(t, 'QtyLabel', 'Amount', 14, True, 'dim'), (0, 0, 10, 0), valign=unreal.VerticalAlignment.V_ALIGN_CENTER)
qty = t.obj(unreal.EditableTextBox, 'ItemQty', True)
qty.set_text('1')
qst = qty.get_editor_property('widget_style')
qst.set_editor_property('background_image_normal', brush(C['field'], 5, C['outline'], 1.0))
qst.set_editor_property('background_image_hovered', brush(C['field'], 5, C['accent'], 1.0))
qst.set_editor_property('background_image_focused', brush(C['field'], 5, C['accent'], 1.0))
ts = qst.get_editor_property('text_style')
ts.set_editor_property('font', font(15, True))
qst.set_editor_property('text_style', ts)
qst.set_editor_property('foreground_color', unreal.SlateColor(specified_color=C['text']))
qst.set_editor_property('padding', unreal.Margin(10, 7, 10, 7))
qty.set_editor_property('widget_style', qst)
hbox_add(qrow, sized(t, 'QtySize', qty, width=70), (0, 0, 8, 0), valign=unreal.VerticalAlignment.V_ALIGN_CENTER)
for n in SPEC['quantities']:
    hbox_add(qrow, sized(t, f'Q_{n}_Size', button(t, f'Q_{n}', str(n), 'button', 13), height=36), (0, 0, 5, 0), fill=1.0, valign=unreal.VerticalAlignment.V_ALIGN_CENTER)
vbox_add(p, qrow, (2, 0, 0, 10))
arow = t.obj(unreal.HorizontalBox, 'GiveRow')
hbox_add(arow, sized(t, 'GiveSize', button(t, 'I_Give', 'ADD TO INVENTORY', 'good', 14), height=46), (0, 0, 8, 0), fill=1.0)
hbox_add(arow, sized(t, 'DropSize', button(t, 'I_Drop', 'DROP AT MY FEET', 'button', 14), height=46), fill=1.0)
vbox_add(p, arow)

# WORLD
p = page('World')
vbox_add(p, section(t, 'Sec_Time', 'TIME'), (5, 0, 0, 4))
time_items = [button(t, 'W_' + k, lbl, tip=tip) for k, lbl, tip in SPEC['time']]
time_items.append(toggle(t, 'DayNight', 'Day / night cycle', 'Pause or resume the clock. ON means time passes normally.'))
vbox_add(p, grid(t, 'TimeGrid', time_items, 2, 5, 46))
vbox_add(p, section(t, 'Sec_Weather', 'WEATHER EVENTS  -  start one now'), (5, 14, 0, 4))
vbox_add(p, grid(t, 'WeatherGrid', [button(t, 'WX_' + k, lbl, 'clear' if k == 'Clear' else 'button') for k, lbl in SPEC['weather']], 2, 5, 46))

# ALL: every built-in command, like the editor's cheat menu
def field(name, hint, size=15):
    e = t.obj(unreal.EditableTextBox, name, True)
    e.set_hint_text(hint)
    st = e.get_editor_property('widget_style')
    st.set_editor_property('background_image_normal', brush(C['field'], 5, C['outline'], 1.0))
    st.set_editor_property('background_image_hovered', brush(C['field'], 5, C['accent'], 1.0))
    st.set_editor_property('background_image_focused', brush(C['field'], 5, C['accent'], 1.0))
    ts = st.get_editor_property('text_style')
    ts.set_editor_property('font', font(size))
    st.set_editor_property('text_style', ts)
    st.set_editor_property('foreground_color', unreal.SlateColor(specified_color=C['text']))
    st.set_editor_property('padding', unreal.Margin(10, 7, 10, 7))
    e.set_editor_property('widget_style', st)
    return e

def well(name, list_name):
    bg = panel(t, name + 'Bg', 'well', (5, 5, 5, 5), 6)
    sc = t.obj(unreal.ScrollBox, name + 'Scroll')
    sc.add_child(t.obj(unreal.VerticalBox, list_name, True))
    bg.set_content(sc)
    return bg

p = page('All')
r = t.obj(unreal.HorizontalBox, 'CmdSearchRow')
hbox_add(r, field('CmdSearch', SPEC['cmd_search_hint'], 16), (0, 0, 8, 0), fill=1.0)
hbox_add(r, sized(t, 'CmdSearchGoSize', button(t, 'CmdSearchGo', 'SEARCH', 'accent_btn', 14), width=96))
vbox_add(p, r, (0, 0, 0, 6))
vbox_add(p, well('CmdList', 'CmdResults'), (0, 0, 0, 8), fill=True)
info = panel(t, 'CmdInfo', 'header', (12, 8, 12, 8), 6)
istack = t.obj(unreal.VerticalBox, 'CmdInfoStack')
vbox_add(istack, text(t, 'CmdName', 'Pick a command above', 16, True, 'accent', var=True))
cd = text(t, 'CmdDesc', 'Every cheat from the Mod Editor menu. Click one to see its options.', 12, False, 'dim', var=True)
cd.set_auto_wrap_text(True)
vbox_add(istack, cd, (0, 2, 0, 0))
cs = text(t, 'CmdState', '', 12, True, 'text', var=True)
cs.set_visibility(unreal.SlateVisibility.COLLAPSED)
vbox_add(istack, cs, (0, 4, 0, 0))
ck = text(t, 'CmdKey', '', 8, False, 'dim', var=True)
ck.set_visibility(unreal.SlateVisibility.COLLAPSED)
vbox_add(istack, ck)
info.set_content(istack)
vbox_add(p, info, (0, 0, 0, 6))
for n, hint, weight in [(1, 'Type to filter, or click an option below', 0.9), (2, 'Type a value or click an option below', 0.6)]:
    blk = t.obj(unreal.VerticalBox, f'CmdP{n}Block', True)
    vbox_add(blk, text(t, f'CmdP{n}Label', 'Option', 13, True, 'dim', var=True), (2, 0, 0, 3))
    vbox_add(blk, field(f'CmdP{n}', hint), (0, 0, 0, 4))
    vbox_add(blk, well(f'CmdOpts{n}', f'CmdOptions{n}'), fill=True)
    blk.set_visibility(unreal.SlateVisibility.COLLAPSED)
    s = vbox_add(p, blk, (0, 0, 0, 6))
    s.set_size(unreal.SlateChildSize(weight, unreal.SlateSizeRule.FILL))
vbox_add(p, sized(t, 'CmdRunSize', button(t, 'CmdRun', 'RUN', 'good', 16), height=48))

# footer
foot = panel(t, 'Footer', 'header', (22, 10, 22, 10), 10)
frow = t.obj(unreal.VerticalBox, 'FooterStack')
status = text(t, 'StatusText', 'Ready.', 14, True, 'accent', var=True)
status.set_auto_wrap_text(True)
vbox_add(frow, status, (0, 0, 0, 2))
vbox_add(frow, text(t, 'VersionText', SPEC['host_note'] + '   |   v' + SPEC['version'], 11, False, 'dim'))
foot.set_content(frow)
vbox_add(main, foot)

compile_save(wb)
cdo = unreal.get_default_object(wb.generated_class())
cdo.set_editor_property('is_focusable', True)
cdo.set_editor_property('priority', 10)
cdo.set_editor_property('stop_action', True)  # blocks game input below the menu; the buff/remote input sits above it
assert unreal.EditorAssetLibrary.save_loaded_asset(wb, False)
print('BUILT_MENU_08', len(t.made), 'widgets;', 'entries ok')
