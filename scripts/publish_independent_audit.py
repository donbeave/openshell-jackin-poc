#!/usr/bin/env python3
"""Publish the frozen independent audit with narrow redaction and provenance.

Uses the source artifact manifest; never traverses source clones or key/state
folders. Existing destination files are preserved by refusing a second copy.
"""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,pathlib,re,socket,platform,os
from datetime import datetime,timezone

ROOT=pathlib.Path(__file__).resolve().parents[1]
DEST_REL=pathlib.Path('research/independent-audit-20261024')
def digest(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def main()->None:
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);args=p.parse_args()
 source=pathlib.Path(args.source).resolve();dest=ROOT/DEST_REL
 if dest.exists():raise SystemExit('Destination exists; refusing to overwrite research.')
 manifest=json.loads((source/'ARTIFACT_MANIFEST.json').read_text())
 spec=importlib.util.spec_from_file_location('publication_redactor',ROOT/'scripts/refresh_publication_stage.py')
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 hostnames={socket.gethostname(),socket.getfqdn(),platform.node()}
 hostnames|={x.split('.')[0] for x in hostnames if '.' in x and len(x.split('.')[0])>8}
 hostnames-={'','localhost','localhost.localdomain'}
 replacements=[(str(pathlib.Path.home()),'/Users/example')]+[(x,'<HOST>') for x in sorted(hostnames,key=len,reverse=True)]
 # Include escaped JSON strings embedded in raw CLI stdout, preserving all
 # other UUIDs (sandbox, generation, request, subject) as evidence identities.
 authority_id=re.compile(r'(?P<prefix>\\?"[^"\s]*(?:gateway-token-id|token-reference|token_reference)\\?"\s*:\s*\\?")(?P<uuid>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})(?P<suffix>\\?")')
 rows=[]
 for record in manifest['files']:
  rel=pathlib.PurePosixPath(record['path'])
  if rel.is_absolute() or '..' in rel.parts:raise SystemExit('Unsafe source manifest path')
  if rel.parts[0]=='sources' or any(x in rel.parts for x in ['.git','__pycache__','certs','state','config','.venv','target']):raise SystemExit(f'Unexpected private/generated manifest member: {rel}')
  if rel.suffix.lower() in {'.key','.pem','.p12','.pfx','.crt','.pyc','.dmg','.exe','.dylib','.so'}:raise SystemExit(f'Unexpected key/binary member: {rel}')
  src=source/str(rel)
  if src.is_symlink() or not src.is_file():raise SystemExit(f'Nonregular source: {rel}')
  raw=src.read_bytes()
  if digest(raw)!=record['sha256']:raise SystemExit(f'Frozen source changed: {rel}')
  text=raw.decode('utf-8')
  if '\x00' in text:raise SystemExit(f'Binary member: {rel}')
  if re.search(r'-----BEGIN (?:[A-Z ]*PRIVATE KEY|CERTIFICATE)-----',text):raise SystemExit(f'Unexpected PEM material: {rel}')
  published,redactions=module.redact_text(text,replacements,str(rel))
  published,count=authority_id.subn(r'\g<prefix>00000000-0000-0000-0000-000000000000\g<suffix>',published)
  if count:redactions.append(f'escaped-authority-reference:{count}')
  if str(rel)=='README.md':
   published='> **Scope note:** this is the independently reviewed audit snapshot. Read the [merged research index](../../RESEARCH_INDEX.md) and [consolidated readiness report](../../READINESS_REPORT.md) for later execution proofs and the current overall decision. Earlier NOT TESTED entries remain accurate for this snapshot, not a claim that the later experiments never ran.\n\n'+published
   redactions.append('publication-scope-banner')
  target=dest/str(rel);target.parent.mkdir(parents=True,exist_ok=True);target.write_text(published)
  os.chmod(target,src.stat().st_mode&0o755)
  rows.append({'path':str(DEST_REL/str(rel)),'source_relative_path':str(rel),'source_sha256':digest(raw),'published_sha256':digest(published.encode()),'published_bytes':len(published.encode()),'redactions':redactions})
 # Original hashes describe the private-path source snapshot. Do not present
 # them as hashes of the sanitized public bytes.
 source_manifest=(source/'ARTIFACT_MANIFEST.json').read_bytes()
 (dest/'SOURCE_ARTIFACT_MANIFEST.json').write_bytes(source_manifest)
 metadata={'utc':datetime.now(timezone.utc).isoformat(),'source_snapshot_manifest_sha256':digest(source_manifest),'baseline_public_commit':'a94bb70b83cb847f005dc2acde1e9d2fa9742689','included_source_files':len(rows),'source_directories_excluded_before_read':['sources/**','**/.git/**','**/__pycache__/**','generated credentials and runtime state'],'source_bytes_preserved_locally':True,'redaction_policy':'Personal home paths/hostnames and authority token-reference UUIDs only; recognized secret patterns redacted. Sandbox/request/generation IDs preserved.','files':rows}
 (dest/'PUBLICATION_PROVENANCE.json').write_text(json.dumps(metadata,indent=2)+'\n')
 print(json.dumps({'destination':str(DEST_REL),'source_files':len(rows),'published_bytes':sum(x['published_bytes'] for x in rows),'redacted_files':sum(bool(x['redactions']) for x in rows)}))
if __name__=='__main__':main()
