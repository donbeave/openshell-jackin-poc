#!/usr/bin/env python3
"""Fetch missing pinned research inputs; never reset an existing checkout."""
import os,pathlib,subprocess
root=pathlib.Path(__file__).resolve().parents[2]
pins={'jackin':('https://github.com/jackin-project/jackin.git','6e266406b49da2ab3c55355f3b7d33d1643ee6cd'),'architect':('https://github.com/jackin-project/jackin-the-architect.git','7b72b38fe1d66e35c0931899c53bf3719592bbcc'),'openshell':('https://github.com/NVIDIA/OpenShell.git','bdb956f2cd65a635f1294fccf1d138d263bf650f')}
def gate():
 path='/System/Volumes/Data' if pathlib.Path('/System/Volumes/Data').exists() else '/'
 state=os.statvfs(path);available=state.f_bavail*state.f_frsize
 if available<2_000_000_000_000:raise SystemExit('Disk below required 2 TB hard gate; source fetch not started.')
for name,(url,sha) in pins.items():
 path=root/'sources'/name
 if path.exists():
  actual=subprocess.check_output(['git','-C',str(path),'rev-parse','HEAD'],text=True).strip()
  if actual!=sha:raise SystemExit(f'{name}: existing checkout differs; preserved without reset.')
  print(f'{name}: existing requested pin retained')
  continue
 gate();path.parent.mkdir(parents=True,exist_ok=True)
 subprocess.run(['git','clone','--filter=blob:none','--no-checkout',url,str(path)],check=True)
 gate();subprocess.run(['git','-C',str(path),'checkout','--detach',sha],check=True)
 print(f'{name}: pinned {sha}')
