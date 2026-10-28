"""Print node kinds, member refs and pin names from a Blueprint T3D export. Usage: py t3dpins.py file.t3d [filter]"""
import re, sys
text = open(sys.argv[1], encoding='utf-8', errors='replace').read()
flt = sys.argv[2] if len(sys.argv) > 2 else ''
for block in re.split(r'\n\s*Begin Object Class=', text)[1:]:
    head = block.split('\n', 1)[0]
    kind = head.split(' ')[0].split('.')[-1]
    if not kind.startswith('K2Node') and 'Node' not in kind: continue
    ref = re.search(r'(?:FunctionReference|EventReference|VariableReference|DelegateReference)=\((?:MemberParent="[^"]*\.([^.\'"]+)\'?",)?MemberName="([^"]+)"', block)
    extra = re.findall(r'^\s*(StructType|TargetType|MacroGraphReference|InputKey|CustomFunctionName|SelectedFunctionName|DelegatePropertyName|ComponentPropertyName)=(.*)$', block, re.M)
    pins = re.findall(r'PinName="([^"]+)"(?:,PinToolTip="[^"]*")?(?:,PinFriendlyName=[^,]*)?(,Direction="EGPD_Output")?,PinType\.PinCategory="([^"]*)"', block)
    line = f"{kind} {ref.group(1) if ref else ''}.{ref.group(2) if ref else ''} {extra}\n   " + ', '.join(f"{'>' if d else '<'}{n}:{c}" for n, d, c in pins)
    if flt in line: print(line)
