#!/usr/bin/env python3
"""Build raw-match and per-line production runtime callsite review ledgers."""
import json, pathlib, re, subprocess, collections
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parent/'sources'/'jackin'
COMMIT=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()
RAW=re.compile(r'DockerApi|BollardDockerClient|bollard|docker (?:run|exec|ps|inspect|rm|stop|start|image|network|volume)|Command::new\("docker"\)|container (?:run|exec|start|stop|rm|list)|Command::new\("container"\)|DOCKER_HOST|docker\.sock')
DIRECT=re.compile(r'(?:\bdocker\.(?:create_container|start_container_by_id|stop_container_by_id|remove_container_by_id|inspect_container_by_id|inspect_container_by_name|list_containers|create_network|remove_network|inspect_network|list_networks|create_volume|remove_volume|pull_image|list_image_tags|inspect_image_labels|remove_image|pause_container_by_id|unpause_container_by_id|kill_container_by_id|restart_container_by_id|wait_container|exec_capture_by_id)|(?:runner|self\.runner)\.run\("docker"|Command::new\("docker"|Command::new\("container"|BollardDockerClient::connect\(|jackin_docker::docker_client::BollardDockerClient::connect\(|docker\.ping\(|ExecRequest::new\("docker"|\.(?:create_container|start_container_by_id|stop_container_by_id|remove_container_by_id|inspect_container_by_id|inspect_container_by_name|list_containers|create_network|remove_network|inspect_network|list_networks|create_volume|remove_volume|pull_image|list_image_tags|inspect_image_labels|remove_image|pause_container_by_id|unpause_container_by_id|kill_container_by_id|restart_container_by_id|wait_container|exec_capture_by_id)\s*\()')
EXCLUDED={'tests','test','testing','target'}
METHODS=['create_container','start_container_by_id','stop_container_by_id','remove_container_by_id','inspect_container_by_id','inspect_container_by_name','list_containers','create_network','remove_network','inspect_network','list_networks','create_volume','remove_volume','pull_image','list_image_tags','inspect_image_labels','remove_image','pause_container_by_id','unpause_container_by_id','kill_container_by_id','restart_container_by_id','wait_container','ping','BollardDockerClient::connect','jackin_docker::docker_client::BollardDockerClient::connect','docker.ping','ExecRequest::new("docker"','exec_capture_by_id','runner.run("docker"' ,'BollardDockerClient::connect','jackin_docker::docker_client::BollardDockerClient::connect','docker.ping','ExecRequest::new("docker"','Command::new("docker"','Command::new("container"','runner.capture(']

def skip(p): return any(x in p.parts for x in EXCLUDED) or p.name.endswith('_tests.rs') or p.name == 'tests.rs'
def symbol_at(lines,idx):
    # nearest enclosing-looking fn signature; Rust braces are not parsed, so
    # only accept declarations before the hit and avoid claiming exact nesting.
    for j in range(idx,-1,-1):
        m=re.search(r'\b(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?fn\s+([A-Za-z0-9_]+)',lines[j])
        if m:return m.group(1)
    return '(module scope)'
def map_row(path,line,sym,text):
    if 'jackin-workflow/src/verify.rs' in path:
        a='Provision, execute, inspect, bound output/time and remove isolated verification worker.'; c='jackin-workflow service invokes run_test_command.'; o='Docker host daemon worker container.'; n='OpenShell sandbox; Jackin retains exact command policy and result recording; no fallback.'; e='No OpenShell worker proof.'; t='Success/failure/timeout/abnormal/unavailable/interrupted with frozen image, controls, exit state and cleanup.'; k='active; OpenShell replacement unproved'
    elif 'jackin-runtime-image/src/image/version.rs' in path:
        a='Run selected agent binary via docker run to obtain --version when metadata absent.'; c='Image build record_built_agent_version fallback.'; o='Builder daemon executes agent process.'; n='Remove; verified install metadata, else OpenShell sandbox exec.'; e='Version command is not authenticated agent evidence; fallback untested.'; t='No-prefetch installation; exact executed version equals build metadata and image digest.'; k='active legacy agent execution; remove'
    elif 'jackin-runtime-image/src/image/' in path:
        a='Build/tag/inspect/pull/list image or prepare image cache.'; c='Role load and prewarm.'; o='Docker/Buildx builder.'; n='Retain builder only; OpenShell target gets image by digest.'; e='Prior small image build/same engine only; full Architect and remote delivery not proved.'; t='Actual Architect builds/version/cache/registry auth/arch/interrupt/digest execution.'; k='active builder'
    elif 'jackin-runtime-launch-dind' in path or 'cleanup-dind-gc' in path or 'cleanup-eject-resources' in path:
        a='Manage optional per-instance engine, network, cert volume and orphan cleanup.'; c='Conditional Docker-grant launch; eject/exile/prune/explicit prewarm.'; o='Jackin sidecar manager plus Docker daemon.'; n='Replace old manager after OpenShell-compatible owner is proven; capability off by default.'; e='Only external daemon forwarding proved; managed ownership not.'; t='Enabled and denied-default Docker matrix, Testcontainers, Compose, isolation, cost, restart/cleanup.'; k='active; required managed mechanism unresolved'
    elif 'jackin-runtime/src/runtime/launch' in path or 'jackin-runtime-launch-' in path:
        a='Resolve/create/start/inspect/remove role workload and post-run setup.'; c='load/hardline recovery role launch.'; o='Local Docker engine role container.'; n='OpenShell target create/get/exec/stop/delete; Jackin retains policy and account logic.'; e='OpenShell primitives only, no Jackin role launch.'; t='Actual role hooks, identity, cwd/env, account admission, limits, readiness, failure cleanup.'; k='active; replacement untested'
    elif 'jackin-runtime/src/runtime/attach' in path or 'jackin-runtime-attach' in path or 'jackin-runtime-snapshot' in path or 'jackin-runtime-session-control' in path or 'host-attach' in path:
        a='Inspect readiness/identity or use Capsule for sessions, events, snapshots, usage, attach.'; c='load/hardline/status/console/session commands.'; o='Docker resource plus Capsule daemon/socket.'; n='OpenShell immutable sandbox identity plus selected proven streaming transport.'; e='OpenShell CLI terminal primitives do not prove Capsule/Rust route.'; t='Protocol frame replay, exact identity race, binary IO, focus/control, reconnect, signal and child lifetime.'; k='active; replacement untested'
    elif 'cleanup-' in path or '/cleanup/' in path:
        a='Inspect/remove role or owned resources for failure/eject/exile/purge/prune.'; c='Lifecycle CLI and failed-launch recovery.'; o='Docker and Jackin local state ledger.'; n='OpenShell lifecycle + immutable receipts; Jackin retains safe retention decision.'; e='Basic async deletion exists in prior POC; Jackin recovery not.'; t='Fault transitions; unavailable/unauthorized vs absent; protect holds/active/foreign; confirm deletion.'; k='active; lifecycle parity untested'
    elif any(x in path for x in ['jackin-runtime-discovery','jackin-runtime-attach-inspect','jackin-runtime-universe','jackin-runtime-drift','jackin-runtime-launch-slot']):
        a='Discover/reconcile/inspect workload or claim first/last instance membership.'; c='Console/status/load/workspace/host awake.'; o='Docker inventory plus Jackin local manifests.'; n='Target-keyed OpenShell inventory and Jackin fleet registry.'; e='No multi-target evidence.'; t='Two gateways, stale/lost events, independent outage, host first/last concurrency.'; k='active; distributed behavior unproved'
    elif 'jackin-host' in path:
        a='Count managed workloads for host keep-awake.'; c='load/reconnect/finalization.'; o='Docker inventory and local Darwin caffeinate.'; n='Target-aware logical membership; keep action on correct desktop.'; e='No multi-target concurrency proof.'; t='Two targets concurrent entry/exit, client crash, reconcile.'; k='active Darwin behavior; adaptation untested'
    elif 'jackin-isolation' in path:
        a='Pause/inspect/resume workload for checkpoint capture.'; c='No production caller found for capture_checkpoint; status must remain foundation pending call graph.'; o='Docker resource and local storage.'; n='Retain workspace materialization; replace mounts. Do not activate checkpoint implicitly.'; e='No live mount/capture barrier proof.'; t='If production caller found: prove write barrier; otherwise release test for not exposed.'; k='implemented; production caller unproved'
    elif 'apps/jackin/src/preflight.rs' in path:
        a='Probe Docker daemon or enumerate managed resources during prerequisites.'; c='load/hardline/eject/exile/purge/prune preflight and doctor.'; o='Local Docker daemon as global requirement.'; n='Separate target gateway, Docker builder, optional engine health.'; e='No split-health experiment.'; t='Reachable target while separate builder down; rebuild error attributed to builder.'; k='active coupling'
    elif path.startswith('crates/apps/jackin/'):
        a='Connect Docker for CLI/console command operation.'; c='Command dispatch in app.rs and corresponding CLI/console entry.'; o='Local DockerApi passed into product logic.'; n='Inject target client; builder and optional engine clients scoped by capability.'; e='Jackin CLI over OpenShell untested.'; t='Command contract, multi-target state, independent health.'; k='active; replacement untested'
    else:
        a='Docker engine adapter executes the corresponding Docker API operation.'; c='Concrete BollardDockerClient implementation consumed by production callers.'; o='Bollard connection selected from Docker context/env.'; n='Split narrow OpenShell target, builder-only Docker, explicit optional engine adapters.'; e='No Jackin adapter integration proof.'; t='Operation contract tests plus TLS identity failure/rotation and target action race.'; k='active adapter; replacement untested'
    meth=next((m for m in METHODS if re.search(r'\b'+re.escape(m)+r'\b',text)),'source operation')
    return {'file':path,'line':line,'symbol':sym,'source':text.strip(),'method_or_command':meth,'executed_action':f'{meth}: {a}','production_caller_entry':c,'current_resource_owner':o,'required_user_outcome':'Preserve the workflow contract described by this operation cluster.','proposed_replacement_owner_and_mechanism':n,'evidence_or_experiment':e,'release_acceptance_test':t,'source_classification':k,'source_action_reviewed':True,'caller_chain_reviewed':False,'review_complete':False}
raw=[]; ledger=[]; excluded=[]
for p in ROOT.glob('crates/**/*.rs'):
    rel=p.relative_to(ROOT); lines=p.read_text(errors='replace').splitlines()
    for i,text in enumerate(lines,1):
        if RAW.search(text):
            reason=None
            if skip(rel): reason='Test/support source: fixtures, assertions or fake adapter; not production execution.'
            elif '/docs/' in str(rel): reason='Documentation only.'
            if reason: excluded.append({'file':str(rel),'line':i,'reason':reason,'review_complete':True})
            else: raw.append({'file':str(rel),'line':i,'match':text.strip()})
        if (DIRECT.search(text) or (str(rel).endswith('image/version.rs') and i==52) or (str(rel).endswith('preflight.rs') and i in (190,))) and not skip(rel): ledger.append(map_row(str(rel),i,symbol_at(lines,i-1),text.strip()))
# Explicit Apple Container production operations: dynamic command string hides CLI verb from generic pattern.
rel='crates/services/jackin-runtime-apple-container-client/src/apple_container_client.rs'; lines=(ROOT/rel).read_text().splitlines()
for i,text in enumerate(lines,1):
    if i in (164,181,185,189,193,198):
        method=re.search(r'async fn (\w+)',text).group(1)
        ledger.append({'file':rel,'line':i,'symbol':method,'method_or_command':{'run_container':'container run','start_container':'container start','stop_container':'container stop','remove_container':'container rm','inspect_container':'container inspect','list_containers':'container list --all --format json'}[method],'executed_action':f'Apple Container client executes {method} through process telemetry.','production_caller_entry':'Persisted Apple backend dispatch from load/hardline/eject; backend finalization is explicit Phase 0 incomplete.','current_resource_owner':'Apple Container CLI runtime; Jackin manifest names backend/resources.','required_user_outcome':'Role sandbox lifecycle and target status.','proposed_replacement_owner_and_mechanism':'Remove Apple adapter/backend dispatch; OpenShell gateway target owns sandbox; Jackin keeps logical state.','evidence_or_experiment':'Apple client command unit mocks only; packaged OpenShell VM evidence is distinct and does not establish Apple parity.','release_acceptance_test':'Actual supported Mac target: fresh setup, launch, status, stop/start, remove, state and recovery.','source_classification':'active Apple path; finalization incomplete','review_complete':True})
# Add production Apple CLI calls, whose verb is in a dynamic argument vector.
rel='crates/services/jackin-runtime-apple-container-client/src/apple_container_client.rs'; lines=(ROOT/rel).read_text().splitlines()
for i,text in enumerate(lines,1):
    if i in (164,181,185,189,193,198):
        method=re.search(r'async fn (\w+)',text).group(1)
        verbs={'run_container':'container run','start_container':'container start','stop_container':'container stop','remove_container':'container rm','inspect_container':'container inspect','list_containers':'container list --all --format json'}
        ledger.append({'file':rel,'line':i,'symbol':method,'method_or_command':verbs[method],'executed_action':f'{verbs[method]} through process telemetry.','production_caller_entry':'Persisted Apple backend dispatch via load/hardline/eject; finalization explicitly incomplete.','current_resource_owner':'Apple Container CLI and Jackin resource manifest.','required_user_outcome':'Role sandbox lifecycle, inventory and status.','proposed_replacement_owner_and_mechanism':'Remove Apple client/backend; OpenShell gateway target owns sandbox, Jackin keeps logical identity/lifecycle.','evidence_or_experiment':'Apple command mock tests only; OpenShell packaged VM experiment is a different driver.','release_acceptance_test':'Supported Mac target launch, status, stop/start/delete, mounts, persistence and recovery.','source_classification':'active Apple backend; finalization incomplete','source_action_reviewed':True,'caller_chain_reviewed':False,'review_complete':False})
# Correct operation-specific owner/action for distinct runtime operations.
for r in ledger:
    if r['file'].endswith('jackin-isolation/src/finalize.rs') and r['line']==275:
        r.update(executed_action='Exec the Jackin status command in the role container and parse the session count before cleanup. On command failure or unparsable output, conservatively treat sessions as present and preserve isolation work.',production_caller_entry='Active static callers: isolation/finalize.rs:222 finalize_foreground_session -> :275 has_jackin_sessions_by_id; runtime/attach/finalize.rs:97 and :154 call finalize_foreground_session; runtime/launch/launch_pipeline/launch_core/orchestrate/finalize.rs:99 and :146 also call it. Caller routes confirmed in the shared route table.',current_resource_owner='Jackin isolation finalization logic owns the preservation decision; Docker exec currently reads Capsule session status.',required_user_outcome='Avoid deleting isolation work when the process may still have Jackin sessions or status cannot be trusted.',proposed_replacement_owner_and_mechanism='Retain Jackin fail-closed preservation decision. Replace Docker exec with authenticated target-scoped OpenShell sandbox exec/status transport only after session status protocol and identity are proved.',required_code_change='Keep status-check failure and parse failure as sessions-present; route status through target + immutable sandbox identity and preserve work if target/status is unavailable.',evidence_or_experiment='Pinned source confirms the active call and fail-closed branches; no OpenShell status transport or live retention experiment proves replacement.',release_acceptance_test='Exercise zero/nonzero/unparseable status, exec failure, missing/unavailable sandbox, and stale identity; all uncertain states preserve work, clean zero-session state follows existing policy.')
    f=r['file']; sym=r['symbol']; meth=r['method_or_command']
    if 'reconnect_lease.rs' in f and sym=='restart_stopped_dind_if_needed':
        r.update(executed_action=('Inspect the separately owned DIND container by immutable Docker ID.' if 'inspect_' in meth else 'Restart the stopped optional DIND sidecar by immutable Docker ID.'),current_resource_owner='Optional Jackin-owned DIND sidecar; Docker network and certificates recorded in instance resource state.',required_user_outcome='Restore granted Docker capability when reconnecting a stopped role.',proposed_replacement_owner_and_mechanism='Retain explicit optional capability decision; use selected managed Docker companion ownership model and OpenShell target receipt.')
    if 'launch_pipeline.rs' in f and sym=='teardown_recreate_container' and meth=='remove_network':
        r.update(executed_action='Remove the Jackin-owned per-role network after role and optional DIND containers are removed.',current_resource_owner='Docker network recorded in the role resource manifest.',required_user_outcome='Recreate a clean role runtime without deleting unrelated networks.',proposed_replacement_owner_and_mechanism='Jackin ownership receipt coordinates sandbox and any explicit Docker capability network teardown; require confirmed delete.')
    if 'verify.rs' in f:
        details={532:('Remove the verification container after execution timeout.','OpenShell owned worker sandbox deletion after process-group termination.'),575:('Inspect availability of exact pinned verification image.','Target image digest lookup/pull; Docker retained only as builder where appropriate.'),583:('Pull pinned verification worker image.','Transfer or resolve exact digest to selected OpenShell target.'),605:('Inspect worker state and actual exit status.','OpenShell wait/get execution result; confirm actual process exit.'),615:('Remove completed verification container.','Delete owned OpenShell worker and wait for completion.'),776:('Start worker with exact approved command, readonly mounts and resource limits.','Create OpenShell worker sandbox with enforced policy; Jackin records exact argv.'),858:('Drop guard force-removes worker on early return.','Owned OpenShell deletion receipt with interruption recovery.')}
        if r['line'] in details:
            r['executed_action'],r['proposed_replacement_owner_and_mechanism']=details[r['line']]
            r['required_user_outcome']='Run approved workflow check isolated; bind result to candidate and trusted checks.'
# Apple backend wrapper callsites, separate from CLI execution implementation.
for rel, sites in {
 'crates/services/jackin-runtime/src/runtime/apple_container.rs':[(172,'launch_apple_container','container run'),(288,'ensure_running_with','container start'),(312,'ensure_absent_for_purge_with','container list'),(345,'remove_with','container stop'),(346,'remove_with','container rm')],
}.items():
 lines=(ROOT/rel).read_text().splitlines()
 for line_no,symbol,verb in sites:
  ledger.append({'file':rel,'line':line_no,'symbol':symbol,'source':lines[line_no-1].strip(),'method_or_command':verb,'executed_action':f'Apple backend calls {verb} after target-state checks.','production_caller_entry':'Persisted Apple backend launch/reconnect/eject/purge dispatch from user load, hardline, eject and purge.','current_resource_owner':'Apple Container CLI; Jackin manifest and lifecycle code.','required_user_outcome':'Launch/reconnect/stop/remove Apple-selected role while preserving state rules.','proposed_replacement_owner_and_mechanism':'Delete Apple dispatch and client; OpenShell target owns sandbox actions, Jackin logical lifecycle retained.','evidence_or_experiment':'No Apple runtime execution evidence; OpenShell VM driver is separate.','release_acceptance_test':'Run each workflow on actual supported Mac host against OpenShell target and retained-state contract.','source_classification':'active Apple dispatch; finalize path incomplete','source_action_reviewed':True,'caller_chain_reviewed':False,'review_complete':False})
# Direct process commands are sometimes built from ExecRequest rather than Command::new.
for rel,line_no,symbol,verb,action in [
 ('crates/apps/jackin/src/preflight.rs',190,'check_docker_daemon','DockerApi.connect + ping','Test whether local builder/engine daemon is reachable.'),
 ('crates/apps/jackin/src/preflight.rs',210,'report_docker_version','docker version --format','Report builder daemon version.'),
 ('crates/services/jackin-runtime-image/src/image/version.rs',52,'extract_agent_version','docker run --rm --entrypoint <agent> <image> --version','Execute agent in builder container to probe version.')]:
 lines=(ROOT/rel).read_text().splitlines()
 ledger.append({'file':rel,'line':line_no,'symbol':symbol,'source':lines[line_no-1].strip(),'method_or_command':verb,'executed_action':action,'production_caller_entry':'Image build or command prerequisite path; see source function.' if 'image/' in rel else 'Required preflight for management paths; doctor includes separate version check.','current_resource_owner':'Docker builder/daemon.' if 'preflight' in rel else 'Docker builder.' ,'required_user_outcome':'Correctly diagnose builder readiness and installed agent version.','proposed_replacement_owner_and_mechanism':'Docker builder health only for image build; eliminate agent docker-run probe in favor verified build metadata or OpenShell exec.','evidence_or_experiment':'Current POC does not prove this Jackin callsite.' ,'release_acceptance_test':'Reachable gateway with unavailable builder; doctor/status still useful; build reports builder error; version only from digest-verified build/runtime.','source_classification':'active prerequisite or legacy agent execution; split/remove as stated','source_action_reviewed':True,'caller_chain_reviewed':False,'review_complete':False})
# DockerApi implementation action methods have Bollard calls not named docker.*; record every API implementation symbol.
rel='crates/adapters/jackin-docker/src/docker_client.rs'; lines=(ROOT/rel).read_text().splitlines()
for i,text in enumerate(lines,1):
 m=re.search(r'async fn (ping|inspect_container_by_name|inspect_container_by_id|remove_container_by_id|list_containers|create_container|start_container_by_id|remove_volume|create_network|remove_network|list_networks|list_image_tags|remove_image|inspect_image_labels|pull_image|exec_capture_by_id|pause_container_by_id|unpause_container_by_id|inspect_full_container_by_id|inspect_network)\b',text)
 if m:
  name=m.group(1); ledger.append({'file':rel,'line':i,'symbol':name,'method_or_command':'Bollard '+name,'executed_action':f'Concrete BollardDockerClient performs {name} against selected Docker daemon.','production_caller_entry':'Jackin runtime, image builder, cleanup, CLI callers listed in other rows.','current_resource_owner':'Docker daemon selected through Docker host/context environment.','required_user_outcome':f'{name} engine operation required by current product path.','proposed_replacement_owner_and_mechanism':'Move execution methods to OpenShell target interface; retain only builder image methods and explicit optional Docker engine adapter.','evidence_or_experiment':'No Jackin Rust adapter route tested; old Python/CLI POC not equivalent.','release_acceptance_test':f'Exercise {name} against each supported target with identity, error and ownership checks.','source_classification':'active concrete adapter','source_action_reviewed':True,'caller_chain_reviewed':False,'review_complete':False})
for r in ledger:
    if r['file'].endswith('jackin-workflow/src/verify.rs'):
        detail={532:'Force-remove worker after timeout.',575:'Inspect pinned verification image locally.',583:'Pull pinned verification image.',605:'Inspect worker runtime state and exit result.',615:'Force-remove completed worker.',776:'Run verification worker with exact policy argv, mounts and limits.',858:'Drop cleanup force-removes owned worker.'}.get(r['line'],'')
        r['executed_action']=detail
        r['proposed_replacement_owner_and_mechanism']='OpenShell target owns worker sandbox lifecycle; Jackin trusted verifier retains exact policy, output and result binding.'
        r['required_user_outcome']='Workflow checks run isolated with exact command and trustworthy result.'
    if r['file'].endswith('image/version.rs') and r['line']==52:
        r.update(method_or_command='CommandRunner.capture docker run --rm --entrypoint <agent> <image> --version',executed_action='Executes selected agent binary in a temporary Docker container to probe version.',production_caller_entry='build.rs record_built_agent_version calls extract_agent_version when prefetched version metadata absent.',current_resource_owner='Docker image builder.',required_user_outcome='Record installed agent version for status/compatibility display.',proposed_replacement_owner_and_mechanism='Build metadata first; OpenShell sandbox exec only when metadata absent. Remove direct docker run.',evidence_or_experiment='Prior POC separately ran agent version in OpenShell; this Docker fallback not tested in that experiment.',release_acceptance_test='No-prefetch install, version matched against actual OpenShell-executed image digest.')
# Test/docs/build-only excluded raw hits are retained with exact lines.
# Deduplicate matches where the explicit source trace supplements the generic scan.
_unique={}
for r in ledger: _unique[(r['file'],r['line'],r['symbol'],r['method_or_command'])]=r
ledger=list(_unique.values())
# Call sites whose commands span multiple lines and are absent from the narrow
# token scanner. These are executed actions, not path-level summaries.
manual_sites=[
 ('crates/apps/jackin/src/console/services/instances.rs',110,'running_role_containers','ExecRequest::new("docker", ["ps", ...])','Run docker ps filtered to Jackin role label; reconcile live role names into console instance refresh.','Jackin console process runner and selected Docker daemon.','OpenShell inventory for target-scoped sandboxes; retain cached console reconciliation and unavailable-target distinction.','Console refresh: two targets, stale observations and one unavailable target.','Current product source only; not executed in this audit.'),
 ('crates/apps/jackin/src/console/services/instances.rs',284,'resolve_snapshot_container','ExecRequest::new("docker", ["inspect", ...])','Run docker inspect to resolve immutable container ID and name for snapshot.','Jackin console process runner and selected Docker daemon.','Resolve target + immutable sandbox ID from OpenShell inventory; do not use name-only action identity.','Snapshot same-name replacement and target outage preserve correct identity.','Current product source only; not executed in this audit.'),
 ('crates/services/jackin-runtime-apple-container-running/src/running.rs',18,'inspect_container_with','AppleContainerApi::inspect_container','Inspect a saved Apple Container ID and verify returned immutable ID matches request.','Apple Container CLI runtime; Jackin Apple adapter owns saved identity.','Remove Apple backend; OpenShell target inventory/get with immutable sandbox identity.','Mac target status/reconnect identity and same-name replacement checks.','Current product source only; Apple tests mock client.'),
]
for f,line,symbol,method,action,owner,outcome,accept,evidence in manual_sites:
 ledger.append({'file':f,'line':line,'symbol':symbol,'method_or_command':method,'executed_action':action,'production_caller_entry':'See exact caller traced in SOURCE_INVENTORY.md; direct command is production-reachable.','current_resource_owner':owner,'required_user_outcome':outcome,'proposed_replacement_owner_and_mechanism':outcome,'evidence_or_experiment':evidence,'release_acceptance_test':accept,'source_classification':'active production callsite; source only','source_action_reviewed':True,'caller_chain_reviewed':False,'review_complete':False})
# Runtime connection and optional-Docker environment paths found by the broad
# source-token scan. These supplements received a second independent source
# action and caller-edge review; this remains static source evidence only.
supplemental_sites=[
 ('crates/adapters/jackin-docker/src/docker_client.rs',251,'connect_to_cli_docker_context','Docker::connect_with_defaults','When endpoint selection resolves to Defaults, establish Bollard connection using Docker library defaults.','Docker daemon selected by Docker client environment/configuration.','Docker/Buildx builder connection or explicit optional-engine connection only.','Honor daemon endpoint for explicit builder/capability operation; ordinary target management must not connect to Docker.','Docker::connect_with_defaults is active source at line 251; no new route execution here.','Set/unset DOCKER_HOST and context; confirm expected daemon, authentication and separate gateway health.'),
 ('crates/adapters/jackin-docker/src/docker_client.rs',253,'connect_to_cli_docker_context','Docker::connect_with_host','When a supported context endpoint resolves to Host, establish Bollard connection to that configured host.','Selected Docker context endpoint.','Docker/Buildx builder connection or explicit optional-engine connection only.','Preserve only required builder/explicit-engine context support; OpenShell targets have independent authenticated gateways.','Docker::connect_with_host is active source at line 253; no Jackin OpenShell route proved.','Unix and plain TCP contexts connect; unsupported SSH/TLS/context failures are clear and do not disable target management.'),
 ('crates/adapters/jackin-docker/src/docker_client.rs',275,'docker_host_env_is_set','std::env::var_os("DOCKER_HOST")','Read DOCKER_HOST to select environment override versus active Docker CLI context lookup.','Jackin process environment and Docker client endpoint selector.','Retain for builder and explicit optional Docker capability only; keep runtime-target auth separate.','Management commands no longer require Docker env; role sandbox does not inherit host Docker connection credentials.','Static behavior only; source reads DOCKER_HOST and branches to default/context endpoint.','DOCKER_HOST precedence, empty/unset behavior, local context, remote context and OpenShell management without DOCKER_HOST.'),
 ('crates/adapters/jackin-docker/src/docker_client.rs',293,'active_docker_context_endpoint','docker context inspect via exec_sync','Construct and execute Docker CLI context inspect to obtain the selected endpoint when DOCKER_HOST is unset; request construction is at :293-296 and exec_sync runs it at :303.','Local Docker CLI process and configured Docker context; process telemetry captures command result.','Retain only for Docker/Buildx builder or explicit optional-engine endpoint selection; no old Docker execution backend.','Separate this context lookup from OpenShell gateway target resolution and report context errors as builder/capability errors.','Static source evidence; no live context lookup tested in this audit.','Default, explicit context, malformed context, unsupported SSH/TLS, CLI unavailable, and gateway reachable while builder unavailable.'),
 ('crates/adapters/jackin-docker/src/docker_client.rs',297,'active_docker_context_endpoint','std::env::var("DOCKER_CONTEXT")','Read nonempty DOCKER_CONTEXT and append the context name to docker context inspect request.','Jackin process environment and local Docker CLI context selector.','Retain only for builder and explicit optional Docker engine connection.','Do not reuse Docker context as OpenShell target identity; keep independent target credentials/inventory.','Static source only; env read and request mutation verified in pinned source.','Explicit context takes effect; unset/empty selects active Docker context; OpenShell targets remain independent.'),
 ('crates/services/jackin-runtime/src/runtime/launch/launch_runtime/environment.rs',82,'fixed_arguments','DOCKER_HOST=tcp://<dind>:2376','Construct the DinD endpoint string unconditionally; add it to role environment only in the `dind_enabled` branch at :116-129.','Jackin role launch environment and per-instance DinD sidecar endpoint.','Explicit optional Docker capability owner only; absent from normal sandbox.','Publish daemon address only after an OpenShell-compatible managed engine model is proven; default capability stays disabled.','Static source only; managed engine remains unproved.','Disabled sandbox has no endpoint; enabled model resolves daemon inside intended boundary and supports Compose/Testcontainers paths.'),
 ('crates/services/jackin-runtime/src/runtime/launch/launch_runtime/environment.rs',84,'fixed_arguments','DOCKER_CERT_PATH=<client cert directory>','Construct client certificate path; append it to role env only in the `dind_enabled` branch at :116-129.','Per-instance DinD certificate volume and role workload env.','Explicit optional engine owner delivers scoped client material; no credential path in normal sandbox.','Replace host/container volume path with proven per-instance managed secret/certificate publication and cleanup.','Static source only; no managed certificate handoff proved.','Enabled certificate reaches only authorized sandbox; denial/default and cross-instance credential isolation.'),
 ('crates/services/jackin-runtime/src/runtime/launch/launch_runtime/environment.rs',123,'fixed_arguments','DOCKER_TLS_VERIFY=1','Append TLS verification to role env only in the `dind_enabled` branch at :116-129.','Role workload environment and DinD certificate trust bundle.','Explicit optional Docker capability; keep TLS verification enabled.','Preserve verified TLS for chosen managed engine route; no insecure endpoint fallback.','Static source only; no managed engine transport test.','Valid cert succeeds; wrong/missing cert fails; normal sandbox has no Docker client capability.'),
 ('crates/adapters/jackin-image/src/image_build.rs',52,'docker_build_env','DOCKER_BUILDKIT=1','Set DOCKER_BUILDKIT=1 in Docker/Buildx image-build environment.','Docker image builder process.','Retain Docker/Buildx as image builder; this environment is builder-scoped and does not enable workload Docker access.','Keep builder env confined to image-build process; do not forward it into OpenShell sandboxes.','Static source; image build POC does not prove Architect recipe behavior.','Actual role image builds use BuildKit, and a normal role sandbox has no Docker endpoint or builder variables.'),
 ('crates/services/jackin-runtime-launch-dind/src/launch_dind.rs',192,'run_dind_sidecar_headless_with_owner','DOCKER_TLS_SAN=DNS:<dind-name>','Set Docker daemon TLS SAN to the per-instance DinD hostname.','Optional DinD sidecar certificate generation and network identity.','Only the explicitly enabled engine owner creates this identity and certificate material.','Replace old DIND hostname/certificate assumptions with chosen managed-engine service identity; isolate each instance.','Static source only; managed engine certificate generation was not proved.','Two enabled instances have noninterchangeable service certs and cannot access each other.'),
 ('crates/services/jackin-runtime-launch-dind/src/launch_dind.rs',197,'run_dind_sidecar_headless_with_owner','DOCKER_TLS_CERTDIR=/certs','Set daemon certificate-generation directory and include the per-instance SAN env in Docker sidecar spec.','Optional DinD sidecar filesystem/certificate volume.','Explicit engine owner controls sidecar and certificate volume lifecycle.','Keep cert data out of normal sandboxes and attach only via authorized per-instance publication.','Static source only; no managed certificate storage proof.','Provision, interrupted setup, stop/restart, teardown and wrong-domain certificate denial.'),
]
for f,line,symbol,method,action,owner,mechanism,change,evidence,accept in supplemental_sites:
 ledger.append({'file':f,'line':line,'symbol':symbol,'method_or_command':method,'executed_action':action,'production_caller_entry':'Source route requires independent review; caller details recorded in `supplemental_source_actions`.','current_resource_owner':owner,'required_user_outcome':mechanism,'proposed_replacement_owner_and_mechanism':change,'required_code_change':change,'evidence_or_experiment':evidence,'release_acceptance_test':accept,'source_classification':'active runtime connection/configuration source; independent review pending','source_action_reviewed':False,'caller_chain_reviewed':False,'source_review_complete':False,'review_complete':False,'replacement_execution_proved':False,'supplemental_source_action':True})
# Reconcile every broad production match: direct call, declaration, import,
# diagnostic text, or unresolved. Preserve residuals instead of silently drop.
ledger_keys={(r['file'],r['line']) for r in ledger}
for r in raw:
    src=r['match']; key=(r['file'],r['line'])
    if key in ledger_keys:
        r.update(disposition='direct operation; see matching direct_callsite_ledger row',review_complete=True)
    elif r['file'].endswith('apps/jackin-capsule/src/client_dispatch.rs') and r['line']==49:
        r.update(disposition='Help synopsis only; its sudo-provision runtime invocation is tracked at jackin-runtime/src/runtime/launch/launch_runtime/session.rs and docker_profile/exec.rs.',review_complete=True)
    elif re.match(r'\s*(use|pub use)\b',src):
        r.update(disposition='Import/type dependency only; executed action occurs in implementation/caller rows.',review_complete=True)
    elif re.match(r'\s*(///|//|/\*|\*)',src):
        r.update(disposition='Comment or documentation; excluded from executed actions.',review_complete=True)
    elif 'DockerApi' in src and (':' in src or 'fn ' in src or 'impl ' in src or 'dyn ' in src or '&impl ' in src):
        r.update(disposition='Interface/type declaration or parameter; maps to concrete adapter operations and production caller ledger.',review_complete=True)
    elif 'BollardDockerClient' in src or 'DockerApi' in src or 'ContainerSpec' in src or 'ContainerHandle' in src:
        r.update(disposition='Type/interface/connection dependency only at this line; concrete operation and caller are linked in direct_callsite_ledger.',review_complete=True)
    elif 'bollard::' in src or 'InspectNetworkOptions' in src:
        r.update(disposition='Bollard error/API type handling in the concrete adapter; not an independent resource action.',review_complete=True)
    elif re.search(r'"[^"]*(docker|container)[^"]*"',src,re.I):
        r.update(disposition='Diagnostic/error/help string only; not a runtime invocation.',review_complete=True)
    else:
        r.update(disposition='UNRESOLVED raw production match; needs direct review.',review_complete=False)
# Build a conservative production function-reference graph in linear passes.
# An edge is a candidate when Rust name resolution is ambiguous.
files={}; defs=collections.defaultdict(list); owner={}
fnrx=re.compile(r'\b(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?fn\s+([A-Za-z0-9_]+)')
for src in ROOT.glob('crates/**/*.rs'):
    rel=src.relative_to(ROOT)
    if skip(rel): continue
    ls=src.read_text(errors='replace').splitlines(); files[str(rel)]=ls; cur='(module scope)'
    for no,tx in enumerate(ls,1):
        fm=fnrx.search(tx)
        if fm:
            cur=fm.group(1); key=f'{rel}::{cur}'
            if key not in defs[cur]: defs[cur].append(key)
            owner[(str(rel),no)]=key
        else: owner[(str(rel),no)]=f'{rel}::{cur}'
callers=collections.defaultdict(set)
callrx=re.compile(r'\b([A-Za-z_][A-Za-z0-9_]*)\s*\(')
for rel,ls in files.items():
    for no,tx in enumerate(ls,1):
        cur=owner[(rel,no)]
        if fnrx.search(tx): continue
        for m in callrx.finditer(tx):
            name=m.group(1)
            for callee in defs.get(name,[]):
                # Same-file edges preferred; cross-file refs retained as candidates.
                if callee.rsplit('::',1)[0]==rel or len(defs[name])==1:
                    callers[callee].add(cur)
roots={'crates/apps/jackin/src/app.rs::run':'CLI command dispatch',
       'crates/apps/jackin/src/cli/dispatch.rs::dispatch':'console dispatch',
       'crates/apps/jackin/src/app/load_cmd.rs::handle_load':'jackin load',
       'crates/apps/jackin/src/app/load_cmd.rs::handle_hardline':'jackin hardline',
       'crates/apps/jackin/src/app/load_cmd.rs::handle_eject':'jackin eject',
       'crates/apps/jackin/src/app/load_cmd.rs::handle_exile':'jackin exile',
       'crates/apps/jackin/src/app/prune_cmd.rs::handle_purge':'jackin purge',
       'crates/apps/jackin/src/app/prune_cmd.rs::handle_prune':'jackin prune',
       'crates/apps/jackin/src/cli/status.rs::run':'jackin status',
       'crates/apps/jackin/src/cli/usage.rs::run':'jackin usage',
       'crates/apps/jackin/src/cli/prewarm.rs::run':'jackin prewarm',
       'crates/apps/jackin/src/app/workflow_cmd.rs::handle':'jackin workflow record test'}
def find_roots(start):
    results=[]; q=[(start,[start])]; visited=set()
    while q and len(results)<5:
        node,path=q.pop(0)
        if node in visited: continue
        visited.add(node)
        if node in roots:
            results.append({'chain':[x.rsplit('::',1)[-1] for x in path[::-1]],'entry':roots[node]});continue
        for pnode in sorted(callers.get(node,())):
            if len(defs.get(pnode.rsplit('::',1)[-1],()))>1 and pnode not in roots: continue
            q.append((pnode,path+[pnode]))
    return results
for r in ledger:
    node=f"{r['file']}::{r['symbol']}"
    traces=find_roots(node)
    r['caller_trace_candidates']=traces
    r['caller_trace_candidate_found']=bool(traces)
    r['caller_chain_reviewed']=False
    r['review_complete']=False
    if traces:
        r['production_caller_entry']='; '.join(t['entry']+' via '+' > '.join(t['chain']) for t in traces)
    if r['file'].endswith('jackin-workflow/src/verify.rs'):
        chain={'entry':'jackin workflow record test','chain':['app::run','workflow_cmd::handle','run_record_test','host_daemon WorkflowRecordTest','WorkflowBackend::record_test','WorkflowService::record_test','run_test_command']}
        if r['symbol']=='drop': chain['chain'].append('TestWorkerGuard::drop')
        r['caller_trace_candidates']=[chain];r['caller_trace_candidate_found']=True;r['caller_chain_reviewed']=False;r['review_complete']=False
        r['production_caller_entry']='jackin workflow record test via '+' > '.join(chain['chain'])
    else:
        r['caller_trace_status']='No resolved name-based path to CLI root; source reference/call graph needs manual tracing.'
# Action-level corrections from independent source review.
for r in ledger:
    if r['file'].endswith('capsule_ready.rs') and r['line'] in (131,145):
        r.update(executed_action='Run docker info inside the optional DinD sidecar to test daemon readiness.' if r['line']==131 else 'Test that the optional DinD certificate volume contains the client CA file.',
                 current_resource_owner='Jackin optional-Docker sidecar manager; DinD child daemon and certificate volume.',
                 required_user_outcome='When explicitly enabled, provide a ready optional Docker engine and usable client certificates.',
                 proposed_replacement_owner_and_mechanism='Do not retain this Capsule/Docker-exec readiness path. Prove an OpenShell-compatible optional-engine owner; default remains disabled.',
                 release_acceptance_test='Enabled/disabled Docker capability; daemon readiness, certificate handoff, isolation and cleanup.')
    if r['file'].endswith('jackin-runtime-apple-container-running/src/running.rs') and r['line']==18:
        r['production_caller_entry']='Apple backend load/reconnect/finalization via runtime/apple_container.rs::ensure_running_with -> inspect_container_with; Apple attach-outcome inspection via attach_outcome.rs::inspect_container_with.'
    if r['file'].endswith('docker.rs') and r['line'] in (311,321):
        r['production_caller_entry']='jackin load / hardline role creation via launch_runtime::docker::start; see launch pipeline and runtime dispatch.'
    if r['file'].endswith('preflight.rs') and r['line'] in (190,209,210):
        r['production_caller_entry']='jackin load, hardline, eject, exile, purge, prune and doctor preflight dispatch.'
    # Explicitly reviewed caller and activity corrections. These are narrow
    # source traces validated by the independent source reviewer, not blanket
    # completion of the generated call graph.
    if r['file'].endswith('image/version.rs') and r['line']==52:
        r.update(production_caller_entry='jackin prewarm -> cli/prewarm.rs:198,511 -> image/prewarm.rs:72 -> prewarm_agent_image -> prewarm_run.rs:43 -> validated.rs:88 or 119 -> build.rs:453 -> record_built_agent_version -> version.rs:132 -> extract_agent_version -> version.rs:52. The load path also reaches build.rs but is not included in this reviewed chain.',caller_chain_reviewed=True,review_complete=True)
    if r['file'].endswith('jackin-workflow/src/verify.rs'):
        action={532:'timeout cleanup rm -f',575:'worker image availability inspect',583:'pinned worker image pull',605:'worker exit-state inspect',615:'post-run rm -f',776:'worker docker run',858:'Drop guard rm -f'}[r['line']]
        r.update(production_caller_entry=f'jackin workflow record test -> workflow_cmd.rs:283/401/447 -> host_daemon.rs:1620/1641 -> WorkflowService::record_test -> run_test_command::{action}; substeps use ensure_sandbox_image / finish_test_execution where applicable.',caller_chain_reviewed=True,review_complete=True)
    if r['file'].endswith('jackin-runtime-cleanup-prune-images/src/prune_images.rs'):
        r.update(production_caller_entry='jackin prune -> app/prune_cmd.rs:66 or :100 -> runtime::prune_images; inspects role-container image consumers, then removes only unreferenced Jackin images.',caller_chain_reviewed=True,review_complete=True)
    if r['file'].endswith('launch_dind.rs') and r['symbol']=='prewarmed_dind_state_is_live':
        r.update(production_caller_entry='jackin load/hardline launch adoption and prewarm_trigger.rs:153 background_sidecar_prewarm_once -> prewarmed_dind_state_is_live.',caller_chain_reviewed=True)
    if r['file'].endswith('image/prewarm_run.rs') and r['symbol']=='reuse_staleness_sentinel':
        r.update(production_caller_entry='jackin load launch orchestration -> runtime::reuse_sentinel -> session.rs:160 -> staleness.rs:53 closure -> reuse_staleness_sentinel.',caller_chain_reviewed=True)
    if r['file'].endswith('image/sibling.rs') and r['symbol']=='prewarm_sibling_image':
        r.update(production_caller_entry='jackin launch -> prewarm_spawn.rs:277 sibling prewarm worker -> prewarm_sibling_image.',caller_chain_reviewed=True)
    if r['file'].endswith('docker.rs') and r['symbol']=='start':
        r.update(production_caller_entry='jackin load/hardline -> runtime/launch/launch_runtime.rs:173 docker::start; role create/start operation.',caller_chain_reviewed=True)
    if r['file'].endswith('preflight.rs') and r['symbol'] in ('check_docker_daemon','report_docker_version','check_orphaned_containers'):
        r.update(production_caller_entry='preflight::run_check match at :122/:123/:132, dispatched from load/hardline/eject/exile/purge/prune and doctor.',caller_chain_reviewed=True)
    if r['file'].endswith('capture.rs') and r['symbol'] in ('capture_checkpoint','confirm_paused'):
        r.update(source_classification='implemented checkpoint foundation; no production caller found',production_caller_entry='No production caller found by repository-wide symbol search; capture tests only.',caller_trace_candidate_found=False,caller_trace_candidates=[],caller_trace_status='No production caller found; tests call the capture foundation.',review_complete=True,caller_chain_reviewed=True)
    if r['file'].endswith('docker_client.rs') and r['symbol'] in ('inspect_full_container_by_id','pause_container_by_id','unpause_container_by_id'):
        r.update(source_classification='implemented adapter method; no production caller found',production_caller_entry='No production caller found; trait/adapter definitions and inactive checkpoint foundation only.',review_complete=True,caller_chain_reviewed=True)
    if r['file'].endswith('exit_diagnosis.rs') and r['symbol'] in ('diagnose_premature_exit','inspect_attach_outcome'):
        r.update(source_classification='test-only diagnostic helper; no production caller',production_caller_entry='Production path uses *_by_id alternatives; these helpers are test-only re-exports and test callers.',review_complete=True,caller_chain_reviewed=True)
    if r['file'].endswith('discovery.rs') and r['symbol']=='list_running_agent_display_names':
        r.update(source_classification='implemented discovery helper; no production caller found',production_caller_entry='Definition/re-export and tests only; console uses running_role_containers instead.',review_complete=True,caller_chain_reviewed=True)
# Trait dispatch hides adapter-to-caller edges. Link each concrete Bollard
# implementation to all direct DockerApi callsites of the same method.
for r in ledger:
    if r['file']=='crates/adapters/jackin-docker/src/docker_client.rs':
        method=r['symbol']
        callers_for_method=[]
        for q in ledger:
            if q is r or q['file'].startswith('crates/adapters/jackin-docker/'): continue
            if q.get('method_or_command')==method:
                callers_for_method.append({'file':q['file'],'line':q['line'],'symbol':q['symbol'],'caller_trace_candidates':q.get('caller_trace_candidates',[])})
        r['trait_callsite_references']=callers_for_method
        r['trait_callsite_count']=len(callers_for_method)
        if callers_for_method:
            refs=[]
            for q in callers_for_method:
                es=sorted({t['entry'] for t in q.get('caller_trace_candidates',[])})
                refs.append(f"{q['file']}:{q['line']} {q['symbol']}"+(f" (candidate entries: {', '.join(es)})" if es else " (caller-to-entry path unverified)"))
            r['production_caller_entry']='Trait-dispatched production callsites: '+'; '.join(refs)
            r['caller_trace_status']='Concrete adapter method linked to exact DockerApi trait callsites; listed CLI entries remain static candidates unless independently marked reviewed.'
        else:
            r['production_caller_entry']='No production caller found for this adapter method; definitions/tests only or inactive foundation. Verify source_classification.'
            r['caller_trace_status']='No production trait callsite found in scanned product ledger.'
    elif not r.get('caller_trace_candidate_found'):
        node=f"{r['file']}::{r['symbol']}"
        incoming=sorted(callers.get(node,()))
        if incoming:
            r['production_caller_entry']='Direct static incoming references (candidate, not CLI-root verified): '+'; '.join(incoming)
            r['caller_trace_status']='Direct incoming source references recorded; path to public entry point not independently verified.'
doc={'source_commit':COMMIT,'raw_scan_pattern':RAW.pattern,'raw_candidate_count':len(raw),'raw_production_matches':raw,'raw_unresolved_count':sum(not r.get('review_complete',False) for r in raw),'direct_callsite_count':len(ledger),'direct_callsite_ledger':ledger,'cross_cutting_production_callsite_count':9,'total_production_callsite_records':len(ledger)+9,'excluded_match_count':len(excluded),'excluded_matches':excluded,'notes':['Each ledger row records direct production operations and concrete adapter API methods. Source call chains are candidate references and require manual review when flagged.','Function context uses nearest preceding fn declaration; Rust module resolution is not fully parsed.','Shell, scripts, packaging and CI results are summarized in SOURCE_INVENTORY.md; inspect those separate file inventories for build-only/runtime classification.']}
# Cross-cutting non-Docker execution assumptions requested by the source audit.
# These are explicit production sites, not scanner keyword hits.
doc['cross_cutting_production_callsites']=[
 {'file':'crates/apps/jackin-capsule/src/main.rs','line':35,'symbol':'main','executed_action':'Choose Capsule daemon mode from PID 1 or JACKIN_CAPSULE_FORCE_DAEMON; production launch expects supervisor process model.','production_caller_entry':'Role image entrypoint starts jackin-capsule; Jackin load and reconnect create role workload.','current_resource_owner':'Role runtime process supervisor; Docker currently starts root 0:0, Capsule PID1 owns children/reaping.','proposed_replacement_owner_and_mechanism':'Prove supported OpenShell entrypoint/supervisor process; preserve Capsule daemon as selected Candidate A only if non-root and non-PID1 settings work, else separate trusted control Candidate B.','evidence_or_experiment':'Candidate A root-mode experiment FAIL (`results/full-refactor-20261024/capsule/a-root-policy.json`); Candidate B NOT TESTED.','release_acceptance_test':'Launch Capsule with actual role image under selected OpenShell identity, create/reconnect sessions, kill supervisor and prove child exits/reaping.' ,'source_classification':'active source; OpenShell compatibility unresolved','caller_chain_reviewed':False,'review_complete':False},
 {'file':'crates/services/jackin-runtime-apple-container-supervisor-env/src/supervisor_env.rs','line':6,'symbol':'supervisor_env','executed_action':'Inject JACKIN_CAPSULE_FORCE_DAEMON=1 for supported non-PID1 Apple process launch.','production_caller_entry':'Apple backend constructs environment for role launch.','current_resource_owner':'Jackin Apple adapter and Capsule process startup.','proposed_replacement_owner_and_mechanism':'Remove Apple-specific path; OpenShell sandbox process config must set explicit main command/env and readiness checks.','evidence_or_experiment':'Apple runtime not executed; OpenShell explicit hook command was tested in primitive fixture only.','release_acceptance_test':'OpenShell starts role hook, Capsule daemon and agent under target-specific process model.','source_classification':'active Apple startup configuration; replacement untested','caller_chain_reviewed':False,'review_complete':False},
 {'file':'crates/apps/jackin-capsule/src/process_isolation/linux.rs','line':38,'symbol':'run','executed_action':'Require root wrapper, build session-specific filesystem policy, drop to non-root UID/GID, retain one capability and install Landlock before exec.','production_caller_entry':'Capsule `new shell/agent` creates `__isolated-exec` subprocess; launched within a role session.','current_resource_owner':'Capsule trusted root supervisor and per-session Unix identity.','proposed_replacement_owner_and_mechanism':'Translate to OpenShell enforced per-session policy or retain in trusted supervisor with proven UID/capability availability; never silently weaken filesystem policy.','evidence_or_experiment':'Root Candidate A policy blocked; Linux process isolation enforcement not executed in OpenShell.','release_acceptance_test':'Allowed/denied filesystem paths, UID/GID, supplementary groups, capabilities and network under selected target.' ,'source_classification':'active source; mechanism unproved','caller_chain_reviewed':False,'review_complete':False},
 {'file':'crates/apps/jackin-capsule/src/process_isolation/linux/enforce.rs','line':143,'symbol':'drop_privileges','executed_action':'Clear supplementary groups and setresgid/setresuid to non-root session identity; install limited DAC capability set.','production_caller_entry':'process_isolation::linux::run called by Capsule main `__isolated-exec`.','current_resource_owner':'Capsule process security boundary inside role workload.','proposed_replacement_owner_and_mechanism':'Use proved OpenShell per-process policy/identity; remove syscalls only if equivalent effective control is tested.','evidence_or_experiment':'No OpenShell equivalent proof.','release_acceptance_test':'Cross-session private files denied; approved workspace paths retain required access and executable semantics.' ,'source_classification':'active source; replacement untested','caller_chain_reviewed':False,'review_complete':False},
 {'file':'crates/apps/jackin-capsule/src/attach_protocol/handshake.rs','line':21,'symbol':'perform_handshake','executed_action':'Read Unix peer UID and perform timed Capsule protocol handshake before accepting attach/control stream.','production_caller_entry':'Capsule daemon accepts local socket client; host attach currently direct socket or Docker exec attach-proxy.','current_resource_owner':'Capsule Unix socket and client process identity.','proposed_replacement_owner_and_mechanism':'Replace socket transport only with authenticated OpenShell stream mapping; preserve Capsule protocol handshake and control ownership.','evidence_or_experiment':'No Rust OpenShell Capsule stream evidence; generic CLI TTY evidence is not equivalent.','release_acceptance_test':'Cross-domain control denial; exact frame replay, timeout, reconnect, binary bytes, focus/input ownership.' ,'source_classification':'active source; OpenShell transport untested','caller_chain_reviewed':False,'review_complete':False},
 {'file':'crates/apps/jackin-capsule/src/usage_relay_proxy/identity.rs','line':104,'symbol':'peer_identity','executed_action':'Derive relay caller UID/GID/PID and Linux process start time from Unix peer credentials.','production_caller_entry':'Capsule `usage-relay-proxy` command called through controlled runtime usage relay.','current_resource_owner':'Capsule peer identity verifier; host broker owns account capability.','proposed_replacement_owner_and_mechanism':'Replace peer credential identity with authenticated target+sandbox+session+domain identity; retain existing authorization policy.','evidence_or_experiment':'No OpenShell authenticated usage relay proof.','release_acceptance_test':'Two account domains and shell domain; wrong/stale identity cannot read or refresh usage.' ,'source_classification':'active source; replacement untested','caller_chain_reviewed':False,'review_complete':False},
 {'file':'crates/apps/jackin-capsule/src/usage_relay_proxy/authorization.rs','line':49,'symbol':'authorizes','executed_action':'Authorize capability-scoped current/refresh/join by peer UID/GID, or exact supervisor PID/start-time identity.','production_caller_entry':'Capsule usage relay request dispatch.','current_resource_owner':'Capsule authorization map loaded from authenticated role config; usage broker owns account data.','proposed_replacement_owner_and_mechanism':'Keep domain authorization in trusted Jackin; enforce on authenticated OpenShell session identity and broker endpoint, not helper UID alone.','evidence_or_experiment':'No real authenticated cross-domain usage denial run.','release_acceptance_test':'Cross-domain usage, stale sandbox generation, refresh and join denial through live channel.' ,'source_classification':'active source; replacement untested','caller_chain_reviewed':False,'review_complete':False},
 {'file':'crates/apps/jackin-capsule/src/session/spawn.rs','line':71,'symbol':'spawn_child_with_registration','executed_action':'Register child PID with process-lifetime reaper and reserve child ownership; fallback handles missing PID.','production_caller_entry':'Capsule session process spawn from daemon control events.','current_resource_owner':'Capsule PID1/reaper and jackin_process child registry.','proposed_replacement_owner_and_mechanism':'Select exactly one wait-status owner under OpenShell; retain session state, prove signals/grandchildren and Darwin only on macOS process hosts.','evidence_or_experiment':'No candidate combined session/grandchild/zombie test in OpenShell.','release_acceptance_test':'Clean exit, signal, supervisor/gateway failure, grandchildren, zombie accumulation and reconnect.' ,'source_classification':'active source; process lifetime replacement untested','caller_chain_reviewed':False,'review_complete':False},
 {'file':'crates/apps/jackin-capsule/src/pid1.rs','line':884,'symbol':'install_sigchld_reaper','executed_action':'Start process-lifetime SIGCHLD child reaper on Darwin Capsule host process.','production_caller_entry':'Capsule main enters daemon mode on macOS then prepares/activates Darwin reaper.','current_resource_owner':'Capsule host process on Darwin; only relevant when Capsule actually runs on macOS.','proposed_replacement_owner_and_mechanism':'OpenShell target process supervisor owns remote workload; Jackin host must not claim Darwin reaping for remote Linux/VM workload.','evidence_or_experiment':'No OpenShell Capsule process-lifetime experiment.','release_acceptance_test':'Run Darwin-specific reaping only on actual Mac process target; test Linux/VM separately.' ,'source_classification':'active Darwin-only source; replacement untested','caller_chain_reviewed':False,'review_complete':False}
]
# Jackin's own build/test tool is executable production code, but these
# operations are confined to the development/release pipeline, not user runs.
doc['build_test_infrastructure_callsites']=[
 {'file':'docker/construct/Dockerfile','line':129,'symbol':'RUN (construct image dependency layer)','executed_action':'Install Docker CE CLI, Buildx and Compose plugins in the developer/CI construct image; does not start a daemon or execute a workload in Jackin runtime.','caller':'Construct Dockerfile image build.','owner':'Construct image builder layer; later CI/developer commands own daemon use.','classification':'active image-build tooling dependency.','decision':'Retain because Docker/Buildx remains the required image builder and Docker Compose is used by build/test lanes. Keep separate from OpenShell execution.','release_test':'Fresh construct image has pinned/recorded CLI tools; user runtime management works with builder independently unavailable.'},
 {'file':'crates/tools/jackin-xtask/src/ci.rs','line':285,'symbol':'build_e2e_step','executed_action':'CI step runs docker info as an E2E prerequisite before cargo e2e.','caller':'xtask CI command builds and executes the e2e step.','owner':'CI host Docker daemon.','classification':'active build/test infrastructure; excluded from product runtime backend.','decision':'Retain only if the CI lane still exercises Docker-capability or build behavior; replace/retarget for OpenShell-specific integration lanes.','release_test':'CI can separately test builder availability and OpenShell target availability; failure reports identify which dependency failed.'},
 {'file':'crates/tools/jackin-xtask/src/ci.rs','line':321,'symbol':'build_e2e_step','executed_action':'Read VELNOR_DOCKER_HOST_TEMP and forward its value as TMPDIR to the E2E process; does not connect to a daemon at this line.','caller':'xtask CI E2E step construction.','owner':'CI process environment.','classification':'active CI environment forwarding; not a runtime Docker API operation.','decision':'Retain only if CI still uses this compatibility variable; rename only as a separately reviewed CI cleanup.','release_test':'Configured temp path reaches E2E subprocess; unset variable leaves inherited TMPDIR.'},
 {'file':'crates/tools/jackin-xtask/src/consumer_ci_gate/lanes.rs','line':14,'symbol':'docker_preflight','executed_action':'Run docker info --format OperatingSystem and require a non-empty daemon identity; optionally require OrbStack.','caller':'Consumer CI profile gate invokes docker_preflight before profile matrix lanes.','owner':'CI host Docker daemon.','classification':'active build/test infrastructure; not user runtime.','decision':'Keep only in Docker-specific builder/capability CI lane; OpenShell lane must validate gateway separately.','release_test':'Distinct CI lanes prove builder, gateway and optional Docker health independently.'},
 {'file':'crates/tools/jackin-xtask/src/profile_matrix.rs','line':122,'symbol':'run_profile_matrix','executed_action':'Run docker run posture probe for selected Docker profile.','caller':'xtask profile-matrix CI command.','owner':'CI host Docker daemon and disposable probe container.','classification':'active integration test infrastructure.','decision':'Retain only as Docker capability profile regression test; add OpenShell policy enforcement tests independently.','release_test':'Profile allow/deny operations enforced under actual selected runtime.'},
 {'file':'crates/tools/jackin-xtask/src/profile_matrix.rs','line':141,'symbol':'run_profile_matrix','executed_action':'Execute command inside Docker posture probe container.','caller':'xtask profile-matrix CI command.','owner':'CI host Docker daemon and disposable probe container.','classification':'active integration test infrastructure.','decision':'Same as profile posture probe; not a production backend path.','release_test':'Effective enforcement, not configuration-only assertion.'},
 {'file':'crates/tools/jackin-xtask/src/profile_matrix.rs','line':150,'symbol':'run_profile_matrix','executed_action':'Execute second command inside Docker posture probe container.','caller':'xtask profile-matrix CI command.','owner':'CI host Docker daemon and disposable probe container.','classification':'active integration test infrastructure.','decision':'Same as profile posture probe; not a production backend path.','release_test':'Positive and negative controls run on OpenShell target.'},
 {'file':'crates/tools/jackin-xtask/src/profile_matrix.rs','line':154,'symbol':'run_profile_matrix','executed_action':'Inspect process state inside disposable Docker profile probe.','caller':'xtask profile-matrix CI command.','owner':'CI host Docker daemon and disposable probe container.','classification':'active integration test infrastructure.','decision':'Keep only as Docker profile test; add equivalent selected-target test.','release_test':'Required process and privilege boundaries enforced.'},
 {'file':'crates/tools/jackin-xtask/src/profile_matrix.rs','line':169,'symbol':'run_profile_matrix','executed_action':'Run docker info to validate daemon for profile test lane.','caller':'xtask profile-matrix CI command.','owner':'CI host Docker daemon.','classification':'active integration test infrastructure.','decision':'Keep only in Docker-specific lane; separate builder/gateway health.','release_test':'Unavailable builder does not misreport target health.'},
 {'file':'crates/tools/jackin-xtask/src/profile_matrix.rs','line':205,'symbol':'ProfileProbeGuard::drop','executed_action':'Remove disposable profile-probe container during guard cleanup.','caller':'Profile matrix probe guard drop.','owner':'CI host Docker daemon; probe receipt owned by test harness.','classification':'active integration test cleanup.','decision':'Keep for Docker test lane; OpenShell tests use owned sandbox receipts and confirmed deletion.','release_test':'Cleanup on success, failure, timeout and interrupted test.'},
 {'file':'crates/tools/jackin-xtask/src/construct.rs','line':148,'symbol':'prepare_builder','executed_action':'Inspect/create/bootstrap Buildx builder used for construct image builds.','caller':'xtask construct init/reset/build/publish commands.','owner':'Docker/Buildx developer or CI builder.','classification':'active build infrastructure; retain.','decision':'Retain Docker/Buildx as required Jackin image builder, separate from OpenShell runtime.','release_test':'Builder unavailable fails image build accurately without making target management unavailable.'},
 {'file':'crates/tools/jackin-xtask/src/construct.rs','line':172,'symbol':'doctor','executed_action':'Inspect Buildx builder state and list builders.','caller':'xtask construct doctor command.','owner':'Docker/Buildx builder.','classification':'active builder diagnostics; retain.','decision':'Builder health is independent of OpenShell gateway health.','release_test':'Doctor reports builder and gateway states separately.'},
 {'file':'crates/tools/jackin-xtask/src/construct.rs','line':182,'symbol':'reset_builder','executed_action':'Remove and recreate/bootstrap selected Buildx builder.','caller':'xtask construct reset command.','owner':'Explicitly selected Buildx builder.','classification':'active build infrastructure cleanup; retain as explicit operator action.','decision':'Not runtime cleanup; does not authorize deleting unrelated builder resources.','release_test':'Reset affects only selected owned builder namespace.'},
 {'file':'crates/tools/jackin-xtask/src/construct.rs','line':203,'symbol':'build_local','executed_action':'Build construct image with Buildx bake.','caller':'xtask construct build command.','owner':'Docker/Buildx builder.','classification':'active image build infrastructure; retain.','decision':'Builder operation remains allowed by product requirements.','release_test':'Pinned recipe, digest, cache and architecture coverage.'},
 {'file':'crates/tools/jackin-xtask/src/construct.rs','line':219,'symbol':'build_local','executed_action':'Run Buildx bake for local construct image.','caller':'xtask construct build command.','owner':'Docker/Buildx builder.','classification':'active image build infrastructure; retain.','decision':'Builder operation remains allowed by product requirements.','release_test':'Cold/warm/forced rebuild and digest identity.'},
 {'file':'crates/tools/jackin-xtask/src/construct.rs','line':237,'symbol':'publish','executed_action':'Build and push construct image by digest using Buildx bake.','caller':'xtask construct publish command.','owner':'Docker/Buildx builder and configured registry.','classification':'active image publishing infrastructure; retain.','decision':'This is image delivery infrastructure, not workload execution.','release_test':'Registry auth, digest, interruption and remote pull verification.'},
 {'file':'crates/tools/jackin-xtask/src/construct.rs','line':293,'symbol':'publish','executed_action':'Inspect registry image metadata using docker buildx imagetools.','caller':'xtask construct publish command.','owner':'Configured registry and Buildx CLI.','classification':'active image publishing infrastructure; retain.','decision':'Retain to verify pushed image identity.','release_test':'Registry inspection matches recorded digest and platform manifests.'},
 {'file':'crates/tools/jackin-xtask/src/construct.rs','line':377,'symbol':'inspect_image','executed_action':'Inspect local construct image metadata.','caller':'xtask construct doctor/build/publish path.','owner':'Docker image builder store.','classification':'active builder image diagnostic; retain.','decision':'Builder cache ownership remains distinct from target image ownership.','release_test':'Safe pruning and digest inspection do not remove target-retained images.'},
 {'file':'crates/tools/jackin-xtask/src/construct.rs','line':459,'symbol':'builder_exists','executed_action':'Check whether named Buildx builder exists.','caller':'xtask construct helper.','owner':'Docker/Buildx builder.','classification':'active build infrastructure helper; retain.','decision':'Builder-only operation.','release_test':'Builder discovery and unavailable state reported distinctly.'},
]
# Correct enclosing function/action pairs against pinned source. A file path
# does not determine whether a tool operation builds, inspects or removes.
for row in doc['build_test_infrastructure_callsites']:
    f=row['file']; n=row['line']
    if f.endswith('profile_matrix.rs') and n in (122,141,150,154): row['symbol']='probe_standard_posture'
    if f.endswith('profile_matrix.rs') and n==169: row['symbol']='docker_info_field'
    if f.endswith('profile_matrix.rs') and n==205:
        row.update(symbol='docker_rm',executed_action='Run docker rm -f for the named disposable probe; ContainerGuard calls this helper on drop.',caller='probe_standard_posture creates ContainerGuard; helper also called before run to remove stale same-name probe.',owner='CI Docker daemon; named test fixture only.',decision='Keep only in Docker profile test lane; OpenShell tests use owned sandbox receipts and confirmed deletion.')
    if f.endswith('construct.rs'):
        names={148:'init_buildx',172:'doctor_buildx',182:'reset_buildx',203:'build_local',219:'build_platform',237:'push_platform',293:'version_published',377:'inspect',459:'builder_exists'}
        if n in names: row['symbol']=names[n]
        if n==293:
            row.update(line=311,executed_action='Run docker buildx imagetools inspect for the configured registry reference and parse publication status.',caller='xtask construct publish -> assert_version_unpublished -> version_published -> output_raw.',owner='Configured registry plus Docker Buildx CLI.',decision='Retain for builder image publication safety; this checks registry availability, not OpenShell target image availability.',release_test='Published/unpublished, unauthorized, timeout and registry outage states; target image delivery verified separately.')
        if n==377: row.update(executed_action='Run docker buildx bake --print for construct-local and construct-publish configuration; does not inspect a built image.',classification='active Buildx configuration diagnostic; retain.',decision='Builder configuration output only; do not use it as evidence of image availability or target delivery.',release_test='Verify output config separately from image build/push/digest inspection.')
# Merge independent row-by-row action and caller reviews by exact source
# identity. Caller-chain proof is static source evidence, not runtime evidence.
reviewed={}
verified_routes=[]
review_audits={}
for fn,key_name in [('action-corrections-a.json','records'),('action-corrections-b.json','rows')]:
    rp=HERE/fn
    if not rp.exists(): continue
    audit=json.loads(rp.read_text())
    if audit.get('source_commit')!=COMMIT: raise ValueError(f'{fn} source commit mismatch')
    review_audits[fn]=audit
    if fn=='action-corrections-b.json': verified_routes=audit.get('verified_call_chains',[])
    for corr in audit[key_name]:
        key=corr.get('key',{})
        ident=(key.get('file'),key.get('line'),key.get('symbol'),key.get('method_or_command'))
        if ident in reviewed: raise ValueError(f'duplicate independent correction {ident}')
        reviewed[ident]=(fn,corr)
seen_reviewed=set()
for r in ledger:
    ident=(r['file'],r['line'],r['symbol'],r.get('method_or_command'))
    if ident not in reviewed: continue
    fn,corr=reviewed[ident]; seen_reviewed.add(ident)
    if fn=='action-corrections-a.json':
        fields={'executed_action':'executed_action','current_resource_owner':'current_resource_owner','required_user_outcome':'required_user_outcome','proposed_replacement_owner_and_mechanism':'proposed_replacement_owner_and_exact_mechanism','required_code_change':'required_code_change','evidence_or_experiment':'evidence_or_experiment','release_acceptance_test':'future_release_acceptance_test','source_classification':'source_classification'}
        for dest,src in fields.items(): r[dest]=corr.get(src)
        r['source_action_reviewed']=corr['source_action_reviewed']
        r['source_excerpt']=corr.get('source_excerpt')
        r['caller_chain_reviewed']=corr['caller_chain_reviewed']
        r['caller_chain_verification']=corr.get('caller_chain_verification',{})
        r['caller_trace_status']=r['caller_chain_verification'].get('status','UNSPECIFIED')
        if corr.get('caller_chain_candidate'): r['production_caller_entry']=corr['caller_chain_candidate']
        ver=r['caller_chain_verification']
        if ver.get('entrypoint_or_scope'): r['verified_entrypoint_or_scope']=ver['entrypoint_or_scope']
        if ver.get('verified_call_edges'):
            r['verified_call_edges']=ver['verified_call_edges']
            chain=[ver['verified_call_edges'][0].get('caller_symbol','?')]
            chain.extend(e.get('callee_symbol','?') for e in ver['verified_call_edges'])
            r['production_caller_entry']=ver.get('entrypoint_or_scope','')+'; verified static chain: '+' -> '.join(chain)
        no_call=ver.get('status','').startswith(('NO_PRODUCTION_CALLER','IMPLEMENTED_WITHOUT_PRODUCTION_CALLER'))
        if no_call: r['caller_trace_candidate_found']=False; r['caller_trace_candidates']=[]
    else:
        q=corr['review']
        r.update(executed_action=corr['executed_action_corrected'],current_resource_owner=q['current_resource_owner'],required_user_outcome=q['required_user_outcome'],proposed_replacement_owner_and_mechanism=q['proposed_owner']+'; '+q['mechanism'],required_code_change=q.get('required_code_change'),evidence_or_experiment=q['evidence_or_experiment'],release_acceptance_test=q['release_acceptance_test'],source_classification=q['source_classification'],source_action_reviewed=q['manual_action_reviewed'],caller_chain_reviewed=q.get('caller_chain_reviewed',q.get('manual_caller_reviewed')),caller_review_note=q['caller_chain_status'])
        r['source_excerpt']=corr.get('source_excerpt')
        r['caller_chain_ids']=q.get('caller_chain_ids',[])
        r['adapter_dispatch_callsite_refs']=q.get('adapter_dispatch_callsite_refs',[])
        r['static_callsite_evidence']=q.get('static_callsite_evidence')
        if q.get('caller_entry'): r['production_caller_entry']=q['caller_entry']
        if q.get('caller_chain_ids'):
            r['production_caller_entry']=(q.get('caller_entry','Verified static caller route')+'; route IDs: '+', '.join(q['caller_chain_ids']))
        status=q.get('caller_chain_status','')
        r['caller_trace_status']=status
        no_call=status.startswith('Verified no active production caller')
        if no_call: r['caller_trace_candidate_found']=False; r['caller_trace_candidates']=[]
    r['source_review_complete']=bool(r.get('source_action_reviewed') and r.get('caller_chain_reviewed'))
    r['review_complete']=r['source_review_complete']
    r['replacement_execution_proved']=False
    r['independent_action_reviewer']=fn
    # Correct old enclosing-function names from actual pinned source.
    if r['file'].endswith('runtime/apple_container.rs') and r['line']==172: r['symbol']='launch'
    if r['file'].endswith('runtime/apple_container.rs') and r['line']==288: r['symbol']='reconnect_with_client_and'
    if r['file'].endswith('runtime/launch/launch_runtime/docker.rs') and r['line'] in (311,321): r['symbol']='start'
# Preserve concise, explicit CLI caller paths for highlighted paths whose row
# level edge table is long; their independently checked route records remain.
for r in ledger:
    if r['file'].endswith('image/version.rs') and r['line']==52:
        r['production_caller_entry']='jackin prewarm -> cli/prewarm.rs:198,511 -> image/prewarm.rs:72 -> prewarm_agent_image -> prewarm_run.rs:43 -> validated.rs:88 or 119 -> build.rs:453 -> record_built_agent_version -> version.rs:132 -> extract_agent_version -> version.rs:52; load caller is not part of this verified chain.'
    if r['file'].endswith('jackin-workflow/src/verify.rs'):
        action={532:'timeout rm',575:'image inspect',583:'image pull',605:'worker exit-state inspect',615:'completed worker rm',776:'worker run',858:'Drop cleanup rm'}[r['line']]
        r['production_caller_entry']=f'jackin workflow record test -> workflow_cmd.rs:283/401/447 -> host_daemon.rs:1620/1641 -> WorkflowService::record_test -> run_test_command -> {action}; substeps use ensure_sandbox_image and finish_test_execution as applicable.'
    if r['file'].endswith('jackin-runtime-cleanup-prune-images/src/prune_images.rs'):
        r['production_caller_entry']='jackin prune -> app/prune_cmd.rs:66 or :100 -> runtime::prune_images; enumerates Docker role consumers and removes only unreferenced Jackin image.'
if set(reviewed)!=seen_reviewed:
    raise ValueError(f'independent corrections did not match ledger: missing={sorted(set(reviewed)-seen_reviewed)[:8]} ({len(set(reviewed)-seen_reviewed)}); extra={sorted(seen_reviewed-set(reviewed))[:8]}')
# Reconcile the two reviewed descriptions of the same Apple purge wrapper line
# only after both correction records have been matched and preserved.
apple_purge_rows=[r for r in ledger if r['file'].endswith('runtime/apple_container.rs') and r['line']==312 and r['symbol']=='ensure_absent_for_purge_with']
if len(apple_purge_rows)>1:
    keep=next((r for r in apple_purge_rows if r['method_or_command']=='list_containers'),apple_purge_rows[0])
    keep['method_or_command']='AppleContainerClient::list_containers'
    keep['executed_action']='Call client.list_containers to check whether the Apple workload exists; AppleContainerClient executes the `container list` command at apple_container_client.rs:198.'
    keep['lower_level_execution_ref']={'file':'crates/services/jackin-runtime-apple-container-client/src/apple_container_client.rs','line':198,'method_or_command':'container list --all --format json'}
    keep['deduplicated_source_aliases']=[{'file':r['file'],'line':r['line'],'symbol':r['symbol'],'method_or_command':r['method_or_command']} for r in apple_purge_rows if r is not keep]
    keep['duplicate_review_records_preserved']=True
    ledger=[r for r in ledger if not any(r is q for q in apple_purge_rows) or r is keep]
# Collapse preflight report/dispatch descriptions that point to the same
# actual expression. Preserve the reviewer/source trace as alias metadata.
daemon_rows=[r for r in ledger if r['file'].endswith('preflight.rs') and r['line']==190 and r['symbol']=='check_docker_daemon']
if len(daemon_rows)>1:
    keep=next((r for r in daemon_rows if r['method_or_command']=='BollardDockerClient::connect'),daemon_rows[0])
    keep['executed_action']='Connect BollardDockerClient to the configured Docker daemon; check_docker_daemon then calls ping at preflight.rs:191 as a separate ledger row.'
    keep['deduplicated_source_aliases']=[{'file':r['file'],'line':r['line'],'symbol':r['symbol'],'method_or_command':r['method_or_command'],'executed_action':r['executed_action']} for r in daemon_rows if r is not keep]
    keep['duplicate_review_records_preserved']=True
    ledger=[r for r in ledger if not any(r is q for q in daemon_rows) or r is keep]
version_rows=[r for r in ledger if r['file'].endswith('preflight.rs') and r['symbol']=='report_docker_version' and r['line'] in (209,210)]
if len(version_rows)>1:
    keep=next((r for r in version_rows if r['line']==210),version_rows[0])
    keep['method_or_command']='docker version --format {{.Server.Version}} (ExecRequest constructed at preflight.rs:209, executed at :210)'
    keep['executed_action']='Execute the docker version --format request and report Docker server version; request construction is at preflight.rs:209, execution is at :210.'
    keep['deduplicated_source_aliases']=[{'file':r['file'],'line':r['line'],'symbol':r['symbol'],'method_or_command':r['method_or_command'],'source':r.get('source'),'executed_action':r['executed_action']} for r in version_rows if r is not keep]
    keep['duplicate_review_records_preserved']=True
    ledger=[r for r in ledger if not any(r is q for q in version_rows) or r is keep]
# Post-review corrections from the final source pass.
for r in ledger:
    if r.get('supplemental_source_action'):
        f,n=r['file'],r['line']
        lines=(ROOT/f).read_text().splitlines()
        r['source_excerpt']=lines[n-1].strip()
        r['source_action_reviewed']=True
        r['caller_chain_reviewed']=True
        r['source_review_complete']=True
        r['review_complete']=True
        r['replacement_execution_proved']=False
        r['independent_source_reviewer']='review_source (supplemental source/caller pass)'
        if f.endswith('docker_client.rs') and n in (251,253,275,293,297):
            edges=[
              {'from':'BollardDockerClient::connect','file':'crates/adapters/jackin-docker/src/docker_client.rs','line':121,'to':'connect_to_cli_docker_context'},
              {'from':'connect_to_cli_docker_context','file':'crates/adapters/jackin-docker/src/docker_client.rs','line':249 if n in (251,253) else 243,'to':'Docker endpoint selection'}]
            if n==293: edges.append({'from':'active_docker_context_endpoint','file':'crates/adapters/jackin-docker/src/docker_client.rs','line':303,'to':'process_telemetry::exec_sync'})
            if n==297: edges.append({'from':'active_docker_context_endpoint','file':'crates/adapters/jackin-docker/src/docker_client.rs','line':301,'to':'append context selector to docker context inspect args'})
            r['caller_chain_verification']={'status':'VERIFIED_STATIC_CALL_PATH','entrypoint_or_scope':'BollardDockerClient::connect callsites: builder/image prewarm, preflight/doctor, role launch, status/usage/workspace/restore and console routes; exact caller rows link their user entries.','verified_call_edges':edges,'limits':'Static source only; no connection experiment inferred.'}
            connect_rows=[q for q in ledger if q.get('method_or_command')=='BollardDockerClient::connect' and not q.get('supplemental_source_action')]
            r['related_connection_call_sites']=[{'file':q['file'],'line':q['line'],'symbol':q['symbol'],'caller_chain_ids':q.get('caller_chain_ids',[])} for q in connect_rows]
            r['production_caller_entry']='BollardDockerClient::connect callsites recorded in related_connection_call_sites -> connect_to_cli_docker_context -> '+('Docker::connect_with_defaults' if n==251 else 'Docker::connect_with_host' if n==253 else 'DOCKER_HOST/DOCKER_CONTEXT endpoint decision')
        elif f.endswith('environment.rs'):
            r['caller_chain_verification']={'status':'VERIFIED_STATIC_CALL_PATH','entrypoint_or_scope':'Docker role launch: launch_runtime/docker.rs:50 -> environment::arguments:22 -> fixed_arguments:70; selected path launched by runtime/launch/launch_runtime.rs:173 and direct load entry chain in reviewed start rows.','verified_call_edges':[{'from':'launch_role_runtime','file':'crates/services/jackin-runtime/src/runtime/launch/launch_runtime/docker.rs','line':50,'to':'environment::arguments'},{'from':'arguments','file':f,'line':22,'to':'fixed_arguments'},{'from':'fixed_arguments','file':f,'line':n,'to':r['method_or_command']}],'limits':'String construction occurs unconditionally; the endpoint/cert values are appended to workload args only when dind_enabled.'}
            r['production_caller_entry']='jackin load/hardline role launch -> launch_runtime::docker::start -> environment::arguments -> fixed_arguments; DinD environment publication is conditional on docker grant.'
        elif f.endswith('image_build.rs'):
            r['caller_chain_verification']={'status':'VERIFIED_STATIC_CALL_PATH','entrypoint_or_scope':'Image builder: jackin-runtime-image/src/image/build.rs:184 and :433 -> docker_build_env.', 'verified_call_edges':[{'from':'build_base_or_derived_image','file':'crates/services/jackin-runtime-image/src/image/build.rs','line':184,'to':'docker_build_env'},{'from':'build_base_or_derived_image','file':'crates/services/jackin-runtime-image/src/image/build.rs','line':433,'to':'docker_build_env'}],'limits':'Static source only; no role image execution or BuildKit runtime proof inferred.'}
            r['production_caller_entry']='Jackin base/derived image build -> image/build.rs:184 or :433 -> docker_build_env; build/load/prewarm caller routes are listed in image ledger rows.'
        else:
            r['caller_chain_verification']={'status':'VERIFIED_STATIC_CALL_PATH','entrypoint_or_scope':'Optional Docker sidecar provisioning and prewarm caller routes.', 'verified_call_edges':[{'from':'run_dind_sidecar_headless_with_owner','file':f,'line':n,'to':r['method_or_command']},{'from':'prewarm/launch caller','file':f,'line':97,'to':'run_dind_sidecar_headless_with_owner'},{'from':'prewarm/launch caller','file':f,'line':320,'to':'run_dind_sidecar_headless_with_owner'}],'limits':'Static source only; no managed Docker engine execution proof inferred.'}
            r['production_caller_entry']='Optional DinD sidecar provisioning via run_dind_sidecar_headless_with_owner, called by explicit launch and prewarm paths; capability mechanism remains unresolved.'
    if r['file'].endswith('discovery.rs') and r['symbol']=='list_running_agent_display_names':
        r.update(source_classification='implemented discovery helper; no production caller',production_caller_entry='Definition/re-export and tests only; console uses running_role_containers instead.',caller_trace_candidate_found=False,caller_trace_candidates=[],caller_chain_reviewed=True,source_review_complete=True,review_complete=True,caller_trace_status='Verified no production caller by repository-wide reference search.')
    if r['file'].endswith('prune_images.rs'):
        image_owner='Docker/Buildx builder image store; not OpenShell target cache.'
        target_refs='Jackin retained `(target, digest, active/reconnect/retained)` receipts protect OpenShell execution images; prune target caches independently.'
        if r['line']==13:
            r.update(executed_action='Enumerate Jackin-managed `jk_*` image tags in the Docker builder store.',current_resource_owner=image_owner,required_user_outcome='Prune unused builder images without losing images needed by active or reconnectable workloads.',proposed_replacement_owner_and_mechanism='Keep Docker/Buildx builder cache pruning separate; OpenShell image caches use target digest references and a separate owner.',required_code_change='Replace role-container label consumer checks with digest/reference receipts across targets before builder or target image deletion.',release_acceptance_test='Image list across builder/targets; active/reconnect/retained digests protected; target outage blocks unsafe deletion.')
        elif r['line']==23:
            r.update(executed_action='List Docker role containers and derive image consumer references from labels before pruning.',current_resource_owner='Docker role containers plus Jackin image label convention.',required_user_outcome='Preserve images needed to reconnect or recreate retained work.',proposed_replacement_owner_and_mechanism='Query Jackin ownership receipts for every target and compare immutable image digests; unavailable targets conservatively block prune.',required_code_change='Replace role-container consumer discovery by Docker with target-scoped digest reference accounting; keep builder and target GC separate.',release_acceptance_test='Active, stopped/reconnectable, retained, unavailable, foreign and unused target image cases.')
        elif r['line']==53:
            r.update(executed_action='Remove an unreferenced Jackin-managed image from Docker builder image store.',current_resource_owner=image_owner,required_user_outcome='Reclaim only unused builder cache while preserving target images and recovery data.',proposed_replacement_owner_and_mechanism='Builder owner removes builder cache only after all target digest references are accounted for; OpenShell target owner separately prunes its cache.',required_code_change='Add ownership receipts and global known-target availability check before deletion; keep Docker builder removal separate from OpenShell target removal.',release_acceptance_test='Delete unused image; retain active/reconnect/retained refs; unavailable gateway prevents unsafe prune; foreign images untouched.')
        r['source_classification']='active image-prune operation; OpenShell reference design required'
# The final review found the old supervisor row conflated Linux and Darwin.
for r in doc['cross_cutting_production_callsites']:
    if r['file'].endswith('pid1.rs') and r['line']==884:
        r.update(symbol='install_sigchld_reaper',executed_action='Start Capsule Linux daemon SIGCHLD signal-wait thread that reaps daemon children; daemon boot calls this only under cfg(not macOS).',production_caller_entry='daemon/boot.rs:69-85::run_daemon -> pid1::install_sigchld_reaper at :77 when target is not macOS.',current_resource_owner='Capsule daemon process on Linux/non-macOS; not Darwin worker reaper.',proposed_replacement_owner_and_mechanism='The selected OpenShell/Linux supervisor must own child wait status or Capsule must retain the reaper under a supported process model; prove one wait owner.',evidence_or_experiment='Static source review only; no OpenShell process-lifetime/reaping proof.',release_acceptance_test='Linux Capsule child/grandchild exit, SIGCHLD, zombie and supervisor-failure tests; Darwin process tests separately on actual macOS execution.',source_classification='active Linux daemon SIGCHLD reaper; Darwin reaper is a separate main.rs path',source_action_reviewed=True,caller_chain_reviewed=True,source_review_complete=True,review_complete=True,replacement_execution_proved=False)
    if r['file'].endswith('supervisor_env.rs'):
        r['symbol']='apple_supervisor_env'
        r.update(production_caller_entry='runtime/apple_container.rs:106 calls apple_supervisor_env while constructing Apple workload environment; active Apple launch path.' ,source_action_reviewed=True,caller_chain_reviewed=True,source_review_complete=True,review_complete=True,replacement_execution_proved=False)
    if r['file'].endswith('process_isolation/linux.rs'):
        r.update(production_caller_entry='Capsule main.rs:25 -> process_isolation::run_isolated_command -> process_isolation/linux.rs:37 -> linux::run at :38.',source_action_reviewed=True,caller_chain_reviewed=True,source_review_complete=True,review_complete=True,replacement_execution_proved=False)
    if r['file'].endswith('process_isolation/linux/enforce.rs'):
        r.update(symbol='drop_privileges',production_caller_entry='Capsule main.rs:25 -> process_isolation::run_isolated_command -> linux.rs:63 -> drop_privileges at enforce.rs:143.',source_action_reviewed=True,caller_chain_reviewed=True,source_review_complete=True,review_complete=True,replacement_execution_proved=False)
    if r['file'].endswith('attach_protocol/handshake.rs'):
        r.update(production_caller_entry='Capsule daemon event loop -> events.rs:72 -> perform_handshake at handshake.rs:21.',source_action_reviewed=True,caller_chain_reviewed=True,source_review_complete=True,review_complete=True,replacement_execution_proved=False)
    if r['file'].endswith('usage_relay_proxy/identity.rs'):
        r.update(production_caller_entry='Capsule usage_relay_proxy.rs:127 invokes peer_identity for the authenticated Unix request.',source_action_reviewed=True,caller_chain_reviewed=True,source_review_complete=True,review_complete=True,replacement_execution_proved=False)
    if r['file'].endswith('usage_relay_proxy/authorization.rs'):
        r.update(production_caller_entry='Capsule usage_relay_proxy.rs:170 invokes authorizes before scoped usage capability dispatch.',source_action_reviewed=True,caller_chain_reviewed=True,source_review_complete=True,review_complete=True,replacement_execution_proved=False)
    if r['file'].endswith('session/spawn.rs'):
        r.update(production_caller_entry='Capsule session/spawn.rs:144 calls spawn_child_with_registration when starting a session child.',source_action_reviewed=True,caller_chain_reviewed=True,source_review_complete=True,review_complete=True,replacement_execution_proved=False)
# Reapply after correction-file merge: this active preservation guard was
# mistakenly grouped with unused checkpoint foundation rows in reviewer B's
# initial action text. The concrete source caller and failure behavior win.
for r in ledger:
    if r['file']=='crates/services/jackin-isolation/src/finalize.rs' and r['line']==275:
        r.update(executed_action='Execute the Jackin status command in the role container and parse its session count before cleanup. If exec fails or output is unparsable, conservatively treat sessions as present and preserve isolation work.',production_caller_entry='Active static callers: isolation/finalize.rs:222 finalize_foreground_session -> :275 has_jackin_sessions_by_id; runtime/attach/finalize.rs:97 and :154 call finalize_foreground_session; runtime/launch/launch_pipeline/launch_core/orchestrate/finalize.rs:99 and :146 also call it. Exact route IDs: route_a64d5a7a14, route_5bed4d6ee3, route_9f0f315d98.',source_classification='active preservation guard; verified production callers; OpenShell replacement untested',current_resource_owner='Jackin isolation finalization owns preservation decision; Docker exec currently reads Capsule session status.',required_user_outcome='Avoid deleting isolation work when sessions may remain or status cannot be trusted.',proposed_replacement_owner_and_mechanism='Retain Jackin fail-closed preservation decision. Replace Docker exec with authenticated target-scoped OpenShell sandbox exec/status transport only after session status protocol and identity are proved.',required_code_change='Keep status-check and parse failures as sessions-present; route status through target plus immutable sandbox identity and preserve work when target/status is unavailable.',evidence_or_experiment='Pinned source confirms active caller and fail-closed branches; no OpenShell status transport or live retention experiment proves replacement.',release_acceptance_test='Exercise zero/nonzero/unparseable status, exec failure, missing/unavailable sandbox, and stale identity; every uncertain state preserves work, while clean zero-session state follows current policy.',source_action_reviewed=True,caller_chain_reviewed=True,source_review_complete=True,review_complete=True,replacement_execution_proved=False)
    if r['file'].endswith('apple_container_client.rs') and r['line']==193:
        r.update(method_or_command='AppleContainerClient::inspect_container -> container list --all --format json',executed_action='Resolve a requested Apple container ID by listing all Apple containers and selecting the matching immutable ID; this helper does not execute `container inspect`. The underlying CLI list helper is at apple_container_client.rs:108-123 and command construction at :232.',source_classification='active Apple inspect-helper API operation; runtime replacement untested')
# Darwin reaper preparation/activation is separate from the non-macOS
# SIGCHLD thread above and only applies when Capsule actually runs on macOS.
doc['cross_cutting_production_callsites'].append({'file':'crates/apps/jackin-capsule/src/main.rs','line':39,'related_lines':[47],'symbol':'main','executed_action':'On macOS daemon startup, prepare the Darwin worker reaper before config/agent setup, then activate it immediately before daemon run. Linux instead calls install_sigchld_reaper from daemon boot.','production_caller_entry':'Capsule main entry: main.rs:35 enters daemon mode; macOS cfg calls prepare_darwin_reaper at :39, activate_darwin_reaper at :47; daemon/boot.rs requires active Darwin reaper at :75.','current_resource_owner':'Capsule process running on macOS; not remote Linux/VM compute.','required_user_outcome':'Child lifetime remains observable and reaped on the platform where Capsule process runs.','proposed_replacement_owner_and_mechanism':'Use the selected OpenShell compute process supervisor/reaper for remote workload; retain Darwin reaper only when Capsule itself runs on macOS and prove compatible child ownership.','required_code_change':'Separate OS-specific reaper behavior; do not treat Linux SIGCHLD thread as Darwin process-lifetime Tokio reaper or claim macOS host behavior for remote sandboxes.','evidence_or_experiment':'Static source review only; no OpenShell Capsule process-lifetime experiment.','release_acceptance_test':'Darwin process/reaper test on actual macOS workload target and Linux/VM test using their actual supervisor; no double wait owner.','source_classification':'active Darwin-only reaper lifecycle; runtime replacement untested','source_action_reviewed':True,'caller_chain_reviewed':True,'source_review_complete':True,'review_complete':True,'replacement_execution_proved':False})
# The reviewer traced all cross-cutting source calls listed here; this is
# source confirmation only and does not prove an OpenShell replacement.
for r in doc['cross_cutting_production_callsites']:
    r.update(source_action_reviewed=True,caller_chain_reviewed=True,source_review_complete=True,review_complete=True,replacement_execution_proved=False,independent_source_reviewer='review_source (cross-cutting action and caller pass)')
def normalized_behavior(row):
    override=row.get('source_behavior_override')
    if override:
        return override
    detail=row.get('source_classification','').lower()
    if ('implemented without production caller' in detail or 'without a production caller' in detail or 'no production caller found' in detail or 'has no production caller' in detail or
        'no active production caller' in detail or 'no product caller' in detail or
        'no production caller.' in detail or 'not invoked' in detail or 'uncalled' in detail):
        return 'Implemented without a production caller'
    if 'planned only' in detail or 'planned, not implemented' in detail:
        return 'Planned only'
    if detail.startswith('incomplete:') or detail=='incomplete':
        return 'Incomplete'
    # No experiment ran the unchanged pinned Jackin product path. Source and
    # fixtures do not constitute executed-product evidence.
    return 'Active but untested'
for rows in (ledger, doc['cross_cutting_production_callsites'], doc['build_test_infrastructure_callsites']):
    for row in rows:
        if row.get('file','').endswith('capture.rs') and row.get('line') in (432,485,517,540):
            row['source_classification']='implemented capture foundation; capture_checkpoint has no production caller, so confirm_paused/checkpoint operations are inactive'
        if row.get('file','').endswith('docker_client.rs') and row.get('line') in (942,958,974):
            row['source_classification']='implemented adapter foundation without a production caller; pause/unpause and full inspection are not used by production paths'
        if row.get('file','').endswith('apple_container_client.rs') and row.get('line') in (164,181,185,189,193,198):
            row['source_classification']='active Apple Container client operation; runtime replacement untested'
        if row.get('file','').endswith('apple_container_client.rs') and row.get('line')==189:
            row['source_classification']='implemented without a production caller; remove_with is also uncalled and production eject uses stop_with'
        if row.get('file','').endswith('runtime/apple_container.rs') and row.get('line') in (172,288,312):
            row['source_classification']='active Apple backend operation; runtime replacement untested'
        row['source_behavior']=normalized_behavior(row)
        row['replacement_execution_proved']=False
# The only explicit incomplete Apple lifecycle operation is a separate method
# foundation that returns Phase 0 failure; do not transfer that status to the
# working Apple run/start/stop/remove/inspect/list callsites.
doc['incomplete_source_behavior_records']=[{'file':'crates/services/jackin-runtime/src/runtime/backend.rs','line':207,'symbol':'AppleContainerBackend::finalize','source_behavior':'Incomplete','executed_action':'The active Apple backend finalization call reaches an explicit Phase 0 error instead of performing finalization.','production_caller_entry':'Persisted Apple hardline route: attach/hardline.rs:35-45 selects AppleContainerBackend::production().hardline; backend.rs:195 reconnects, :197 calls self.finalize, whose method at :207 returns the Phase 0 error.','current_user_effect':'Apple hardline/finalization through this backend path fails at the explicit Phase 0 method; do not claim successful finalization.', 'required_code_change':'Implement lifecycle finalization through the selected OpenShell target ownership model or retain Jackin trusted finalization with a proven target-scoped status path.','evidence_or_experiment':'Pinned source and exact caller chain only; Apple runtime/finalization was not executed.','release_acceptance_test':'Exercise Apple-selected hardline finalization on a real supported target after replacement; test normal completion, retained/dirty/unpushed work, failed inspection and interrupted finalization.','source_action_reviewed':True,'caller_chain_reviewed':True,'source_review_complete':True,'replacement_execution_proved':False}]
doc['cross_cutting_production_callsite_count']=len(doc['cross_cutting_production_callsites'])
doc['total_production_callsite_records']=len(ledger)+len(doc['cross_cutting_production_callsites'])
doc['source_assumption_reconciliations']=[
 {'file':'crates/core/jackin-core/src/env_model.rs','line':166,'related_lines':[167,168],'symbol':'RESERVED_RUNTIME_ENV_VARS','executed_action':'Static policy data reserves DOCKER_HOST, DOCKER_TLS_VERIFY and DOCKER_CERT_PATH from role-provided env configuration; `is_reserved` is checked by launch env assembly at launch_runtime/environment.rs:188 and by configuration validation at jackin-env/resolve.rs:171. This does not clear inherited host env by itself.','current_resource_owner':'Jackin configuration and launch environment policy.','required_user_outcome':'Agent-controlled configuration cannot replace runtime-owned Docker endpoint or certificate values.','proposed_replacement_owner_and_mechanism':'Keep trusted Jackin env allow/deny policy before publishing OpenShell env; optional Docker capability env is added only through an explicit owner.','evidence_or_experiment':'Static source only; no user-config env override test in OpenShell path.','release_acceptance_test':'Attempt config override of reserved Docker env; reject/omit it while explicitly enabled capability receives only its scoped values; normal sandbox gets none.','source_action_reviewed':True,'caller_chain_reviewed':True,'source_review_complete':True,'replacement_execution_proved':False},
 {'file':'crates/services/jackin-runtime/src/runtime/apple_container.rs','line':110,'symbol':'launch','executed_action':'Filter JACKIN_CAPSULE_FORCE_DAEMON, supervisor PID and debug keys from host-provided env before Apple Container launch; trusted Apple supervisor env is created separately.','current_resource_owner':'Jackin Apple backend environment construction and Apple Container process.','required_user_outcome':'Host configuration cannot impersonate Capsule supervisor settings in a launched workload.','proposed_replacement_owner_and_mechanism':'Remove Apple-specific backend; OpenShell process env is assembled from trusted role/agent/session config and cannot inherit operator-only supervisor env accidentally.','evidence_or_experiment':'Static source only; Apple runtime was not executed in this audit.','release_acceptance_test':'Host env injection of reserved supervisor keys is filtered; actual target receives selected trusted startup values.','source_action_reviewed':True,'caller_chain_reviewed':True,'source_review_complete':True,'replacement_execution_proved':False}
 ,{'file':'crates/services/jackin-runtime-launch-mounts/src/mounts.rs','line':720,'related_lines':[722,727,728],'symbol':'resolve_backend','executed_action':'Resolve persisted workspace/runtime backend selector, mapping absent or docker to Docker and apple-container to Apple Container; unknown strings fail. The mount builder uses this result to select backend-specific mounts.','production_caller_entry':'Workspace launch/materialization reads runtime backend and calls resolve_backend; Docker is default for unspecified selector. Exact callsites include workspace mount construction and launch backend dispatch.','current_resource_owner':'Jackin workspace config and runtime selector; Docker/Apple backend adapters own execution.','required_user_outcome':'Preserve explicit runtime selection for fresh setup with a single OpenShell target model; do not retain Docker/Apple execution fallbacks.','proposed_replacement_owner_and_mechanism':'Replace persisted runtime backend selector with configured OpenShell target identity; Docker remains only image builder or explicit capability owner.','evidence_or_experiment':'Static source only; no migration needed under fresh-setup reset allowance.','release_acceptance_test':'Fresh target selection routes mount/sandbox to configured OpenShell target; unknown target config is explicit and no legacy runtime fallback occurs.','source_action_reviewed':True,'caller_chain_reviewed':True,'source_review_complete':True,'replacement_execution_proved':False}
]
for row in doc['source_assumption_reconciliations']:
    row['source_behavior']=normalized_behavior(row)
    row['replacement_execution_proved']=False
if len(ledger)!=207: raise ValueError(f'expected 196 unique reviewed base rows after three duplicate-source consolidations + 11 supplemental direct rows, got {len(ledger)}')
doc['supplemental_source_actions']=[r for r in ledger if r.get('supplemental_source_action')]
# Keep route evidence once, with row-level route IDs linking back to it.
doc['verified_call_chains']=verified_routes
doc['independent_source_reviews']={fn:{k:v for k,v in audit.items() if k not in ('records','rows','verified_call_chains')} for fn,audit in review_audits.items()}
# Normalize B's historical counters to its completed static caller-chain pass;
# preserve the execution limitation and distinguish this from runtime proof.
if 'action-corrections-b.json' in doc['independent_source_reviews']:
    b=doc['independent_source_reviews']['action-corrections-b.json']
    b['caller_chains_independently_traced_count']=120
    b['review_complete_count']=120
    b['caller_chain_pending_count']=0
    b['counter_note']='Counts describe static source/caller-route review only; they do not imply execution or OpenShell replacement proof.'
for row in doc['build_test_infrastructure_callsites']:
    row.update(source_action_reviewed=True,caller_chain_reviewed=True,source_review_complete=True,review_complete=True,replacement_execution_proved=False,reviewer='review_source (static source/action/caller pass)')
doc['direct_callsite_ledger']=ledger
doc['direct_callsite_count']=len(ledger)
doc['source_coverage_summary']={'direct_rows':len(ledger),'unique_base_reviewed_direct_rows':len(ledger)-sum(bool(r.get('supplemental_source_action')) for r in ledger),'base_correction_records':len(reviewed),'deduplicated_source_representations':3,'supplemental_direct_rows':sum(bool(r.get('supplemental_source_action')) for r in ledger),'direct_rows_source_action_reviewed':sum(bool(r.get('source_action_reviewed')) for r in ledger),'direct_rows_caller_route_or_no_caller_verified':sum(bool(r.get('caller_chain_reviewed')) for r in ledger),'direct_rows_source_review_complete':sum(bool(r.get('source_review_complete')) for r in ledger),'direct_rows_replacement_execution_proved':sum(bool(r.get('replacement_execution_proved')) for r in ledger),'cross_cutting_rows':len(doc['cross_cutting_production_callsites']),'cross_cutting_rows_independently_reviewed':sum(bool(r.get('source_review_complete')) for r in doc['cross_cutting_production_callsites']),'build_test_infrastructure_rows':len(doc['build_test_infrastructure_callsites']),'build_test_infrastructure_rows_independently_reviewed':sum(bool(r.get('source_review_complete')) for r in doc['build_test_infrastructure_callsites']),'source_behavior_exception_rows':len(doc['incomplete_source_behavior_records']),'raw_matches':len(raw),'raw_matches_unresolved':sum(not r.get('review_complete',False) for r in raw),'excluded_support_matches':len(excluded),'independent_correction_rows':len(reviewed),'independent_correction_rows_unmatched':0}
(HERE/'source-inventory.json').write_text(json.dumps(doc,indent=2)+'\n')
print(f"{len(raw)} raw production matches; {len(ledger)} direct callsite/API rows; {len(excluded)} explicit test/support exclusions")
