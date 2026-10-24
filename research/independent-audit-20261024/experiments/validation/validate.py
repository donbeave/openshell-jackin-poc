#!/usr/bin/env python3
"""Validate research artifacts without executing workloads or product tests."""
import ast,datetime,hashlib,json,pathlib,re,subprocess
root=pathlib.Path(__file__).resolve().parents[2]
failures=[];checks={};files=[]
for directory in ('audits','evidence','experiments'):
 for p in (root/directory).rglob('*'):
  if not p.is_file() or '__pycache__' in p.parts:continue
  files.append(p)
  try:
   if p.suffix=='.json':json.loads(p.read_text())
   if p.suffix=='.py':ast.parse(p.read_text(),filename=str(p))
   if p.suffix=='.sh':
    shell='bash' if 'bash' in p.read_text().splitlines()[0] else 'sh'
    r=subprocess.run([shell,'-n',str(p)],capture_output=True)
    if r.returncode:failures.append({'file':str(p.relative_to(root)),'check':'shell syntax','stderr':r.stderr.decode()})
  except Exception as exc:failures.append({'file':str(p.relative_to(root)),'check':'parse','error':str(exc)})
checks['json_python_shell_files_checked']=len(files)
expected={'jackin':'6e266406b49da2ab3c55355f3b7d33d1643ee6cd','architect':'7b72b38fe1d66e35c0931899c53bf3719592bbcc','openshell':'bdb956f2cd65a635f1294fccf1d138d263bf650f'}
checks['source_checkouts']={}
for name,sha in expected.items():
 path=root/'sources'/name
 got=subprocess.check_output(['git','-C',str(path),'rev-parse','HEAD'],text=True).strip()
 changes=subprocess.check_output(['git','-C',str(path),'status','--porcelain'],text=True).strip()
 checks['source_checkouts'][name]={'expected':sha,'actual':got,'worktree_changes':changes}
 if got!=sha or changes:failures.append({'source':name,'check':'pinned unchanged checkout'})
d=json.loads((root/'audits/source-inventory.json').read_text());b=json.loads((root/'audits/broad-source-matches.json').read_text())
allowed={'Active and demonstrated','Active but untested','Implemented without a production caller','Incomplete','Planned only'}
rows=d['direct_callsite_ledger'];keys=set()
for r in rows:
 key=(r['file'],r['line'],r['symbol'])
 if key in keys:failures.append({'check':'duplicate canonical site','key':key})
 keys.add(key)
 if r.get('source_behavior') not in allowed:failures.append({'check':'source behavior','key':key})
 if not r.get('source_review_complete',r.get('review_complete',False)):failures.append({'check':'source review incomplete','key':key})
 if r.get('replacement_execution_proved'):failures.append({'check':'unexpected replacement execution claim','key':key})
 path=root/'sources/jackin'/r['file']
 if not path.is_file() or not 1<=r['line']<=len(path.read_text().splitlines()):failures.append({'check':'invalid source reference','key':key})
checks['inventory']=d['source_coverage_summary'];checks['broad_match_count']=len(b['matches'])
if not b.get('coverage_complete'):failures.append({'check':'broad source coverage'})
if d.get('raw_unresolved_count')!=0:failures.append({'check':'unresolved narrow source candidates'})
for p in root.glob('*.md'):
 for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',p.read_text()):
  if target.startswith(('http:','https:','#')):continue
  target=target.split('#',1)[0]
  if not (p.parent/target).exists():failures.append({'check':'local markdown target','file':p.name,'target':target})
# Only inspect experiment-owned paths for retained generated private-key files.
private_paths=[]
for p in (root/'experiments').rglob('*'):
 if p.is_file() and p.suffix in ('.key','.p12','.pfx','.pem'):
  private_paths.append(str(p.relative_to(root)))
checks['retained_experiment_key_paths']=private_paths
if private_paths:failures.append({'check':'retained experiment key paths','paths':private_paths})
out={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'result':'PASS' if not failures else 'FAIL','scope':'Artifact/source integrity and syntax only; no product or runtime acceptance tests.','checks':checks,'failures':failures}
(root/'evidence/validation.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'result':out['result'],'files_checked':len(files),'direct_sites':len(rows),'failures':failures},indent=2))
raise SystemExit(bool(failures))
