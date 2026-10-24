#!/usr/bin/env python3
import json, pathlib, subprocess, sys
if len(sys.argv) != 4:
    raise SystemExit('usage: validate-volume-source.py VOLUME EXPECTED_DEVICE WORKSPACE')
name, expected_raw, workspace = sys.argv[1:]
expected = str(pathlib.Path(expected_raw).resolve(strict=True))
actual = json.loads(subprocess.check_output(['docker','volume','inspect',name],text=True))[0]
options = actual.get('Options') or {}
labels = actual.get('Labels') or {}
checks = {
  'driver_local': actual.get('Driver') == 'local',
  'type_none': options.get('type') == 'none',
  'bind_option': options.get('o') == 'bind',
  'canonical_device': pathlib.Path(options.get('device','')).resolve(strict=True).as_posix() == expected,
  'attachable': labels.get('openshell.ai/sandbox-attachable') == 'true',
  'workspace': labels.get('openshell.ai/sandbox-attachable-workspace') == workspace,
  'fixture_identity': labels.get('jackin.fixture') == 'jfr-20261024-verification-worker',
}
print(json.dumps({'volume':name,'expected_device':expected,'actual_device':options.get('device'),'checks':checks,'authorized':all(checks.values())},indent=2))
raise SystemExit(0 if all(checks.values()) else 1)
