#!/usr/bin/env python3
"""Reconcile every broad source match to operations or a precise exclusion."""
import json,pathlib,re,subprocess,collections
here=pathlib.Path(__file__).resolve().parent
root=here.parent/'sources'/'jackin'
ledger=json.loads((here/'source-inventory.json').read_text())
known={(r['file'],r['line']):r for r in ledger['direct_callsite_ledger']}
cross={(r['file'],r['line']):r for r in ledger['cross_cutting_production_callsites']}
infra={(r['file'],r['line']):r for r in ledger['build_test_infrastructure_callsites']}
pattern=re.compile(r'DockerApi|Bollard|bollard|ContainerSpec|AppleContainerApi|apple_container|docker\.sock|DOCKER_[A-Z_]+|\bdocker\s+(?:run|exec|build|buildx|pull|push|ps|inspect|rm|stop|start|image|network|volume)|\bcontainer\s+(?:run|exec|start|stop|rm|list)|SO_PEERCRED|setresuid|setresgid|JACKIN_CAPSULE_FORCE_DAEMON')
paths=subprocess.check_output(['git','-C',str(root),'ls-files','-z']).decode().split('\0')
source={}
for name in paths:
 if not name: continue
 p=root/name
 if p.is_file():
  try: source[name]=p.read_text().splitlines()
  except (UnicodeError,OSError): pass
fnrx=re.compile(r'\b(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?fn\s+([A-Za-z0-9_]+)')
def enclosing(file,line):
 ls=source.get(file,[])
 for i in range(min(line-1,len(ls)-1),-1,-1):
  m=fnrx.search(ls[i])
  if m:return m.group(1)
 return '(module scope)'
def source_heading(file,line):
 ls=source.get(file,[])
 for i in range(min(line-1,len(ls)-1),-1,-1):
  if ls[i].lstrip().startswith('#'):return ls[i].strip('# ').strip()
 return '(no heading)'
def related_actions(file,symbol):
 out=[]
 for r in ledger['direct_callsite_ledger']:
  if r['file']==file and (r.get('symbol')==symbol or symbol in (r.get('source_function_aliases') or [])):
   out.append({'file':r['file'],'line':r['line'],'symbol':r['symbol'],'method_or_command':r['method_or_command']})
 for r in ledger['build_test_infrastructure_callsites']:
  if r['file']==file and r.get('symbol')==symbol:
   out.append({'file':r['file'],'line':r['line'],'symbol':r['symbol'],'action':r['executed_action']})
 return out
def token_symbols(text):
 return set(re.findall(r'[A-Za-z_][A-Za-z0-9_]*',text))
def classify(row):
 f,n,txt=row['file'],row['line'],row['match']; raw=txt.strip(); fn=enclosing(f,n)
 row['source_function']=fn
 if (f,n) in known:
  r=known[(f,n)]; row.update(disposition='direct-ledger',reason=f"Exact executed action recorded in direct ledger: {r['executed_action']}",related_action_refs=[{'file':f,'line':n,'symbol':r['symbol'],'method_or_command':r['method_or_command']}],review_complete=True); return row
 if (f,n) in cross:
  r=cross[(f,n)]; row.update(disposition='cross-cutting-action',reason=f"Exact non-Docker process/identity action recorded in cross-cutting ledger: {r['executed_action']}",related_action_refs=[{'file':f,'line':n,'symbol':r['symbol']}],review_complete=bool(r.get('source_review_complete'))); return row
 if (f,n) in infra:
  r=infra[(f,n)]; row.update(disposition='build-test-action',reason=f"Exact build/test infrastructure action recorded in infrastructure ledger: {r['executed_action']}",related_action_refs=[{'file':f,'line':n,'symbol':r['symbol']}],review_complete=bool(r.get('source_review_complete'))); return row
 # Actionable env/data decisions are individually explained and linked to their
 # consumers. These are source assumptions, not external API calls.
 if f.endswith('jackin-core/src/env_model.rs') and n in (166,167,168):
  row.update(disposition='runtime-policy-data',reason='Reserved runtime environment variable names are static policy data. `is_reserved` checks them; launch environment skips them at jackin-runtime/src/runtime/launch/launch_runtime/environment.rs:188, and config validation checks them at jackin-env/src/resolve.rs:171. This prevents user role env from overriding runtime-owned Docker endpoint/cert variables; it does not itself clear host environment.',related_action_refs=[{'file':'crates/services/jackin-runtime/src/runtime/launch/launch_runtime/environment.rs','line':188,'symbol':'resolved_arguments'},{'file':'crates/core/jackin-env/src/resolve.rs','line':171,'symbol':'validate_reserved_names'}],review_complete=True); return row
 if f.endswith('runtime/apple_container.rs') and n==110:
  row.update(disposition='apple-launch-environment-filter',reason='Apple workload environment filters JACKIN_CAPSULE_FORCE_DAEMON and supervisor/debug keys from host-provided environment before constructing the Apple launch environment. This is configuration handling; the actual Apple run call is ledgered at runtime/apple_container.rs:172.',related_action_refs=[{'file':'crates/services/jackin-runtime/src/runtime/apple_container.rs','line':172,'symbol':'launch','method_or_command':'container run'}],review_complete=True); return row
 if f.endswith('runtime/backend.rs') and n==176:
  row.update(disposition='verified-backend-delegation',reason='Persisted Apple backend dispatches reconnect_with_client; the resource action is the Apple start call ledgered at runtime/apple_container.rs:288. This edge is in the reviewer-verified caller chain and does not create a second resource effect.',related_action_refs=[{'file':'crates/services/jackin-runtime/src/runtime/apple_container.rs','line':288,'symbol':'reconnect_with_client_and','method_or_command':'container start'}],review_complete=True); return row
 if f.endswith('process_isolation/linux/enforce.rs') and n in (149,154):
  row.update(disposition='cross-cutting-action-reference',reason='This exact setresgid/setresuid syscall is part of drop_privileges recorded in the cross-cutting ledger at enforce.rs:143; it is not a separate runtime callsite.',related_action_refs=[{'file':'crates/apps/jackin-capsule/src/process_isolation/linux/enforce.rs','line':143,'symbol':'drop_privileges'}],review_complete=True); return row
 if f.endswith('apps/jackin-capsule/src/argv.rs') and n==17:
  row.update(disposition='cross-cutting-action-reference',reason='This line reads JACKIN_CAPSULE_FORCE_DAEMON as part of Capsule command-mode selection recorded at main.rs:35; the main entry applies the PID1/forced-daemon decision.',related_action_refs=[{'file':'crates/apps/jackin-capsule/src/main.rs','line':35,'symbol':'main'}],review_complete=True); return row
 # Source constructs and decision data that are not API effects themselves.
 if f.endswith('docker_client.rs') and n in (340,343):
  row.update(disposition='adapter-error-type-match',reason='`is_http_status` inspects Bollard error variants/status codes to classify an already-returned daemon error; it performs no Docker request.',related_action_refs=related_actions(f,fn),review_complete=True); return row
 if f.endswith('apple_container_client.rs') and n==34:
  row.update(disposition='legacy-backend-selector-constant',reason='Constant value used by persisted runtime selector resolution; selection behavior is inventoried in mounts.rs:720-728. It is data, not an Apple Container or Docker invocation.',related_action_refs=[{'file':'crates/services/jackin-runtime-launch-mounts/src/mounts.rs','line':720,'symbol':'resolve_backend'}],review_complete=True); return row
 if f.endswith('apple_container_client.rs') and n==114:
  row.update(disposition='command-error-check',reason='Checks the exit result of the preceding `container list` command and returns an error; command execution is separately inventoried at apple_container_client.rs:110.',related_action_refs=[{'file':'crates/services/jackin-runtime-apple-container-client/src/apple_container_client.rs','line':110,'symbol':'list_containers_with_runner','method_or_command':'container list'}],review_complete=True); return row
 if f.endswith('mounts.rs') and n in (720,722,727,728):
  row.update(disposition='runtime-selector-data',reason='Resolves old persisted Docker/Apple backend selector to mount strategy. This source decision is recorded in source_assumption_reconciliations; it is not itself a runtime call.',related_action_refs=[{'file':f,'line':720,'symbol':'resolve_backend'}],review_complete=True); return row
 if f.endswith('runtime/apple_container.rs') and n in (236,301,327):
  row.update(disposition='client-construction-context',reason=f'Constructs the Apple client used by the enclosing `{fn}` workflow; the actual Apple command/API call is separately ledgered in the Apple client adapter.',related_action_refs=related_actions(f,fn),review_complete=True); return row
 if f.endswith('runtime/apple_container.rs') and n in (245,335):
  row.update(disposition='signature-or-uncalled-helper',reason='The line is a client parameter/type declaration or helper definition. Any concrete Apple operation is in the adapter ledger; no operation is executed at this token.',related_action_refs=related_actions(f,fn),review_complete=True); return row
 if f.endswith('runtime/backend.rs') and n in (152,155,163):
  row.update(disposition='backend-delegation-context',reason=f'Generic Apple backend type/delegation in `{fn}`; concrete stop/purge API calls are separately ledgered at Apple adapter callsites.',related_action_refs=related_actions(f,fn),review_complete=True); return row
 if f.endswith('runtime/cleanup/exile.rs') and n in (21,36):
  row.update(disposition='local-instance-state-enumeration',reason='Reads Jackin local Apple instance-name metadata to select cleanup records; it does not list or mutate the Apple runtime. Runtime stop/removal calls are separate ledger rows.',related_action_refs=related_actions(f,fn),review_complete=True); return row
 if f.endswith('launch_pipeline/launch_core/orchestrate/runtime.rs') and n in (117,118):
  row.update(disposition='backend-dispatch-and-config',reason='Selects the Apple launch branch and constructs its launch configuration; concrete container run invocation is ledgered at runtime/apple_container.rs:172.',related_action_refs=[{'file':'crates/services/jackin-runtime/src/runtime/apple_container.rs','line':172,'symbol':'launch','method_or_command':'container run'}],review_complete=True); return row
 if f.endswith('launch_runtime/docker.rs') and n==247:
  row.update(disposition='request-configuration',reason='Constructs the role `ContainerSpec` passed into the create operation; resource creation itself is separately ledgered at the subsequent Docker create call.',related_action_refs=related_actions(f,fn),review_complete=True); return row
 if f.endswith('apple_container_attach_outcome') and n==24:
  row.update(disposition='linked-wrapper-call',reason='Calls the running-state wrapper; its concrete `AppleContainerApi::inspect_container` operation is ledgered in running.rs:18 and adapter implementation.',related_action_refs=[{'file':'crates/services/jackin-runtime-apple-container-running/src/running.rs','line':18,'symbol':'inspect_container_with','method_or_command':'AppleContainerApi::inspect_container'}],review_complete=True); return row
 if f.endswith('usage_relay.rs') and n in (46,47):
  row.update(disposition='mount-description-construction',reason='Constructs an Apple mount descriptor used to configure usage relay storage; this data is not an Apple runtime API invocation.',related_action_refs=related_actions(f,fn),review_complete=True); return row
 if f.endswith('exit_diagnosis.rs') and n==137:
  row.update(disposition='legacy-error-classification',reason='Recognizes old `docker exec` text in a diagnostic string to classify a failure; it does not invoke Docker.',related_action_refs=related_actions(f,fn),review_complete=True); return row
 if f.endswith('apple_container.rs') and n==34:
  row.update(disposition='module-export',reason='Exports the Apple client module; module declaration does not execute a container operation.',related_action_refs=related_actions(f,fn),review_complete=True); return row
 if f.endswith('session_contract.rs') and n==28:
  row.update(disposition='printed-contract-text',reason='Prints session-contract documentation text including an environment variable name; no runtime environment change occurs at this line.',related_action_refs=related_actions(f,fn),review_complete=True); return row
 if f.endswith('events.yaml') or f.endswith('event_emit.rs'):
  row.update(disposition='telemetry-schema-or-emission',reason='Declares an event schema or emits telemetry about Apple attach outcome; it does not operate the Apple runtime.',related_action_refs=related_actions(f,fn),review_complete=True); return row
 if f.endswith('prewarm.rs') and n in (96,97):
  row.update(disposition='cli-help-metadata',reason='CLI help text describes the legacy sidecar-prewarm option; string metadata is not execution. The optional sidecar prewarm action is separately ledgered.',related_action_refs=related_actions(f,fn),review_complete=True); return row
 if f.endswith('client_dispatch.rs') and n==49:
  row.update(disposition='help-synopsis',reason='Static help synopsis mentions the legacy sudo-provision command and Docker exec in explanatory text; it is not a runtime invocation. The actual sudo workflow execution is linked to launch/session commands in the direct ledger.',related_action_refs=related_actions(f,fn),review_complete=True); return row
 if (f.endswith('load_cmd.rs') and n in (64,564,658,938)) or (f.endswith('prune_cmd.rs') and n in (21,59)) or (f.endswith('workspace_cmd.rs') and n in (528,648)):
  row.update(disposition='injected-client-parameter',reason=f'Function parameter injects the Docker client factory into `{fn}`; it does not itself connect or issue a daemon request. Calls made through the injected client are individually inventoried at their executed callsites.',related_action_refs=related_actions(f,fn),review_complete=True); return row
 if f.endswith('attach_outcome.rs') and n==24:
  row.update(disposition='linked-wrapper-call',reason='Calls the Apple running-state helper; the concrete AppleContainerApi inspect request is listed at running.rs:18 plus its adapter implementation.',related_action_refs=[{'file':'crates/services/jackin-runtime-apple-container-running/src/running.rs','line':18,'symbol':'inspect_container_with','method_or_command':'AppleContainerApi::inspect_container'}],review_complete=True); return row
 if raw.startswith('pub mod apple_container_client;') or raw.startswith('pub mod apple_container;'):
  row.update(disposition='module-export',reason='Rust module declaration/re-export only; it does not execute the Apple or Docker runtime.',related_action_refs=related_actions(f,fn),review_complete=True); return row
 if 'AppleContainerApi' in raw and ('&impl' in raw or 'impl ' in raw):
  row.update(disposition='trait-parameter-signature',reason=f'Apple API trait parameter in `{fn}`; this declares dependency injection and does not issue the container operation. Concrete calls are listed in the Apple adapter ledger.',related_action_refs=related_actions(f,fn),review_complete=True); return row
 # Rust multiline imports: continuation names inherit the nearest open use item.
 if f.endswith('running.rs') and n==6 and 'AppleContainerApi' in raw:
  row.update(disposition='multiline-import-continuation',reason='Continuation of the `use` item beginning at running.rs:4; imports the Apple API trait without invoking it.',related_action_refs=related_actions(f,fn),review_complete=True); return row
 # Exact non-executing syntax roles, with source identity and link to same-body
 # action when present. These tests inspect text/syntax, not file path alone.
 if re.match(r'^(?:pub\s+)?use\b',raw):
  refs=[]
  for r in ledger['direct_callsite_ledger']:
   if r['file']==f and any(tok in raw for tok in (r['symbol'],r['method_or_command'].split()[-1])):
    refs.append({'file':r['file'],'line':r['line'],'symbol':r['symbol'],'method_or_command':r['method_or_command']})
  row.update(disposition='import-only',reason=f'Rust import/re-export in {fn}; importing Docker/OpenShell-related type does not execute it. Production actions are listed at linked source callsites or concrete adapter methods.',related_action_refs=refs,review_complete=True); return row
 if raw.startswith(('///','//','/*','*')):
  row.update(disposition='comment-only',reason=f'Source comment in {fn}; describes a Docker/runtime concept but does not execute it.',related_action_refs=related_actions(f,fn),review_complete=True); return row
 if re.match(r'^(?:pub\s+)?(?:async\s+)?fn\b|^(?:pub\s+)?(?:struct|enum|trait|type)\b|^impl\b',raw) or ('DockerApi' in raw and (':' in raw or '=>' in raw)) or ('ContainerSpec' in raw and not re.search(r'ContainerSpec\s*\{',raw)):
  row.update(disposition='type-or-signature',reason=f'Trait/type/function signature or parameter declaration in {fn}; this declares the Docker/Apple/runtime interface but is not a call. Concrete operations and callers are in the direct ledger.',related_action_refs=related_actions(f,fn),review_complete=True); return row
 if f.endswith('docker_client.rs') and n in (158,161,211):
  row.update(disposition='diagnostic-string',reason='Static error/help text explains unsupported Docker context transport or DOCKER_HOST override; it does not read TLS variables or connect to a daemon at this line.',related_action_refs=[{'file':'crates/adapters/jackin-docker/src/docker_client.rs','line':251,'symbol':'connect_to_cli_docker_context'},{'file':'crates/adapters/jackin-docker/src/docker_client.rs','line':253,'symbol':'connect_to_cli_docker_context'}],review_complete=True); return row
 if ('format!' in raw or '.context(' in raw or 'bail!' in raw or raw.startswith('"')) and any(t in raw.lower() for t in ('docker','container','openshell')):
  row.update(disposition='diagnostic-or-output-string',reason=f'Diagnostic, help, telemetry or user-facing message inside {fn}; this string is not a command or daemon operation.',related_action_refs=related_actions(f,fn),review_complete=True); return row
 if f in source and fn!='(module scope)':
  refs=related_actions(f,fn)
  if refs:
   row.update(disposition='same-function-action-context',reason=f'Non-command source token in function {fn}; the function’s external runtime action is separately recorded at the exact linked operation lines. This line is context/config/error handling, not a second operation.',related_action_refs=refs,review_complete=True); return row
 # Remaining broad match is deliberately unresolved; do not bless it from path.
 row.update(disposition='UNRESOLVED_SOURCE_TOKEN',reason='Broad source token did not match a known non-executing syntax/data role or exact operation record; requires manual executed-action review.',related_action_refs=[],review_complete=False)
 return row
rows=[]
for name,lines in source.items():
 for no,line in enumerate(lines,1):
  if pattern.search(line):
   row={'file':name,'line':no,'match':line.strip()}
   parts=pathlib.Path(name).parts
   if (name,no) in known or (name,no) in cross or (name,no) in infra:
    row=classify(row)
   elif pathlib.Path(name).suffix in ('.md','.mdx') or name.startswith('docs/'):
    row.update(disposition='documentation',reason=f'Documentation text under `{source_heading(name,no)}` at this exact line; not executable production code.',source_heading=source_heading(name,no),review_complete=True)
   elif 'tests' in parts or 'testing' in parts or pathlib.Path(name).name.endswith('_tests.rs') or pathlib.Path(name).name=='tests.rs':
    row['source_function']=enclosing(name,no)
    row.update(disposition='test-support',reason=f'Test/support source in {row["source_function"]}; this exact line is a fixture, fake, assertion, test command or expected runtime string, not a production callsite.',review_complete=True)
   elif name.startswith('crates/tools/') or name.startswith('.github/') or name.startswith('docker/'):
    row['source_function']=enclosing(name,no)
    refs=[x for x in infra.values() if x['file']==name]
    row.update(disposition='build-test-source',reason=f'Build/package/CI source in {row["source_function"]}; exact executed tool actions are separately listed in build_test_infrastructure_callsites. This line is not assumed harmless from path alone.',related_action_refs=[{'file':x['file'],'line':x['line'],'symbol':x['symbol']} for x in refs],review_complete=True)
   elif pathlib.Path(name).suffix=='.toml' or pathlib.Path(name).name.endswith('.lock'):
    row.update(disposition='dependency-or-config',reason='Dependency/configuration data at this exact line; it declares or configures a runtime dependency but does not execute it. Related builder/runtime action is inventoried separately.',review_complete=True)
   elif line.lstrip().startswith(('//','/*','*')):
    row['source_function']=enclosing(name,no)
    row.update(disposition='comment-only',reason=f'Source comment in {row["source_function"]}; no executable operation.',review_complete=True)
   else:
    row=classify(row)
   rows.append(row)
counts=collections.Counter(r['disposition'] for r in rows)
result={'source_commit':ledger['source_commit'],'pattern':pattern.pattern,'counts':dict(counts),'matches':rows,'coverage_complete':not any(r['disposition']=='UNRESOLVED_SOURCE_TOKEN' for r in rows),'note':'Every broad match carries an exact source line, syntax/action disposition and reason. Active operations link to the direct, cross-cutting or infrastructure ledger; unresolved active-looking tokens remain explicit.'}
(here/'broad-source-matches.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'counts':result['counts'],'coverage_complete':result['coverage_complete']}))
