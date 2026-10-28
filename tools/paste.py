"""Paste a generated graph file into the Blueprint graph currently shown in the editor.
Everything runs in one process so the editor keeps keyboard focus between steps.
Usage: py paste.py file.txt [--clear] [--at x y]"""
import sys, subprocess, time
import win
args = sys.argv[1:]
at = (600, 640)
if '--at' in args:
    i = args.index('--at'); at = (int(args[i + 1]), int(args[i + 2]))
subprocess.run(['powershell', '-NoProfile', '-Command', f"Set-Clipboard -Value (Get-Content -Raw '{args[0]}')"], check=True)
win.focus()
win.click(*at); time.sleep(0.5)
if '--clear' in args:
    win.keys('ctrl+a'); time.sleep(0.6)
    win.keys('delete'); time.sleep(0.8)
    win.click(*at); time.sleep(0.4)
win.keys('ctrl+v'); time.sleep(3)
print('pasted', args[0])
