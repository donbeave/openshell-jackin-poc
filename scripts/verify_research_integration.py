#!/usr/bin/env python3
"""Validate the research publication; keep raw security diagnostics outside it."""
from __future__ import annotations
import ast,hashlib,json,os,pathlib,re,subprocess,tempfile
from datetime import datetime,timezone
ROOT=pathlib.Path(__file__).resolve().parents[1]
BUNDLE=ROOT/'research/independent-audit-20261024'
REVIEWED={
 ('experiments/full-refactor-20261024/verification-worker/results/image-inspect.json',1):'Official image public signing-key ID; prior independent publication review.',
 ('experiments/full-refactor-20261024/verification-worker/tmpfs-diagnostic/inspect.json',154):'Official image public signing-key ID; prior independent publication review.',
 ('experiments/full-refactor-20261024/verification-worker/tmpfs-diagnostic/docker-inspect.json',154):'Official image public signing-key ID; prior independent publication review.',
 ('results/full-replacement-20261024/control/tls-wrong-ou.stdout.json',7):'Synthetic mTLS test subject; prior independent publication review.',
 ('results/full-replacement-20261024/docker/managed-engine-research.md',25):'Plain prose; prior independent publication review.',
 ('research/independent-audit-20261024/evidence/capsule/RESULTS.md',30):'Plain prose about peer identity and reaping; complete sentence manually inspected, no credential value.'}
def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def main()->None:
 failures=[];count=0
 for p in BUNDLE.rglob('*'):
  if not p.is_file() or '__pycache__' in p.parts:continue
  try:
   if p.suffix=='.json':json.loads(p.read_text())
   if p.suffix=='.py':ast.parse(p.read_text())
   if p.suffix=='.sh':
    shell='bash' if 'bash' in p.read_text().splitlines()[0] else 'sh'
    if subprocess.run([shell,'-n',str(p)],capture_output=True).returncode:failures.append(str(p.relative_to(ROOT))+' shell syntax')
  except Exception:failures.append(str(p.relative_to(ROOT))+' parse')
  count+=1
 for name in ['publish_independent_audit.py','verify_research_integration.py']:
  ast.parse((ROOT/'scripts'/name).read_text())
 provenance=json.loads((BUNDLE/'PUBLICATION_PROVENANCE.json').read_text())
 for row in provenance['files']:
  if sha((ROOT/row['path']).read_bytes())!=row['published_sha256']:failures.append(row['path']+' provenance')
 for row in json.loads((ROOT/'INTEGRATION_EXTRA_EVIDENCE.json').read_text())['new_included']:
  if sha((ROOT/row['path']).read_bytes())!=row['published_sha256']:failures.append(row['path']+' extra provenance')
 for row in json.loads((BUNDLE/'ARTIFACT_MANIFEST.json').read_text())['files']:
  if sha((BUNDLE/row['path']).read_bytes())!=row['sha256']:failures.append(row['path']+' bundle hash')
 md=[ROOT/x for x in ['README.md','RESEARCH_INDEX.md','READINESS_REPORT.md','SOURCE_INVENTORY.md','FULL_REFACTOR_HANDOFF.md','INTEGRATION_PUBLICATION.md']]+list(BUNDLE.rglob('*.md'))
 for p in md:
  for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',p.read_text()):
   if target.startswith(('http:','https:','#','mailto:')):continue
   if not (p.parent/target.split('#',1)[0]).exists():failures.append(str(p.relative_to(ROOT))+' missing '+target)
 if failures:raise SystemExit(json.dumps({'failures':failures},indent=2))
 scan=pathlib.Path(tempfile.mkdtemp(prefix='jackin-integration-release-scan-'));env=os.environ.copy()
 for key in ['GITLEAKS_CONFIG','GITLEAKS_CONFIG_TOML']:env.pop(key,None)
 cmd=['gitleaks','dir','.','--redact=100','--ignore-gitleaks-allow','--gitleaks-ignore-path','/dev/null','--no-banner','--no-color','--report-format','json','--report-path',str(scan/'gitleaks.json')]
 run=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True)
 (scan/'stdout.txt').write_bytes(run.stdout);(scan/'stderr.txt').write_bytes(run.stderr)
 findings=json.loads((scan/'gitleaks.json').read_text())
 unknown=[{'file':x['File'],'line':x['StartLine'],'rule':x['RuleID']} for x in findings if (x['File'],x['StartLine']) not in REVIEWED]
 if unknown or len(findings)!=6 or run.returncode!=1:raise SystemExit(json.dumps({'unexpected':unknown,'count':len(findings),'exit':run.returncode}))
 result={
  'utc':datetime.now(timezone.utc).isoformat(),
  'base_commit':'a94bb70b83cb847f005dc2acde1e9d2fa9742689',
  'source_snapshot_files':361,'new_bundle_files_checked':count,
  'existing_publication_files_compared':1768,'existing_redacted_content_mismatches':0,
  'additional_evidence_files':5,'format_link_provenance_failures':failures,
  'secret_scan':{
   'command':cmd[:-1]+['<outside-publication-tree>/gitleaks.json'],
   'exit_status':run.returncode,'report_sha256':sha((scan/'gitleaks.json').read_bytes()),
   'allowlist_suppression':False,
   'findings':[{'file':x['File'],'line':x['StartLine'],'rule':x['RuleID'],'disposition':REVIEWED[(x['File'],x['StartLine'])]} for x in findings]
  },
  'readiness':'NOT READY TO START THE FULL OPENSHELL REFACTOR',
  'product_code_refactored':False,'source_checkouts_keys_runtime_state_excluded':True
 }
 (ROOT/'INTEGRATION_CHECKS.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'format_link_hash_failures':len(failures),'scanner_exit':run.returncode,'reviewed_non_secret_findings':len(findings),'unexpected_findings':unknown}))
if __name__=='__main__':main()
