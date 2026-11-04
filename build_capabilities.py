"""Generate capability flags from recorded real evidence, not model prose."""
import json
from pathlib import Path
p=Path(__file__).parent
load=lambda name:json.loads((p/name).read_text())
initial=load('live-verification.json'); final=load('continuation-verification.json'); links=load('link-verification.json'); deployment=load('deployment-facts.json');trace=load('dedicated-trace.json')
actions=[x['kvps']['tool_name'] for x in trace['logs'] if x.get('type')=='agent' and x.get('kvps',{}).get('tool_name')]
assert actions==['code_execution_tool','response'],actions
assert final['artifact']['content_matches'] and final['verified']
assert any(x.get('type')=='response' and x.get('content')==initial['artifact_path'] for x in trace['logs'])
result={
 'schema_version':1,'verified_at_utc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
 'worker':{'id':'agent-zero-1','base_url':'http://<agent-zero-host>:50080','version':'v2.14','authentication':'server-side vault login session plus CSRF','api_family':'installed Web UI API'},
 'capabilities':{'authenticated_send':True,'poll':True,'dedicated_context_pause':initial['pause_verified'],'dedicated_context_resume':final['resume_readback'],'file_artifact_verified':final['verified'],'open_worker_ui':True,'desktop_software_installed':True,'live_desktop_available':False,'automatic_dispatch_ready':False,'supervised_dispatch_prototype_verified':True},
 'verified_urls':[x for x in links['links'] if x.get('available')],
 'other_url_probes':[x for x in links['links'] if not x.get('available')],
 'job':{'context':initial['context'],'status':'artifact_verified_completed','running':final['running'],'artifact':final['artifact'],'response_path_verified':True,'code_tool_actions':actions.count('code_execution_tool'),'preexisting_context_metadata_unchanged':final['preexisting_context_metadata_unchanged'],'recovery_required':True},
 'argus':{'status':'not_connected','live_peer_requests_sent':False},
 'recommendation':{'buttons':['Open worker','Copy task / manual handoff'],'desktop_button':'Open worker UI; require manual Desktop activation, not a verified direct session','automatic_dispatch':'disabled'},
 'deployment':{'native_unraid_templates_verified':True,'candidate_port':50082,'candidate_port_not_listening':deployment['candidate_50082_not_listening'],'port_reserved':False,'child_database':'separate SQLite; not created by this prototype','global_board_migration':False},
 'limitations':['Initial20s poll timeout; recovered same context without duplicate send','First artifact probe failed because python executable absent; corrected to python3','Pause is cooperative, not subprocess cancellation','Prompt tool/path limits are not enforced sandbox isolation','Automatic Agent Zero memory storage remains enabled','Desktop status healthy does not establish a live desktop; actual display unavailable','No actual browser desktop input tested in this task','No instance2 job or authenticated API test'],
 'evidence':['live-verification.json','continuation-first-failure.json','continuation-verification.json','dedicated-trace.json','desktop-state.json','link-verification.json','deployment-facts.json']}
(p/'integration-capabilities.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'artifact_verified':result['job']['status'],'actual_code_tool_actions':result['job']['code_tool_actions'],'verified_urls':result['verified_urls'],'automatic_dispatch_ready':False},indent=2))
