#!/usr/bin/env python3
"""Collect public source metadata without reading account credentials."""
import json, pathlib, subprocess, datetime
root=pathlib.Path(__file__).resolve().parents[2]
out=root/'evidence'/'versions';out.mkdir(parents=True,exist_ok=True)
refs={'jackin-project/jackin':'6e266406b49da2ab3c55355f3b7d33d1643ee6cd','jackin-project/jackin-the-architect':'7b72b38fe1d66e35c0931899c53bf3719592bbcc','NVIDIA/OpenShell':'bdb956f2cd65a635f1294fccf1d138d263bf650f','donbeave/openshell-jackin-poc':'2315e6a278231854b3139b1ca32402777ff3cd01'}
manifest={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'repositories':{}}
for repo,reviewed in refs.items():
 def fetch(endpoint,name):
  cmd=['gh','api','repos/'+repo+'/'+endpoint]
  r=subprocess.run(cmd,capture_output=True)
  data={'command':cmd,'exit_status':r.returncode,'stderr':r.stderr.decode()}
  try:data['response']=json.loads(r.stdout)
  except ValueError:data['stdout']=r.stdout.decode()
  (out/(repo.replace('/','__')+'__'+name+'.json')).write_text(json.dumps(data,indent=2)+'\n')
  return data.get('response',{})
 head=fetch('commits/main','head');releases=fetch('releases?per_page=100','releases')
 sha=head.get('sha')
 rec={'reviewed':reviewed,'current_main':sha,'releases':[{k:r.get(k) for k in ('tag_name','published_at','prerelease','draft','target_commitish')} for r in releases] if isinstance(releases,list) else releases}
 if sha and reviewed!=sha:fetch('compare/'+reviewed+'...'+sha,'compare')
 manifest['repositories'][repo]=rec
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
