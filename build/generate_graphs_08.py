"""Generates Blueprint clipboard text for the v0.8 menu: the four tabs plus ALL, which runs any of the copied built-in commands.
Output: graphs/menu-08-pass1..5.txt, pasted into W_DirectorMenu's event graph in that order (see README)."""
import json, sys, uuid
from pathlib import Path

ROOT = Path(__file__).parent
RUN = sys.argv[1] if len(sys.argv) > 1 else 'CM08'  # node-name prefix; use a new one per paste so leftovers are told apart
P = 'ResearchDirectorI7yTl'
SPEC = json.loads((ROOT / 'menu-spec-08.json').read_text())
CMDS = json.loads((ROOT / 'commands-08.json').read_text())['commands']
CLASSES = json.loads((ROOT / 'commands-08-classes.json').read_text())['classes']
MENU = f'/{P}/Widgets/W_DirectorMenu.W_DirectorMenu_C'
ENTRY = f'/{P}/Widgets/W_DirectorItemEntry.W_DirectorItemEntry_C'
CENTRY = f'/{P}/Widgets/W_DirectorCmdEntry.W_DirectorCmdEntry_C'
PAWN = '/Game/Blueprints/Characters/Abiotic_PlayerCharacter.Abiotic_PlayerCharacter_C'
DAYNIGHT = '/Game/Blueprints/Environment/Systems/DayNightManager.DayNightManager_C'
GCO = '/Script/AbioticFactor.GameCommandObject'
FOREACH = ('MacroGraphReference=(MacroGraph="/Script/Engine.EdGraph\'/Engine/EditorBlueprintResources/StandardMacros.StandardMacros:ForEachLoop\'",'
           'GraphBlueprint="/Script/Engine.Blueprint\'/Engine/EditorBlueprintResources/StandardMacros.StandardMacros\'",GraphGuid=99DBFD5540A796041F72A5A9DA655026)')
UMG, KML, KSL, KTL, GS = '/Script/UMG', '/Script/Engine.KismetMathLibrary', '/Script/Engine.KismetStringLibrary', '/Script/Engine.KismetTextLibrary', '/Script/Engine.GameplayStatics'
WBL = '/Script/UMG.WidgetBlueprintLibrary'

def cmd(name):
    return f'/{P}/Commands/BP_Director{name}.BP_Director{name}_C'

def cls(path):
    return '"/Script/CoreUObject.Class\'' + path + '\'"'

def color(key):
    r, g, b, a = SPEC['colors'][key]
    return f'(R={r},G={g},B={b},A={a})'

class Graph:
    def __init__(self):
        self.nodes = []
        self.x = 0
        self.y = 0
        self.part = 1

    def node(self, kind, props=''):
        n = {'name': f'{RUN}_{len(self.nodes)}', 'kind': kind, 'props': props, 'pins': [], 'x': self.x, 'y': self.y, 'part': self.part}
        self.x += 320
        self.nodes.append(n)
        return n

    def row(self):
        self.x = 0
        self.y += 420

    def pin(self, n, name, cat='exec', out=False, obj=None, default=None, defaultobj=None, sub=None, array=False):
        p = {'id': uuid.uuid4().hex.upper(), 'name': name, 'cat': cat, 'out': out, 'obj': obj, 'default': default,
             'defaultobj': defaultobj, 'sub': sub, 'array': array, 'links': [], 'node': n}
        n['pins'].append(p)
        return p

    def get(self, n, name):
        return next(p for p in n['pins'] if p['name'] == name)

    def link(self, a, b):
        a['links'].append(b)
        b['links'].append(a)

    # value pins: either a literal default or a linked output pin
    def feed(self, n, name, value, cat, obj=None, sub=None, array=False):
        if isinstance(value, dict):
            p = self.pin(n, name, cat, obj=obj, sub=sub, array=array)
            self.link(value, p)
        elif value is not None:
            p = self.pin(n, name, cat, obj=obj, sub=sub, default=value)
        else:
            p = self.pin(n, name, cat, obj=obj, sub=sub)
        return p

    def call(self, owner, fn, exec=True, target=None, target_cls=None, args=(), out=None, kind='K2Node_CallFunction'):
        """args: (pin, value, cat[, obj]) ; out: (pin, cat[, obj]) -> returns (node, outpin)"""
        n = self.node(f'/Script/BlueprintGraph.{kind}',
                      f'FunctionReference=(MemberParent={cls(owner)},MemberName="{fn}")' + ('' if exec else '\nbIsPureFunc=True'))
        if exec:
            self.pin(n, 'execute')
            self.pin(n, 'then', out=True)
        if target is not None:
            self.feed(n, 'self', target, 'object', target_cls or owner)
        for a in args:
            self.feed(n, a[0], a[1], a[2], a[3] if len(a) > 3 else None, a[4] if len(a) > 4 else None)
        o = None
        if out:
            o = self.pin(n, out[0], out[1], True, out[2] if len(out) > 2 else None, sub=out[3] if len(out) > 3 else None,
                         array=out[4] if len(out) > 4 else False)
        return n, o

    def call_self(self, fn, args=()):
        n = self.node('/Script/BlueprintGraph.K2Node_CallFunction', f'FunctionReference=(MemberName="{fn}",bSelfContext=True)')
        self.pin(n, 'execute')
        self.pin(n, 'then', out=True)
        for a in args:
            self.feed(n, a[0], a[1], a[2], a[3] if len(a) > 3 else None, array=a[4] if len(a) > 4 else False)
        return n

    def delegate(self, fn):
        n = self.node('/Script/BlueprintGraph.K2Node_CreateDelegate', f'SelectedFunctionName="{fn}"')
        self.pin(n, 'self', 'object', obj='/Script/CoreUObject.Object')
        return self.pin(n, 'OutputDelegate', 'delegate', True)

    def custom_event(self, name, params=()):
        lines = [f'CustomFunctionName="{name}"']
        n = self.node('/Script/BlueprintGraph.K2Node_CustomEvent', '')
        self.pin(n, 'OutputDelegate', 'delegate', True)
        self.pin(n, 'then', out=True)
        outs = {}
        for pname, cat, obj, *array in params:
            array = bool(array and array[0])
            outs[pname] = self.pin(n, pname, cat, True, obj, array=array)
            sub = f',PinSubCategoryObject={cls(obj)}' if obj else ''
            container = ',ContainerType=Array' if array else ''
            lines.append(f'CustomProperties UserDefinedPin (PinName="{pname}",PinType=(PinCategory="{cat}"{sub}{container}),DesiredPinDirection=EGPD_Output)')
        n['props'] = '\n'.join(lines)
        return n, outs

    def event(self, owner, fn):
        n = self.node('/Script/BlueprintGraph.K2Node_Event',
                      f'EventReference=(MemberParent={cls(owner)},MemberName="{fn}")\nbOverrideFunction=True')
        self.pin(n, 'OutputDelegate', 'delegate', True)
        self.pin(n, 'then', out=True)
        return n

    def bound(self, widget, owner='/Script/UMG.Button', delegate='OnClicked', sig='OnButtonClickedEvent__DelegateSignature'):
        n = self.node('/Script/BlueprintGraph.K2Node_ComponentBoundEvent',
                      f'DelegatePropertyName="{delegate}"\nDelegateOwnerClass={cls(owner)}\nComponentPropertyName="{widget}"\n'
                      f'EventReference=(MemberParent="/Script/CoreUObject.Package\'/Script/UMG\'",MemberName="{sig}")\n'
                      f'bInternalEvent=True\nCustomFunctionName="BndEvt__{RUN}_{widget}_{delegate}"')
        self.pin(n, 'OutputDelegate', 'delegate', True)
        self.pin(n, 'then', out=True)
        return n

    def var(self, name, obj, owner=None, target=None, cat='object', sub=None):
        if owner:
            n = self.node('/Script/BlueprintGraph.K2Node_VariableGet', f'VariableReference=(MemberParent={cls(owner)},MemberName="{name}")')
            self.feed(n, 'self', target, 'object', owner)
        else:
            n = self.node('/Script/BlueprintGraph.K2Node_VariableGet', f'VariableReference=(MemberName="{name}",bSelfContext=True)')
        return self.pin(n, name, cat, True, obj, sub=sub)

    def set_var(self, owner, name, target, value, cat='bool'):
        n = self.node('/Script/BlueprintGraph.K2Node_VariableSet', f'VariableReference=(MemberParent={cls(owner)},MemberName="{name}")')
        self.pin(n, 'execute')
        self.pin(n, 'then', out=True)
        self.feed(n, 'self', target, 'object', owner)
        self.feed(n, name, value, cat)
        return n

    def cast(self, obj, target, as_name):
        n = self.node('/Script/BlueprintGraph.K2Node_DynamicCast', 'TargetType=' + cls(target))
        self.pin(n, 'execute')
        self.pin(n, 'then', out=True)
        self.pin(n, 'CastFailed', out=True)
        self.feed(n, 'Object', obj, 'object', '/Script/CoreUObject.Object')
        o = self.pin(n, as_name, 'object', True, target)
        self.pin(n, 'bSuccess', 'bool', True)
        return n, o

    def branch(self, cond):
        n = self.node('/Script/BlueprintGraph.K2Node_IfThenElse')
        self.pin(n, 'execute')
        self.feed(n, 'Condition', cond, 'bool')
        self.pin(n, 'then', out=True)
        self.pin(n, 'else', out=True)
        return n

    def foreach(self, array, elem_cat, elem_obj=None):
        wild = f'ResolvedWildcardType=(PinCategory="{elem_cat}"' + (f',PinSubCategoryObject={cls(elem_obj)}' if elem_obj else '') + ')'
        n = self.node('/Script/BlueprintGraph.K2Node_MacroInstance', FOREACH + '\n' + wild)
        self.pin(n, 'Exec')
        self.feed(n, 'Array', array, elem_cat, elem_obj, array=True)
        self.pin(n, 'LoopBody', out=True)
        el = self.pin(n, 'Array Element', elem_cat, True, elem_obj)
        self.pin(n, 'Array Index', 'int', True)
        self.pin(n, 'Completed', out=True)
        return n, el

    # --- small value helpers (pure)
    def s2t(self, s):
        return self.call(KTL, 'Conv_StringToText', False, args=[('InString', s, 'string')], out=('ReturnValue', 'text'))[1]

    def t2s(self, t):
        return self.call(KTL, 'Conv_TextToString', False, args=[('InText', t, 'text')], out=('ReturnValue', 'string'))[1]

    def concat(self, a, b):
        return self.call(KSL, 'Concat_StrStr', False, args=[('A', a, 'string'), ('B', b, 'string')], out=('ReturnValue', 'string'))[1]

    def owning_player(self):
        return self.call('/Script/UMG.UserWidget', 'GetOwningPlayer', False, out=('ReturnValue', 'object', '/Script/Engine.PlayerController'))[1]

    def chain(self, *nodes):
        for a, b in zip(nodes, nodes[1:]):
            self.link(self.get(a, 'then'), self.get(b, 'execute') if any(p['name'] == 'execute' for p in b['pins']) else self.get(b, 'Exec'))
        return nodes[-1]

    def write(self, path):
        for n in self.nodes:
            for p in n['pins']:
                for b in p['links']:
                    assert b['node']['part'] == n['part'], (n['name'], p['name'], b['node']['name'])
        parts = sorted({n['part'] for n in self.nodes})
        for part in parts:
            self.write_part(path.with_name(f'{path.stem}-pass{part}.txt'), [n for n in self.nodes if n['part'] == part])
        return len(self.nodes)

    def write_part(self, path, nodes):
        chunks = []
        for n in nodes:
            chunks.append(f'Begin Object Class={n["kind"]} Name="{n["name"]}"\n' + (n['props'] + '\n' if n['props'] else '') +
                          f'NodePosX={n["x"]}\nNodePosY={n["y"]}\nNodeGuid={uuid.uuid4().hex.upper()}')
            for p in n['pins']:
                s = f'CustomProperties Pin (PinId={p["id"]},PinName="{p["name"]}",'
                if p['out']:
                    s += 'Direction="EGPD_Output",'
                s += f'PinType.PinCategory="{p["cat"]}",PinType.PinSubCategory="{p["sub"] or ""}",PinType.PinSubCategoryObject='
                if p['obj'] and p['cat'] in ('object', 'class', 'softobject'):
                    s += cls(p['obj'])
                elif p['obj'] and p['obj'].startswith('enum:'):
                    s += '"/Script/CoreUObject.Enum\'' + p['obj'][5:] + '\'"'
                elif p['obj'] and p['obj'].startswith('uds:'):
                    s += '"/Script/Engine.UserDefinedStruct\'' + p['obj'][4:] + '\'"'
                elif p['obj']:
                    s += '"/Script/CoreUObject.ScriptStruct\'' + p['obj'] + '\'"'
                else:
                    s += 'None'
                s += ',PinType.ContainerType=' + ('Array' if p['array'] else 'None') + ','
                if p['default'] is not None:
                    s += 'DefaultValue=' + json.dumps(str(p['default'])) + ','
                if p['defaultobj']:
                    s += 'DefaultObject=' + p['defaultobj'] + ','
                if p['links']:
                    s += 'LinkedTo=(' + ''.join(f'{b["node"]["name"]} {b["id"]},' for b in p['links']) + '),'
                s += 'bHidden=False,bOrphanedPin=False,)'
                chunks.append(s)
            chunks.append('End Object')
        path.parent.mkdir(exist_ok=True)
        path.write_text('\n'.join(chunks) + '\n', encoding='utf-8')
        return len(self.nodes)

# ====================================================================== menu graph
g = Graph()
TEXTBLOCK, BUTTON, ETB = '/Script/UMG.TextBlock', '/Script/UMG.Button', '/Script/UMG.EditableTextBox'

def set_text(widget_pin, text_pin, owner=TEXTBLOCK):
    return g.call(owner, 'SetText', target=widget_pin, args=[('InText', text_pin, 'text')])[0]

def status(msg):
    return set_text(g.var('StatusText', TEXTBLOCK), g.s2t(msg) if isinstance(msg, str) else g.s2t(msg))

# --- custom events (declared first so calls can resolve)
close_ev, _ = g.custom_event('CloseMenu')
g.row()
tab_ev, tab_args = g.custom_event('SelectTab', [('Index', 'int', None)])
g.row()
g.part = 2
run_ev, run = g.custom_event('RunCommand', [('Cmd', 'class', GCO), ('P1', 'string', None), ('P2', 'string', None), ('Label', 'string', None)])
g.row()
g.part = 1
refresh_ev, _ = g.custom_event('Refresh')
g.row()
search_ev, _ = g.custom_event('SearchItems')
g.row()
pick_ev, _ = g.custom_event('PickItem')
g.row()

# --- CloseMenu
pc = g.owning_player()
remove = g.call('/Script/UMG.Widget', 'RemoveFromParent')[0]
mode = g.call(WBL, 'SetInputMode_GameOnly', args=[('PlayerController', pc, 'object', '/Script/Engine.PlayerController'), ('bFlushInput', 'true', 'bool')])[0]
cursor = g.set_var('/Script/Engine.PlayerController', 'bShowMouseCursor', pc, 'false')
g.chain(close_ev, remove, mode, cursor)
g.row()

# --- Construct
g.part = 5
construct = g.event('/Script/UMG.UserWidget', 'Construct')
pc = g.owning_player()
selfpin = g.pin(g.node('/Script/BlueprintGraph.K2Node_Self'), 'self', 'object', True, '/Script/CoreUObject.Object')
mode = g.call(WBL, 'SetInputMode_GameAndUIEx', args=[('PlayerController', pc, 'object', '/Script/Engine.PlayerController'),
                                                     ('InWidgetToFocus', selfpin, 'object', '/Script/UMG.Widget'),
                                                     ('bHideCursorDuringCapture', 'false', 'bool'), ('bFlushInput', 'true', 'bool')])[0]
cursor = g.set_var('/Script/Engine.PlayerController', 'bShowMouseCursor', pc, 'true')
listen = g.call('/Script/UMG.UserWidget', 'ListenForInputAction', args=[('ActionName', 'EscapeMenu', 'name'), ('EventType', 'IE_Pressed', 'byte'),
                                                                        ('bConsume', 'true', 'bool'), ('Callback', g.delegate('CloseMenu'), 'delegate')])[0]
# Hotbar keys and the wheel still pick the item in your hand while the menu is open (the KeySlot/KeyNext/KeyPrev events are below).
HOTKEYS = [(f'HotbarSlot{i}', f'KeySlot{i}') for i in range(1, 11)] + [('NextHotbarItem', 'KeyNext'), ('PreviousHotbarItem', 'KeyPrev')]
hot = [g.call('/Script/UMG.UserWidget', 'ListenForInputAction', args=[('ActionName', action, 'name'), ('EventType', 'IE_Pressed', 'byte'),
                                                                     ('bConsume', 'true', 'bool'), ('Callback', g.delegate(ev), 'delegate')])[0]
       for action, ev in HOTKEYS]
tab0 = g.call_self('SelectTab', [('Index', '0', 'int')])
refresh_call = g.call_self('Refresh')
search_call = g.call_self('SearchItems')
cmd_call = g.call_self('SearchCommands')
ready = status('Ready. Pick a tab above.')
g.chain(construct, mode, cursor, listen, *hot, tab0, refresh_call, search_call, cmd_call, ready)
g.row()

# --- close button
g.chain(g.bound('CloseButton'), g.call_self('CloseMenu'))
g.row()

# --- SelectTab
g.part = 1
idx = tab_args['Index']
nodes = [tab_ev, g.call('/Script/UMG.WidgetSwitcher', 'SetActiveWidgetIndex', target=g.var('Pages', '/Script/UMG.WidgetSwitcher'), args=[('Index', idx, 'int')])[0]]
for i, (key, _) in enumerate(SPEC['tabs']):
    eq = g.call(KML, 'EqualEqual_IntInt', False, args=[('A', idx, 'int'), ('B', str(i), 'int')], out=('ReturnValue', 'bool'))[1]
    col = g.call(KML, 'SelectColor', False, args=[('A', color('tab_on'), 'struct', '/Script/CoreUObject.LinearColor'), ('B', color('tab'), 'struct', '/Script/CoreUObject.LinearColor'), ('bPickA', eq, 'bool')],
                 out=('ReturnValue', 'struct', '/Script/CoreUObject.LinearColor'))[1]
    nodes.append(g.call(BUTTON, 'SetBackgroundColor', target=g.var('Tab_' + key, BUTTON), args=[('InBackgroundColor', col, 'struct', '/Script/CoreUObject.LinearColor')])[0])
g.chain(*nodes)
g.row()
g.part = 5
for i, (key, _) in enumerate(SPEC['tabs']):
    g.chain(g.bound('Tab_' + key), g.call_self('SelectTab', [('Index', str(i), 'int')]))
    g.row()

# --- RunCommand
g.part = 2
pc = g.owning_player()
castn, castpc = g.cast(pc, '/Script/AbioticFactor.AbioticPlayerController', 'AsAbiotic Player Controller')
auth = g.call('/Script/Engine.Actor', 'HasAuthority', False, target=pc, out=('ReturnValue', 'bool'))[1]
br = g.branch(auth)
make = g.node('/Script/BlueprintGraph.K2Node_GenericCreateObject')
g.pin(make, 'execute')
g.pin(make, 'then', out=True)
g.feed(make, 'Class', run['Cmd'], 'class', GCO)
g.feed(make, 'Outer', g.pin(g.node('/Script/BlueprintGraph.K2Node_Self'), 'self', 'object', True, '/Script/CoreUObject.Object'), 'object', '/Script/CoreUObject.Object')
made = g.pin(make, 'ReturnValue', 'object', True, GCO)
execn = g.call(GCO, 'OnCommandExecuted', target=made, args=[('Player', castpc, 'object', '/Script/AbioticFactor.AbioticPlayerController'),
                                                            ('FirstParam', run['P1'], 'string'), ('SecondParam', run['P2'], 'string')])[0]
refresh_call = g.call_self('Refresh')
done = set_text(g.var('StatusText', TEXTBLOCK), g.s2t(run['Label']))
g.link(g.get(run_ev, 'then'), g.get(castn, 'execute'))
g.link(g.get(castn, 'then'), g.get(br, 'execute'))
g.link(g.get(br, 'then'), g.get(make, 'execute'))
g.chain(make, execn, refresh_call, done)
denied = status('Only the host (or single player) can use cheats.')
g.link(g.get(br, 'else'), g.get(denied, 'execute'))
g.row()

def run_cmd(name, p1='', p2='', label=''):
    return g.call_self('RunCommand', [('Cmd', None, 'class', GCO), ('P1', p1, 'string'), ('P2', p2, 'string'), ('Label', label, 'string')])

def run_literal(name, p1='', p2='', label=''):
    n = run_cmd(name, p1, p2, label)
    pin = g.get(n, 'Cmd')
    pin['defaultobj'] = f'"/Script/Engine.BlueprintGeneratedClass\'{cmd(name)}\'"'
    return n

def run_dynamic(name, p1, p2, label):
    n = g.call_self('RunCommand', [('Cmd', None, 'class', GCO), ('P1', p1, 'string'), ('P2', p2, 'string'), ('Label', label, 'string')])
    g.get(n, 'Cmd')['defaultobj'] = f'"/Script/Engine.BlueprintGeneratedClass\'{cmd(name)}\'"'
    return n

# --- Refresh
g.part = 1
pawn = g.call('/Script/UMG.UserWidget', 'GetOwningPlayerPawn', False, out=('ReturnValue', 'object', '/Script/Engine.Pawn'))[1]
pcast, ppawn = g.cast(pawn, PAWN, 'AsAbiotic Player Character')
chain = [refresh_ev, pcast]
STATE = {'GodMode': ('Invincible', False), 'InfiniteStamina': ('InfiniteStamina', False), 'InfiniteAmmo': ('InfiniteAmmo', False),
         'FreeCrafting': ('Debug_FreeCrafting', False), 'DisableStateDrain': ('IsStateDrainDisabled', False),
         'NPCsIgnorePlayer': ('NPC_Targetable', True), 'Ghost': ('GhostMode', False), 'MasterKey': ('HasMasterKey', False)}

def show_state(key, value):
    on = g.call(KML, 'SelectString', False, args=[('A', 'ON', 'string'), ('B', 'OFF', 'string'), ('bPickA', value, 'bool')], out=('ReturnValue', 'string'))[1]
    a = set_text(g.var('TS_' + key, TEXTBLOCK), g.s2t(on))
    col = g.call(KML, 'SelectColor', False, args=[('A', color('toggle_on'), 'struct', '/Script/CoreUObject.LinearColor'), ('B', color('toggle_off'), 'struct', '/Script/CoreUObject.LinearColor'), ('bPickA', value, 'bool')],
                 out=('ReturnValue', 'struct', '/Script/CoreUObject.LinearColor'))[1]
    b = g.call(BUTTON, 'SetBackgroundColor', target=g.var('T_' + key, BUTTON), args=[('InBackgroundColor', col, 'struct', '/Script/CoreUObject.LinearColor')])[0]
    return [a, b]

for key, _, _ in SPEC['toggles']:
    prop, invert = STATE[key]
    v = g.var(prop, None, PAWN, ppawn, 'bool')
    if invert:
        v = g.call(KML, 'Not_PreBool', False, args=[('A', v, 'bool')], out=('ReturnValue', 'bool'))[1]
    chain += show_state(key, v)
for key, *_ in SPEC['stats']:
    cur = g.var('Current' + key, None, PAWN, ppawn, 'real', 'double')
    mx = g.var('Max' + key, None, PAWN, ppawn, 'real', 'double')
    pct = g.call(KML, 'Divide_DoubleDouble', False, args=[('A', cur, 'real', None, 'double'), ('B', mx, 'real', None, 'double')], out=('ReturnValue', 'real', None, 'double'))[1]
    chain.append(g.call('/Script/UMG.ProgressBar', 'SetPercent', target=g.var('Bar_' + key, '/Script/UMG.ProgressBar'), args=[('InPercent', pct, 'real', None, 'float')])[0])
    rc = g.call(KML, 'Round', False, args=[('A', cur, 'real', None, 'double')], out=('ReturnValue', 'int'))[1]
    rm = g.call(KML, 'Round', False, args=[('A', mx, 'real', None, 'double')], out=('ReturnValue', 'int'))[1]
    sc = g.call(KSL, 'Conv_IntToString', False, args=[('InInt', rc, 'int')], out=('ReturnValue', 'string'))[1]
    sm = g.call(KSL, 'Conv_IntToString', False, args=[('InInt', rm, 'int')], out=('ReturnValue', 'string'))[1]
    chain.append(set_text(g.var('Val_' + key, TEXTBLOCK), g.s2t(g.concat(g.concat(sc, ' / '), sm))))
dn = g.call(GS, 'GetActorOfClass', True, args=[('ActorClass', None, 'class', '/Script/Engine.Actor')], out=('ReturnValue', 'object', DAYNIGHT))
g.get(dn[0], 'ActorClass')['defaultobj'] = f'"/Script/Engine.BlueprintGeneratedClass\'{DAYNIGHT}\'"'
paused = g.var('DayNightManuallyPaused', None, DAYNIGHT, dn[1], 'bool')
running = g.call(KML, 'Not_PreBool', False, args=[('A', paused, 'bool')], out=('ReturnValue', 'bool'))[1]
chain += [dn[0]] + show_state('DayNight', running)
g.chain(*chain)
g.row()

# --- toggle / action / survival / world buttons
g.part = 5
for key, label, _ in SPEC['toggles']:
    g.chain(g.bound('T_' + key), run_literal(key, label=f'Switched {label.lower()}.'))
    g.row()
for key, label, _ in SPEC['actions']:
    g.chain(g.bound('A_' + key), run_literal(key, label=f'Done: {label.lower()}.'))
    g.row()
for key, label, actions, _ in SPEC['stats']:
    for suffix, text, value in actions:
        g.chain(g.bound(f'S_{key}_{suffix}'), run_literal('Modify' + key, value, label=f'{label}: {text.lower() if suffix == "Max" else text}.'))
        g.row()
restore = [g.bound('S_RestoreAll'), run_literal('HealRevive', label='Healed.')]
for key, label, actions, _ in SPEC['stats']:
    restore.append(run_literal('Modify' + key, actions[-1][2], label='Restoring...'))
restore.append(status('Everything restored.'))
g.chain(*restore)
g.row()
TIME = {'Hour1': ('AddTimeMinutes', '60'), 'Hour6': ('AddTimeMinutes', '360'), 'Morning': ('SkipToMorning', ''), 'Night': ('SkipToNightfall', '')}
for key, label, _ in SPEC['time']:
    name, p1 = TIME[key]
    g.chain(g.bound('W_' + key), run_literal(name, p1, label=f'Time: {label.lower()}.'))
    g.row()
g.chain(g.bound('T_DayNight'), run_literal('ToggleDayNightCycle', label='Switched the day / night cycle.'))
g.row()
for key, label in SPEC['weather']:
    if key == 'Clear':
        g.chain(g.bound('WX_Clear'), run_literal('ClearWeatherEvent', label='Weather cleared.'))
    else:
        g.chain(g.bound('WX_' + key), run_literal('SetWeatherEvent', key, label=f'Weather: {label.lower()}.'))
    g.row()

# --- items: quantity buttons
for n in SPEC['quantities']:
    g.chain(g.bound(f'Q_{n}'), set_text(g.var('ItemQty', ETB), g.s2t(str(n)), ETB))
    g.row()

# --- items: give / drop
for button_name, command, verb in [('I_Give', 'SpawnItem', 'Added to inventory: '), ('I_Drop', 'SpawnItemOnGround', 'Dropped at your feet: ')]:
    ev = g.bound(button_name)
    item_id = g.t2s(g.call(TEXTBLOCK, 'GetText', False, target=g.var('SelectedItemId', TEXTBLOCK), out=('ReturnValue', 'text'))[1])
    has = g.call(KSL, 'NotEqual_StrStr', False, args=[('A', item_id, 'string'), ('B', '', 'string')], out=('ReturnValue', 'bool'))[1]
    br = g.branch(has)
    qty = g.t2s(g.call(ETB, 'GetText', False, target=g.var('ItemQty', ETB), out=('ReturnValue', 'text'))[1])
    name = g.t2s(g.call(TEXTBLOCK, 'GetText', False, target=g.var('SelectedItemName', TEXTBLOCK), out=('ReturnValue', 'text'))[1])
    label = g.concat(g.concat(verb, qty), g.concat(' x ', name))
    run_n = run_dynamic(command, item_id, qty, label)
    g.link(g.get(ev, 'then'), g.get(br, 'execute'))
    g.link(g.get(br, 'then'), g.get(run_n, 'execute'))
    g.link(g.get(br, 'else'), g.get(status('Pick an item from the search results first.'), 'execute'))
    g.row()

# --- items: search
g.chain(g.bound('ItemSearchGo'), g.call_self('SearchItems'))
g.row()
committed = g.bound('ItemSearch', ETB, 'OnTextCommitted', 'OnEditableTextBoxCommittedEvent__DelegateSignature')
g.pin(committed, 'Text', 'text', True)
g.pin(committed, 'CommitMethod', 'byte', True, '/Script/SlateCore.ETextCommit')
g.chain(committed, g.call_self('SearchItems'))
g.row()

g.part = 1
results = g.var('ItemResults', '/Script/UMG.VerticalBox')
clear = g.call('/Script/UMG.PanelWidget', 'ClearChildren', target=results)[0]
names_n, names = g.call('/Script/AbioticFactor.GlobalItemHandleFunctionLibrary', 'GetAllGlobalItemRowNames', True, out=('OutRowNames', 'name', None, None, True))
loop, elem = g.foreach(names, 'name')
count = g.call('/Script/UMG.PanelWidget', 'GetChildrenCount', False, target=g.var('ItemResults', '/Script/UMG.VerticalBox'), out=('ReturnValue', 'int'))[1]
room = g.call(KML, 'Less_IntInt', False, args=[('A', count, 'int'), ('B', '60', 'int')], out=('ReturnValue', 'bool'))[1]
br_room = g.branch(room)
handle = g.call('/Script/AbioticFactor.GlobalItemHandleFunctionLibrary', 'Conv_NameToGlobalItem', False, args=[('RowName', elem, 'name')],
                out=('ReturnValue', 'struct', '/Script/AbioticFactor.GlobalItemRowHandle'))[1]
rown = g.node('/Script/BlueprintGraph.K2Node_CallFunction',
              'FunctionReference=(MemberParent=' + cls('/Script/AbioticFactor.GlobalItemHandleFunctionLibrary') + ',MemberName="GetGlobalItemRow")')
g.pin(rown, 'execute')
g.feed(rown, 'RowHandle', handle, 'struct', '/Script/AbioticFactor.GlobalItemRowHandle')
g.pin(rown, 'Valid', out=True)
g.pin(rown, 'NotValid', out=True)
rowdata = g.pin(rown, 'Data', 'struct', True, '/Script/AbioticFactor.AbioticInventoryItem')
brk = g.node('/Script/BlueprintGraph.K2Node_BreakStruct', 'StructType="/Script/CoreUObject.ScriptStruct\'/Script/AbioticFactor.AbioticInventoryItem\'"')
g.feed(brk, 'AbioticInventoryItem', rowdata, 'struct', '/Script/AbioticFactor.AbioticInventoryItem')
item_name = g.pin(brk, 'ItemName', 'text', True)
item_icon = g.pin(brk, 'InventoryIcon', 'softobject', True, '/Script/Engine.Texture2D')
query = g.t2s(g.call(ETB, 'GetText', False, target=g.var('ItemSearch', ETB), out=('ReturnValue', 'text'))[1])
id_str = g.call(KSL, 'Conv_NameToString', False, args=[('InName', elem, 'name')], out=('ReturnValue', 'string'))[1]
m1 = g.call(KSL, 'Contains', False, args=[('SearchIn', g.t2s(item_name), 'string'), ('Substring', query, 'string')], out=('ReturnValue', 'bool'))[1]
m2 = g.call(KSL, 'Contains', False, args=[('SearchIn', id_str, 'string'), ('Substring', query, 'string')], out=('ReturnValue', 'bool'))[1]
match = g.call(KML, 'BooleanOR', False, args=[('A', m1, 'bool'), ('B', m2, 'bool')], out=('ReturnValue', 'bool'))[1]
br_match = g.branch(match)
cw = g.node('/Script/UMGEditor.K2Node_CreateWidget')
g.pin(cw, 'execute')
g.pin(cw, 'then', out=True)
g.pin(cw, 'Class', 'class', obj='/Script/UMG.UserWidget', defaultobj=f'"/Script/UMG.WidgetBlueprintGeneratedClass\'{ENTRY}\'"')
g.feed(cw, 'OwningPlayer', g.owning_player(), 'object', '/Script/Engine.PlayerController')
entry = g.pin(cw, 'ReturnValue', 'object', True, ENTRY)
s1 = set_text(g.var('EntryName', TEXTBLOCK, ENTRY, entry), item_name)
s2 = set_text(g.var('EntryId', TEXTBLOCK, ENTRY, entry), g.s2t(id_str))
s3 = g.call('/Script/UMG.Image', 'SetBrushFromSoftTexture', target=g.var('EntryIcon', '/Script/UMG.Image', ENTRY, entry), args=[('SoftTexture', item_icon, 'softobject', '/Script/Engine.Texture2D'), ('bMatchSize', 'false', 'bool')])[0]
add = g.call('/Script/UMG.VerticalBox', 'AddChildToVerticalBox', target=g.var('ItemResults', '/Script/UMG.VerticalBox'), args=[('Content', entry, 'object', '/Script/UMG.Widget')],
             out=('ReturnValue', 'object', '/Script/UMG.VerticalBoxSlot'))
slot_pad = g.call('/Script/UMG.VerticalBoxSlot', 'SetPadding', target=add[1], args=[('InPadding', '(Left=0,Top=0,Right=0,Bottom=4)', 'struct', '/Script/SlateCore.Margin')])[0]
bind = g.node('/Script/BlueprintGraph.K2Node_AddDelegate', f'DelegateReference=(MemberParent={cls(BUTTON)},MemberName="OnClicked")')
g.pin(bind, 'execute')
g.pin(bind, 'then', out=True)
g.feed(bind, 'self', g.var('EntryButton', BUTTON, ENTRY, entry), 'object', BUTTON)
g.feed(bind, 'Delegate', g.get(pick_ev, 'OutputDelegate'), 'delegate')
shown = g.call('/Script/UMG.PanelWidget', 'GetChildrenCount', False, target=g.var('ItemResults', '/Script/UMG.VerticalBox'), out=('ReturnValue', 'int'))[1]
fin = status(g.concat(g.call(KSL, 'Conv_IntToString', False, args=[('InInt', shown, 'int')], out=('ReturnValue', 'string'))[1], ' items shown. Click one to select it.'))
g.chain(search_ev, clear, names_n, loop)
g.link(g.get(loop, 'LoopBody'), g.get(br_room, 'execute'))
g.link(g.get(br_room, 'then'), g.get(rown, 'execute'))
g.link(g.get(rown, 'Valid'), g.get(br_match, 'execute'))
g.link(g.get(br_match, 'then'), g.get(cw, 'execute'))
g.chain(cw, s1, s2, s3, add[0], slot_pad, bind)
g.link(g.get(loop, 'Completed'), g.get(fin, 'execute'))
g.row()

# --- PickItem: find the hovered result
kids = g.call('/Script/UMG.PanelWidget', 'GetAllChildren', False, target=g.var('ItemResults', '/Script/UMG.VerticalBox'), out=('ReturnValue', 'object', '/Script/UMG.Widget', None, True))[1]
loop, child = g.foreach(kids, 'object', '/Script/UMG.Widget')
ecast, ent = g.cast(child, ENTRY, 'AsW Director Item Entry')
hover = g.call('/Script/UMG.Widget', 'IsHovered', False, target=g.var('EntryButton', BUTTON, ENTRY, ent), out=('ReturnValue', 'bool'))[1]
br_h = g.branch(hover)
eid = g.call(TEXTBLOCK, 'GetText', False, target=g.var('EntryId', TEXTBLOCK, ENTRY, ent), out=('ReturnValue', 'text'))[1]
ename = g.call(TEXTBLOCK, 'GetText', False, target=g.var('EntryName', TEXTBLOCK, ENTRY, ent), out=('ReturnValue', 'text'))[1]
p1 = set_text(g.var('SelectedItemId', TEXTBLOCK), eid)
p2 = set_text(g.var('SelectedItemName', TEXTBLOCK), ename)
p3 = status(g.concat('Selected ', g.t2s(ename)))
g.chain(pick_ev, loop)
g.link(g.get(loop, 'LoopBody'), g.get(ecast, 'execute'))
g.link(g.get(ecast, 'then'), g.get(br_h, 'execute'))
g.link(g.get(br_h, 'then'), g.get(p1, 'execute'))
g.chain(p1, p2, p3)

# ====================================================================== ALL tab
# Each command is one '|'-separated string: label|desc|first input|second input|value box|category|index.
# The index picks the copied command class out of a literal class array (the classes are hard references,
# so the cooker ships them). Empty input labels hide that input.
VIS = 'enum:/Script/UMG.ESlateVisibility'
VBOX, PANEL = '/Script/UMG.VerticalBox', '/Script/UMG.PanelWidget'
STRUCT_SLIDER = '/Script/AbioticFactor.GameSliderSettings'

def input_labels(c):
    ins, t = c['inputs'], c['type']
    first = ins[0] if ins else ''
    if t == 'EXEC' or t == 'TOGGLE':
        return '', '', 0
    if t == 'VALUE':
        return 'Amount' if first in ('', 'Value') else first, '', 1
    if t == 'OPTION':
        return first or 'Option', '', 0
    if t == 'OPTION_VALUE':
        return first or 'Option', 'Amount', 2
    if t == 'TWO_OPTION':
        return first or 'Option', (ins[1] if len(ins) > 1 else '') or 'Second option (optional)', 0
    if t == 'OPTION_TOGGLE':
        return first or 'Option', 'On or off: true / false (empty = switch)', 0
    raise ValueError(t)

META = []
for i, c in enumerate(CMDS):
    p1, p2, vb = input_labels(c)
    label = c['label'] + ('  (debug view)' if c['debug'] else '')
    parts = [label, c['desc'], p1, p2, str(vb), c['category'], str(i)]
    assert all('|' not in x for x in parts) and all(x.isascii() for x in parts), parts
    META.append('|'.join(parts))
CLASS_LIST = [CLASSES[c['row']] for c in CMDS]

def class_array():
    n = g.node('/Script/BlueprintGraph.K2Node_MakeArray', f'NumInputs={len(CLASS_LIST)}')
    for i, path in enumerate(CLASS_LIST):
        g.pin(n, f'[{i}]', 'class', obj=GCO, defaultobj=f'"/Script/Engine.BlueprintGeneratedClass\'{path}\'"')
    return g.pin(n, 'Array', 'class', True, GCO, array=True)

def meta_array():
    n = g.node('/Script/BlueprintGraph.K2Node_MakeArray', f'NumInputs={len(META)}')
    for i, m in enumerate(META):
        g.pin(n, f'[{i}]', 'string', default=m)
    return g.pin(n, 'Array', 'string', True, array=True)

def split_fields(src, count):
    out, rest = [], src
    for _ in range(count - 1):
        n, left = g.call(KSL, 'Split', False, args=[('SourceString', rest, 'string'), ('InStr', '|', 'string')], out=('LeftS', 'string'))
        rest = g.pin(n, 'RightS', 'string', True)
        g.pin(n, 'ReturnValue', 'bool', True)
        out.append(left)
    out.append(rest)
    return out

def text_of(widget, owner=TEXTBLOCK, target_cls=None, target=None):
    w = g.var(widget, owner) if target is None else g.var(widget, owner, target_cls, target)
    return g.t2s(g.call(owner, 'GetText', False, target=w, out=('ReturnValue', 'text'))[1])

def visibility(widget_pin, value):
    return g.call('/Script/UMG.Widget', 'SetVisibility', target=widget_pin, args=[('InVisibility', value, 'byte', VIS)])[0]

def show_if(cond, widget_name, owner=TEXTBLOCK):
    """Branch -> Visible / Collapsed; returns (branch, [two tail nodes]) so the caller can join both tails."""
    br = g.branch(cond)
    on = visibility(g.var(widget_name, owner), 'SelfHitTestInvisible')
    off = visibility(g.var(widget_name, owner), 'Collapsed')
    g.link(g.get(br, 'then'), g.get(on, 'execute'))
    g.link(g.get(br, 'else'), g.get(off, 'execute'))
    return br, [on, off]

def join(tails, nxt):
    for t in tails:
        g.link(g.get(t, 'then'), g.get(nxt, 'execute') if any(p['name'] == 'execute' for p in nxt['pins']) else g.get(nxt, 'Exec'))

def self_pin():
    return g.pin(g.node('/Script/BlueprintGraph.K2Node_Self'), 'self', 'object', True, '/Script/CoreUObject.Object')

def selected_index():
    key = text_of('CmdKey')
    has = g.call(KSL, 'NotEqual_StrStr', False, args=[('A', key, 'string'), ('B', '', 'string')], out=('ReturnValue', 'bool'))[1]
    idx = g.call(KSL, 'Conv_StringToInt', False, args=[('InString', key, 'string')], out=('ReturnValue', 'int'))[1]
    return has, idx

def with_selected_command(start):
    """start -> [has key?] -> for each class -> [index matches] ; returns (node whose 'then' runs with the command, command object, class pin, no-key branch)."""
    has, idx = selected_index()
    br_has = g.branch(has)
    loop, cls_pin = g.foreach(class_array(), 'class', GCO)
    eq = g.call(KML, 'EqualEqual_IntInt', False, args=[('A', g.get(loop, 'Array Index'), 'int'), ('B', idx, 'int')], out=('ReturnValue', 'bool'))[1]
    br_eq = g.branch(eq)
    make = g.node('/Script/BlueprintGraph.K2Node_GenericCreateObject')
    g.pin(make, 'execute')
    g.pin(make, 'then', out=True)
    g.feed(make, 'Class', cls_pin, 'class', GCO)
    g.feed(make, 'Outer', self_pin(), 'object', '/Script/CoreUObject.Object')
    obj = g.pin(make, 'ReturnValue', 'object', True, GCO)
    g.link(g.get(start, 'then'), g.get(br_has, 'execute'))
    g.link(g.get(br_has, 'then'), g.get(loop, 'Exec'))
    g.link(g.get(loop, 'LoopBody'), g.get(br_eq, 'execute'))
    g.link(g.get(br_eq, 'then'), g.get(make, 'execute'))
    return make, obj, cls_pin, br_has

def add_entry(box_name, name_pin, desc_pin, key_pin, pick_ev):
    cw = g.node('/Script/UMGEditor.K2Node_CreateWidget')
    g.pin(cw, 'execute')
    g.pin(cw, 'then', out=True)
    g.pin(cw, 'Class', 'class', obj='/Script/UMG.UserWidget', defaultobj=f'"/Script/UMG.WidgetBlueprintGeneratedClass\'{CENTRY}\'"')
    g.feed(cw, 'OwningPlayer', g.owning_player(), 'object', '/Script/Engine.PlayerController')
    entry = g.pin(cw, 'ReturnValue', 'object', True, CENTRY)
    nodes = [cw, set_text(g.var('EntryName', TEXTBLOCK, CENTRY, entry), g.s2t(name_pin))]
    if desc_pin is None:
        nodes.append(visibility(g.var('EntryDesc', TEXTBLOCK, CENTRY, entry), 'Collapsed'))
    else:
        nodes.append(set_text(g.var('EntryDesc', TEXTBLOCK, CENTRY, entry), g.s2t(desc_pin)))
    if key_pin is not None:
        nodes.append(set_text(g.var('EntryKey', TEXTBLOCK, CENTRY, entry), g.s2t(key_pin)))
    add = g.call(VBOX, 'AddChildToVerticalBox', target=g.var(box_name, VBOX), args=[('Content', entry, 'object', '/Script/UMG.Widget')],
                 out=('ReturnValue', 'object', '/Script/UMG.VerticalBoxSlot'))
    nodes.append(add[0])
    nodes.append(g.call('/Script/UMG.VerticalBoxSlot', 'SetPadding', target=add[1], args=[('InPadding', '(Left=0,Top=0,Right=0,Bottom=3)', 'struct', '/Script/SlateCore.Margin')])[0])
    bind = g.node('/Script/BlueprintGraph.K2Node_AddDelegate', f'DelegateReference=(MemberParent={cls(BUTTON)},MemberName="OnClicked")')
    g.pin(bind, 'execute')
    g.pin(bind, 'then', out=True)
    g.feed(bind, 'self', g.var('EntryButton', BUTTON, CENTRY, entry), 'object', BUTTON)
    g.feed(bind, 'Delegate', g.get(pick_ev, 'OutputDelegate'), 'delegate')
    nodes.append(bind)
    g.chain(*nodes)
    return cw

def hovered_entry(box_name, start):
    """start -> for each child of box -> cast -> hovered? ; returns (branch node, entry pin)."""
    kids = g.call(PANEL, 'GetAllChildren', False, target=g.var(box_name, VBOX), out=('ReturnValue', 'object', '/Script/UMG.Widget', None, True))[1]
    loop, child = g.foreach(kids, 'object', '/Script/UMG.Widget')
    ecast, ent = g.cast(child, CENTRY, 'AsW Director Cmd Entry')
    hover = g.call('/Script/UMG.Widget', 'IsHovered', False, target=g.var('EntryButton', BUTTON, CENTRY, ent), out=('ReturnValue', 'bool'))[1]
    br = g.branch(hover)
    g.chain(start, loop)
    g.link(g.get(loop, 'LoopBody'), g.get(ecast, 'execute'))
    g.link(g.get(ecast, 'then'), g.get(br, 'execute'))
    return br, ent

# ---- pass 1: state, options, prefill, option picks (call nothing that is not already compiled)
g.part = 1
g.row()
state_ev, _ = g.custom_event('ShowCmdState')
g.row()
pick_opt = {}
for n in (1, 2):
    pick_opt[n], _ = g.custom_event(f'PickOption{n}')
    g.row()
list_ev = {}
for n in (1, 2):
    list_ev[n] = g.custom_event(f'ListOptions{n}', [('Options', 'name', None, True)])
    g.row()
prefill_ev, prefill_args = g.custom_event('PrefillValue', [('Which', 'int', None)])
g.row()

# ShowCmdState: "Now: ON" for toggles, "Now: 120" for values, hidden otherwise
make, obj, _, _ = with_selected_command(state_ev)
st = g.call(GCO, 'GetCurrentState', target=obj, out=('OutState', 'string'))
st_ok = g.pin(st[0], 'ReturnValue', 'bool', True)
br_st = g.branch(st_ok)
show_state = set_text(g.var('CmdState', TEXTBLOCK), g.s2t(g.concat('Now: ', st[1])))
vis_on = visibility(g.var('CmdState', TEXTBLOCK), 'SelfHitTestInvisible')
val = g.call(GCO, 'GetCurrentValue', False, target=obj, out=('OutValue', 'real', None, 'float'))
val_ok = g.pin(val[0], 'ReturnValue', 'bool', True)
br_val = g.branch(val_ok)
val_txt = g.call(KTL, 'Conv_DoubleToText', False, args=[('Value', val[1], 'real', None, 'double'), ('bUseGrouping', 'false', 'bool'), ('MaximumFractionalDigits', '2', 'int')], out=('ReturnValue', 'text'))[1]
show_val = set_text(g.var('CmdState', TEXTBLOCK), g.s2t(g.concat('Now: ', g.t2s(val_txt))))
vis_on2 = visibility(g.var('CmdState', TEXTBLOCK), 'SelfHitTestInvisible')
vis_off = visibility(g.var('CmdState', TEXTBLOCK), 'Collapsed')
g.chain(make, st[0], br_st)
g.link(g.get(br_st, 'then'), g.get(show_state, 'execute'))
g.chain(show_state, vis_on)
g.link(g.get(br_st, 'else'), g.get(br_val, 'execute'))
g.link(g.get(br_val, 'then'), g.get(show_val, 'execute'))
g.chain(show_val, vis_on2)
g.link(g.get(br_val, 'else'), g.get(vis_off, 'execute'))
g.row()

# ListOptions1/2: up to 80 of the given options that contain what is typed in the box.
# The options arrive as an event parameter, so the (pure, slow) option getter runs once, not once per loop step.
for n in (1, 2):
    ev, args = list_ev[n]
    clear = g.call(PANEL, 'ClearChildren', target=g.var(f'CmdOptions{n}', VBOX))[0]
    loop, opt = g.foreach(args['Options'], 'name')
    opt_s = g.call(KSL, 'Conv_NameToString', False, args=[('InName', opt, 'name')], out=('ReturnValue', 'string'))[1]
    count = g.call(PANEL, 'GetChildrenCount', False, target=g.var(f'CmdOptions{n}', VBOX), out=('ReturnValue', 'int'))[1]
    room = g.call(KML, 'Less_IntInt', False, args=[('A', count, 'int'), ('B', '80', 'int')], out=('ReturnValue', 'bool'))[1]
    hit = g.call(KSL, 'Contains', False, args=[('SearchIn', opt_s, 'string'), ('Substring', text_of(f'CmdP{n}', ETB), 'string')], out=('ReturnValue', 'bool'))[1]
    ok = g.call(KML, 'BooleanAND', False, args=[('A', room, 'bool'), ('B', hit, 'bool')], out=('ReturnValue', 'bool'))[1]
    br = g.branch(ok)
    g.chain(ev, clear, loop)
    g.link(g.get(loop, 'LoopBody'), g.get(br, 'execute'))
    cw = add_entry(f'CmdOptions{n}', opt_s, None, None, pick_opt[n])
    g.link(g.get(br, 'then'), g.get(cw, 'execute'))
    g.row()

# PickOption1/2: clicked option goes into the box
for n in (1, 2):
    br, ent = hovered_entry(f'CmdOptions{n}', pick_opt[n])
    put = set_text(g.var(f'CmdP{n}', ETB), g.call(TEXTBLOCK, 'GetText', False, target=g.var('EntryName', TEXTBLOCK, CENTRY, ent), out=('ReturnValue', 'text'))[1], ETB)
    g.link(g.get(br, 'then'), g.get(put, 'execute'))
    g.row()

# PrefillValue: put the command's default amount in the value box and its range in the label
make, obj, _, _ = with_selected_command(prefill_ev)
sl = g.call(GCO, 'GetSliderSettings', False, target=obj, out=('ReturnValue', 'struct', STRUCT_SLIDER))
g.pin(sl[0], 'bDynamicSettings', 'bool', True)
brk = g.node('/Script/BlueprintGraph.K2Node_BreakStruct', f'StructType="/Script/CoreUObject.ScriptStruct\'{STRUCT_SLIDER}\'"')
g.feed(brk, 'GameSliderSettings', sl[1], 'struct', STRUCT_SLIDER)
vmin, vmax, vdef = (g.pin(brk, k, 'real', True, sub='float') for k in ('MinSliderValue', 'MaxSliderValue', 'DefaultSliderValue'))
def num(v):
    return g.call(KTL, 'Conv_DoubleToText', False, args=[('Value', v, 'real', None, 'double'), ('bUseGrouping', 'false', 'bool'), ('MaximumFractionalDigits', '2', 'int')], out=('ReturnValue', 'text'))[1]
ranged = g.call(KML, 'NotEqual_DoubleDouble', False, args=[('A', vmin, 'real', None, 'double'), ('B', vmax, 'real', None, 'double')], out=('ReturnValue', 'bool'))[1]
br_range = g.branch(ranged)
g.chain(make, br_range)
prev = g.get(br_range, 'then')  # Which == 1 ? box 1 : (Which == 2 ? box 2 : nothing)
for n in (1, 2):
    is_n = g.call(KML, 'EqualEqual_IntInt', False, args=[('A', prefill_args['Which'], 'int'), ('B', str(n), 'int')], out=('ReturnValue', 'bool'))[1]
    br_n = g.branch(is_n)
    put = set_text(g.var(f'CmdP{n}', ETB), num(vdef), ETB)
    rng = g.concat(g.concat(text_of(f'CmdP{n}Label'), '  ('), g.concat(g.concat(g.t2s(num(vmin)), ' to '), g.concat(g.t2s(num(vmax)), ')')))
    lab = set_text(g.var(f'CmdP{n}Label', TEXTBLOCK), g.s2t(rng))
    g.link(prev, g.get(br_n, 'execute'))
    g.link(g.get(br_n, 'then'), g.get(put, 'execute'))
    g.chain(put, lab)
    prev = g.get(br_n, 'else')
g.row()

# ---- pass 2: FillOptions1/2 (call ListOptions)
g.part = 2
for n in (1, 2):
    ev, _ = g.custom_event(f'FillOptions{n}')
    make, obj, _, br_has = with_selected_command(ev)
    fn = 'GetFirstParamOptions' if n == 1 else 'GetSecondParamOptions'
    opts_n, opts = g.call(GCO, fn, False, target=obj, out=('ReturnValue', 'name', None, None, True))
    g.pin(opts_n, 'bDynamicOptions', 'bool', True)
    g.chain(make, g.call_self(f'ListOptions{n}', [('Options', opts, 'name', None, True)]))
    g.link(g.get(br_has, 'else'), g.get(g.call(PANEL, 'ClearChildren', target=g.var(f'CmdOptions{n}', VBOX))[0], 'execute'))
    g.row()

# ---- pass 3: SelectCommand (calls pass-1/2 events)
g.part = 3
sel_ev, sel_args = g.custom_event('SelectCommand', [('Key', 'string', None)])
f_label, f_desc, f_p1, f_p2, f_vb, f_cat, f_idx = split_fields(sel_args['Key'], 7)
nodes = [sel_ev,
         set_text(g.var('CmdKey', TEXTBLOCK), g.s2t(f_idx)),
         set_text(g.var('CmdName', TEXTBLOCK), g.s2t(f_label)),
         set_text(g.var('CmdDesc', TEXTBLOCK), g.s2t(g.concat(g.concat(f_cat, '  -  '), f_desc))),
         set_text(g.var('CmdP1Label', TEXTBLOCK), g.s2t(f_p1)),
         set_text(g.var('CmdP2Label', TEXTBLOCK), g.s2t(f_p2)),
         set_text(g.var('CmdP1', ETB), g.s2t(''), ETB),
         set_text(g.var('CmdP2', ETB), g.s2t(''), ETB)]
g.chain(*nodes)
has1 = g.call(KSL, 'NotEqual_StrStr', False, args=[('A', f_p1, 'string'), ('B', '', 'string')], out=('ReturnValue', 'bool'))[1]
br1, tails1 = show_if(has1, 'CmdP1Block', VBOX)
g.link(g.get(nodes[-1], 'then'), g.get(br1, 'execute'))
has2 = g.call(KSL, 'NotEqual_StrStr', False, args=[('A', f_p2, 'string'), ('B', '', 'string')], out=('ReturnValue', 'bool'))[1]
br2, tails2 = show_if(has2, 'CmdP2Block', VBOX)
join(tails1, br2)
calls = [g.call_self('ShowCmdState'), g.call_self('FillOptions1'), g.call_self('FillOptions2'),
         g.call_self('PrefillValue', [('Which', g.call(KSL, 'Conv_StringToInt', False, args=[('InString', f_vb, 'string')], out=('ReturnValue', 'int'))[1], 'int')]),
         status(g.concat('Selected: ', f_label))]
join(tails2, calls[0])
g.chain(*calls)
g.row()

# ---- pass 4: list, pick, run (call earlier events and RunCommand)
g.part = 4
pick_cmd, _ = g.custom_event('PickCommand')
g.row()
search_cmd, _ = g.custom_event('SearchCommands')
g.row()
run_sel, _ = g.custom_event('RunSelected')
g.row()

# SearchCommands: every command whose name, description or category contains the search text
clear = g.call(PANEL, 'ClearChildren', target=g.var('CmdResults', VBOX))[0]
loop, meta = g.foreach(meta_array(), 'string')
f_label, f_desc, _, _, _, f_cat, _ = split_fields(meta, 7)
hay = g.concat(g.concat(f_label, ' '), g.concat(g.concat(f_desc, ' '), f_cat))
hit = g.call(KSL, 'Contains', False, args=[('SearchIn', hay, 'string'), ('Substring', text_of('CmdSearch', ETB), 'string')], out=('ReturnValue', 'bool'))[1]
br = g.branch(hit)
cw = add_entry('CmdResults', f_label, g.concat(g.concat(f_cat, '  -  '), f_desc), meta, pick_cmd)
shown = g.call(PANEL, 'GetChildrenCount', False, target=g.var('CmdResults', VBOX), out=('ReturnValue', 'int'))[1]
fin = status(g.concat(g.call(KSL, 'Conv_IntToString', False, args=[('InInt', shown, 'int')], out=('ReturnValue', 'string'))[1], ' commands. Click one to choose it.'))
g.chain(search_cmd, clear, loop)
g.link(g.get(loop, 'LoopBody'), g.get(br, 'execute'))
g.link(g.get(br, 'then'), g.get(cw, 'execute'))
g.link(g.get(loop, 'Completed'), g.get(fin, 'execute'))
g.row()

# PickCommand: the hovered result becomes the selected command
br, ent = hovered_entry('CmdResults', pick_cmd)
pick = g.call_self('SelectCommand', [('Key', text_of('EntryKey', TEXTBLOCK, CENTRY, ent), 'string')])
g.link(g.get(br, 'then'), g.get(pick, 'execute'))
g.row()

# RunSelected: run with both boxes (converted the way the game's own menu does), then refresh the state line
make, obj, cls_pin, br_has = with_selected_command(run_sel)
conv = []
for n in (1, 2):
    conv.append(g.call(GCO, 'ConvertParamToOriginal', False, target=obj, args=[('InParam', text_of(f'CmdP{n}', ETB), 'string'), ('bIsSecondParam', 'true' if n == 2 else 'false', 'bool')],
                       out=('ReturnValue', 'string'))[1])
run_n = g.call_self('RunCommand', [('Cmd', cls_pin, 'class', GCO), ('P1', conv[0], 'string'), ('P2', conv[1], 'string'),
                                   ('Label', g.concat('Ran: ', text_of('CmdName')), 'string')])
g.chain(make, run_n, g.call_self('ShowCmdState'))
g.link(g.get(br_has, 'else'), g.get(status('Pick a command from the list first.'), 'execute'))
g.row()

# ---- pass 5: buttons and boxes
g.part = 5
g.chain(g.bound('CmdSearchGo'), g.call_self('SearchCommands'))
g.row()
for widget, target in [('CmdSearch', 'SearchCommands'), ('CmdP1', 'FillOptions1'), ('CmdP2', 'FillOptions2')]:
    ch = g.bound(widget, ETB, 'OnTextChanged', 'OnEditableTextBoxChangedEvent__DelegateSignature')
    g.pin(ch, 'Text', 'text', True)
    g.chain(ch, g.call_self(target))
    g.row()
g.chain(g.bound('CmdRun'), g.call_self('RunSelected'))
g.row()

# ====================================================================== hotbar keys while the menu is open
# The menu blocks game input, so held-item actions would only ever hit the Cheat Remote. 1-0 and the wheel are caught
# here and passed to the character's own RefreshSelectedHotbarSlot (what its HotbarSlotN / Next / Previous inputs end in).
INV = '/Game/Blueprints/Characters/Abiotic_InventoryComponent.Abiotic_InventoryComponent_C'
SLOT_STRUCT = 'uds:/Game/Blueprints/Data/InventorySlotSelected_Struct.InventorySlotSelected_Struct'

def my_pawn():
    pawn = g.call('/Script/UMG.UserWidget', 'GetOwningPlayerPawn', False, out=('ReturnValue', 'object', '/Script/Engine.Pawn'))[1]
    return g.cast(pawn, PAWN, 'AsAbiotic Player Character')

# pass 1: SelectHotbar(Index) - ignored while a menu text box has the keyboard (typing "25" must not switch items)
g.part = 1
g.row()
hb_ev, hb_args = g.custom_event('SelectHotbar', [('Index', 'int', None)])
typing = None
for box in ['ItemSearch', 'ItemQty', 'CmdSearch', 'CmdP1', 'CmdP2']:
    f = g.call('/Script/UMG.Widget', 'HasKeyboardFocus', False, target=g.var(box, ETB), out=('ReturnValue', 'bool'))[1]
    typing = f if typing is None else g.call(KML, 'BooleanOR', False, args=[('A', typing, 'bool'), ('B', f, 'bool')], out=('ReturnValue', 'bool'))[1]
br_typing = g.branch(typing)
pcast, ppawn = my_pawn()
# backpacks give 8-10 hotbar slots; keys past the last one do nothing
top = g.var('MaxHotbarSlotSelected', None, PAWN, ppawn, 'int')
fits = g.call(KML, 'LessEqual_IntInt', False, args=[('A', hb_args['Index'], 'int'), ('B', top, 'int')], out=('ReturnValue', 'bool'))[1]
br_fits = g.branch(fits)
slots = g.call(KML, 'Add_IntInt', False, args=[('A', top, 'int'), ('B', '1', 'int')], out=('ReturnValue', 'int'))[1]
too_far = status(g.concat(g.concat('Your hotbar only has ', g.call(KSL, 'Conv_IntToString', False, args=[('InInt', slots, 'int')], out=('ReturnValue', 'string'))[1]), ' slots.'))
switch =g.call(PAWN, 'RefreshSelectedHotbarSlot', target=ppawn, args=[('Inventory', g.var('CharacterHotbarInventory', INV, PAWN, ppawn), 'object', INV),
                                                                       ('Index', hb_args['Index'], 'int'), ('Sound', 'true', 'bool')])[0]
slot_no = g.call(KML, 'Add_IntInt', False, args=[('A', hb_args['Index'], 'int'), ('B', '1', 'int')], out=('ReturnValue', 'int'))[1]
said = status(g.concat(g.concat('Holding hotbar slot ', g.call(KSL, 'Conv_IntToString', False, args=[('InInt', slot_no, 'int')], out=('ReturnValue', 'string'))[1]),
                       '. Held-item actions now use it.'))
g.chain(hb_ev, br_typing)
g.link(g.get(br_typing, 'else'), g.get(pcast, 'execute'))
g.chain(pcast, br_fits)
g.link(g.get(br_fits, 'then'), g.get(switch, 'execute'))
g.link(g.get(br_fits, 'else'), g.get(too_far, 'execute'))
g.chain(switch, said)

# pass 2: HotbarStep(Delta) - the wheel; wraps like the game's Next/PreviousHotbarItem
g.part = 2
g.row()
step_ev, step_args = g.custom_event('HotbarStep', [('Delta', 'int', None)])
pcast, ppawn = my_pawn()
brk = g.node('/Script/BlueprintGraph.K2Node_BreakStruct', f'StructType="/Script/Engine.UserDefinedStruct\'{SLOT_STRUCT[4:]}\'"')
g.feed(brk, 'InventorySlotSelected_Struct', g.var('CurrentHotbarSlotSelected', SLOT_STRUCT, PAWN, ppawn, 'struct'), 'struct', SLOT_STRUCT)
cur = g.pin(brk, 'Index_5_6BDC7B3944A5DE0B319F9FA20720872F', 'int', True)
top = g.var('MaxHotbarSlotSelected', None, PAWN, ppawn, 'int')
nxt = g.call(KML, 'Add_IntInt', False, args=[('A', cur, 'int'), ('B', step_args['Delta'], 'int')], out=('ReturnValue', 'int'))[1]
over = g.call(KML, 'Greater_IntInt', False, args=[('A', nxt, 'int'), ('B', top, 'int')], out=('ReturnValue', 'bool'))[1]
under = g.call(KML, 'Less_IntInt', False, args=[('A', nxt, 'int'), ('B', '0', 'int')], out=('ReturnValue', 'bool'))[1]
wrap1 = g.call(KML, 'SelectInt', False, args=[('A', '0', 'int'), ('B', nxt, 'int'), ('bPickA', over, 'bool')], out=('ReturnValue', 'int'))[1]
wrap2 = g.call(KML, 'SelectInt', False, args=[('A', top, 'int'), ('B', wrap1, 'int'), ('bPickA', under, 'bool')], out=('ReturnValue', 'int'))[1]
g.chain(step_ev, pcast, g.call_self('SelectHotbar', [('Index', wrap2, 'int')]))

# pass 3: the parameterless events ListenForInputAction calls
g.part = 3
g.row()
for i in range(1, 11):
    ev, _ = g.custom_event(f'KeySlot{i}')
    g.chain(ev, g.call_self('SelectHotbar', [('Index', str(i - 1), 'int')]))
    g.row()
for name, delta in [('KeyNext', '1'), ('KeyPrev', '-1')]:
    ev, _ = g.custom_event(name)
    g.chain(ev, g.call_self('HotbarStep', [('Delta', delta, 'int')]))
    g.row()

menu_nodes = g.write(ROOT / 'graphs' / 'menu-08.txt')
print('menu nodes', menu_nodes)

# ====================================================================== shared helpers
# (0.5/0.6 also had a badge buff graph here; the badge was removed in 0.6.)
def player_controller():
    return g.call(GS, 'GetPlayerController', False, args=[('PlayerIndex', '0', 'int')], out=('ReturnValue', 'object', '/Script/Engine.PlayerController'))[1]

def find_menus():
    n = g.call(WBL, 'GetAllWidgetsOfClass', args=[('WidgetClass', None, 'class', '/Script/UMG.UserWidget'), ('TopLevelOnly', 'true', 'bool')],
               out=('FoundWidgets', 'object', MENU, None, True))
    g.get(n[0], 'WidgetClass')['defaultobj'] = f'"/Script/UMG.WidgetBlueprintGeneratedClass\'{MENU}\'"'
    return n

# ====================================================================== Cheat Remote (held item)
g = Graph()
ITEM = '/Game/Blueprints/Items/Abiotic_Item_ParentBP.Abiotic_Item_ParentBP_C'
use = g.event(ITEM, 'UseItem_LocalFX')
user = g.pin(use, 'UsingCharacter', 'object', True, '/Game/Blueprints/Characters/Abiotic_PlayerCharacter.Abiotic_PlayerCharacter_C')
g.pin(use, 'TargetActor', 'object', True, '/Script/Engine.Actor')
pawn0 = g.call(GS, 'GetPlayerPawn', False, args=[('PlayerIndex', '0', 'int')], out=('ReturnValue', 'object', '/Script/Engine.Pawn'))[1]
mine = g.call(KML, 'EqualEqual_ObjectObject', False, args=[('A', user, 'object', '/Script/CoreUObject.Object'), ('B', pawn0, 'object', '/Script/CoreUObject.Object')], out=('ReturnValue', 'bool'))[1]
br_mine = g.branch(mine)
found = find_menus()
length = g.call('/Script/Engine.KismetArrayLibrary', 'Array_Length', False, args=[('TargetArray', found[1], 'object', MENU)], out=('ReturnValue', 'int'), kind='K2Node_CallArrayFunction')
g.get(length[0], 'TargetArray')['array'] = True
none = g.call(KML, 'EqualEqual_IntInt', False, args=[('A', length[1], 'int'), ('B', '0', 'int')], out=('ReturnValue', 'bool'))[1]
br_none = g.branch(none)
cw = g.node('/Script/UMGEditor.K2Node_CreateWidget')
g.pin(cw, 'execute')
g.pin(cw, 'then', out=True)
g.pin(cw, 'Class', 'class', obj='/Script/UMG.UserWidget', defaultobj=f'"/Script/UMG.WidgetBlueprintGeneratedClass\'{MENU}\'"')
g.feed(cw, 'OwningPlayer', player_controller(), 'object', '/Script/Engine.PlayerController')
widget = g.pin(cw, 'ReturnValue', 'object', True, MENU)
addv = g.call('/Script/UMG.UserWidget', 'AddToViewport', target=widget, args=[('ZOrder', '100', 'int')])[0]
g.chain(use, br_mine)
g.link(g.get(br_mine, 'then'), g.get(found[0], 'execute'))
g.chain(found[0], br_none)
g.link(g.get(br_none, 'then'), g.get(cw, 'execute'))
g.chain(cw, addv)
# the remote graph is unchanged since 0.6; it is only written for reference
print('remote nodes', g.write(ROOT / 'graphs' / 'remote-08.txt'))
