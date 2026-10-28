"""Small Windows helpers for driving the Mod Editor window: screenshot, click, keys.
Usage: py win.py shot out.png | click x y | dclick x y | keys ctrl+v | focus"""
import ctypes, ctypes.wintypes as wt, subprocess, sys, time

user32 = ctypes.windll.user32
user32.SetProcessDPIAware()
import os
TITLE = os.environ.get('CM_WINDOW', 'AbioticFactor [Test] - Unreal Editor')  # e.g. CM_WINDOW=W_DirectorMenu for an asset editor window

def hwnd():
    h = user32.FindWindowW(None, TITLE)
    if not h:
        raise SystemExit('editor window not found')
    return h

def rect():
    r = wt.RECT()
    user32.GetWindowRect(hwnd(), ctypes.byref(r))
    return r.left, r.top, r.right, r.bottom

def pid_of(h):
    pid = ctypes.c_ulong()
    user32.GetWindowThreadProcessId(h, ctypes.byref(pid))
    return pid.value

def editor_in_front():
    return pid_of(user32.GetForegroundWindow()) == pid_of(hwnd())

def focus():
    h = hwnd()
    user32.ShowWindow(h, 9)
    # Alt tap lets SetForegroundWindow succeed from a background process.
    user32.keybd_event(0x12, 0, 0, 0); user32.keybd_event(0x12, 0, 2, 0)
    user32.SetForegroundWindow(h)
    time.sleep(0.4)

def shot(path):
    l, t, r, b = rect()
    ps = ('Add-Type -AssemblyName System.Drawing;'
          f'$b=New-Object System.Drawing.Bitmap({r-l},{b-t});$g=[System.Drawing.Graphics]::FromImage($b);'
          f'$g.CopyFromScreen({l},{t},0,0,$b.Size);$b.Save("{path}");')
    focus()
    subprocess.run(['powershell', '-NoProfile', '-Command', ps], check=True)
    print('window', l, t, r, b)

def click(x, y, double=False):
    l, t, _, _ = rect()
    user32.SetCursorPos(l + x, t + y)
    time.sleep(0.15)
    for _ in range(2 if double else 1):
        user32.mouse_event(2, 0, 0, 0, 0); user32.mouse_event(4, 0, 0, 0, 0)
        time.sleep(0.08)

VK = {'ctrl': 0x11, 'shift': 0x10, 'alt': 0x12, 'enter': 0x0D, 'esc': 0x1B, 'tab': 0x09,
      'delete': 0x2E, 'f7': 0x76, 'home': 0x24, 'end': 0x23, 'space': 0x20}

def keys(combo, at=None):
    # Keyboard input goes to the foreground window, so click into the target first (that also
    # brings the editor forward) and refuse to type anywhere else.
    if at:
        click(*at)
        time.sleep(0.3)
    if not editor_in_front():
        raise SystemExit('editor is not the foreground window; not sending keys')
    parts = combo.lower().split('+')
    codes = [VK[p] if p in VK else ord(p.upper()) for p in parts]
    ext = {0x2E, 0x24, 0x23}  # delete/home/end are extended keys
    for c in codes: user32.keybd_event(c, 0, 1 if c in ext else 0, 0); time.sleep(0.05)
    for c in reversed(codes): user32.keybd_event(c, 0, (1 if c in ext else 0) | 2, 0); time.sleep(0.05)

if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'shot': shot(sys.argv[2])
    elif cmd == 'click': click(int(sys.argv[2]), int(sys.argv[3]))
    elif cmd == 'dclick': click(int(sys.argv[2]), int(sys.argv[3]), True)
    elif cmd == 'keys': keys(sys.argv[2], (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else None)
    elif cmd == 'focus': focus()
