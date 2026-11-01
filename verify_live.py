"""Bounded authorized live test. Vault values and sessions stay in memory."""
import json, os, re, shlex, sqlite3, subprocess, time, uuid
from pathlib import Path
from a0_client import A0Client
ROOT=Path(__file__).parent

def ssh(command):
    r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','root@100.108.186.69',command],capture_output=True,text=True,timeout=30)
    if r.returncode: raise RuntimeError('Strix read-only SSH operation failed')
    return r.stdout

def vault_login():
    db=sqlite3.connect('file:/home/helix/.hermes-minimal/state.db?mode=ro',uri=True)
    row=db.execute("select content from messages where id=104372 and session_id='20260921_065527_ebd12a' and role='user'").fetchone()
    match=re.fullmatch(r'The password for that is (\S+)\s*',row[0],re.I) if row else None
    if not match: raise RuntimeError('BLOCK: authorized Keychain credential reference unavailable')
    remote='''import json,sys,subprocess,os
p=json.load(sys.stdin)
def run(a,e=None):
 r=subprocess.run(a,env=e,capture_output=True,text=True,stdin=subprocess.DEVNULL,timeout=70)
 if r.returncode: raise RuntimeError('Vault command failed')
 return r.stdout.strip()
k='/Users/helix/Library/Keychains/login.keychain-db'
run(['security','unlock-keychain','-p',p['keychain_password'],k])
e=os.environ.copy()
e['BW_PASSWORD']=run(['security','find-generic-password','-w','-a','helix','-s','HERMES_BITWARDEN_MASTER_PASSWORD',k])
e['BW_SESSION']=run(['/opt/homebrew/bin/bw','unlock','--passwordenv','BW_PASSWORD','--raw'],e)
e.pop('BW_PASSWORD',None)
assert json.loads(run(['/opt/homebrew/bin/bw','status'],e))['status']=='unlocked'
v=json.loads(run(['/opt/homebrew/bin/bw','get','item','4534c9ae-e837-420c-9ad0-b4ea0101619a'],e))
assert v['name']=='Strix Agent Zero 1' and v.get('organizationId') and v.get('collectionIds')
print(json.dumps({'username':v['login']['username'],'password':v['login']['password']}))
'''
    r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','helix@100.117.95.108','/opt/homebrew/bin/python3 -c '+shlex.quote(remote)],input=json.dumps({'keychain_password':match[1]}),capture_output=True,text=True,timeout=190)
    try:
        if r.returncode: raise ValueError()
        v=json.loads(r.stdout)
        assert v.get('username') and v.get('password')
        return v
    except Exception: raise RuntimeError('BLOCK: existing authorized Mac Keychain/Bitwarden retrieval failed; no fallback credential extraction attempted') from None

def meta(p):
    return [{k:x.get(k) for k in ('id','running','paused','created_at')} for x in p.get('contexts',[])]

def save(name,obj):
    (ROOT/name).write_text(json.dumps(obj,indent=2)+'\n')

def main():
    client=A0Client('http://100.108.186.69:50080')
    result={'started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'argus':'not_connected','automatic_dispatch_ready':False,'tested_instance':'agent-zero-1'}
    context=None
    try:
        credentials=vault_login();client.login(**credentials);del credentials
        before=client.poll();result['contexts_before']=meta(before)
        save('preflight.json',result)
        if any(x.get('running') and not x.get('paused') for x in before.get('contexts',[])):
            raise RuntimeError('BLOCK: worker has an active unpaused context; preserving workload')
        desktop=client.post('plugins/_desktop/desktop_session',{'action':'status'})
        save('desktop-status.json',desktop)
        context=client.create(); result['context']=context
        isolated='/a0/usr/workdir/creator-studio-integration-'+uuid.uuid4().hex
        path=isolated+'/integration-verified.txt';result['artifact_path']=path
        prompt=f'Bounded integration verification only. Create directory {isolated} and text file {path} containing exactly integration verified followed by a newline. Use code_execution_tool only, at most two tool actions, then return the absolute path and stop. Do not use browser, websites, network, paid tools, delegation, other workdirs, settings, or other files. Do not modify any existing file. This is an isolated harmless task.'
        result['send']=client.send(context,prompt)
        result['pause_ack']=client.pause(context)
        paused=client.poll(context)
        result['pause_verified']=paused['paused'] is True
        result['resume_ack']=client.resume(context)
        resumed=client.poll(context);result['resume_verified']=resumed['paused'] is False
        deadline=time.monotonic()+180
        latest=resumed
        while time.monotonic()<deadline:
            latest=client.poll(context)
            own=next((x for x in latest['contexts'] if x['id']==context),{})
            if not own.get('running') and latest.get('logs'): break
            time.sleep(5)
        # Store only this dedicated chat's logs; no unrelated tasks/notifications.
        save('dedicated-trace.json',{'context':context,'paused':latest['paused'],'logs':latest['logs']})
        own=next((x for x in latest['contexts'] if x['id']==context),{})
        result['running_at_end']=own.get('running')
        if own.get('running'):
            client.pause(context);result['deadline_pause_verified']=client.poll(context)['paused']
        check="import pathlib,json,hashlib; p=pathlib.Path("+repr(path)+"); exists=p.is_file() and not p.is_symlink(); b=p.read_bytes() if exists else b''; print(json.dumps({'exists':exists,'content_matches':b==b'integration verified\\n','bytes':len(b),'sha256':hashlib.sha256(b).hexdigest() if exists else None,'resolved_path':str(p.resolve())}))"
        artifact=json.loads(ssh('docker exec agent-zero-1 python3 -c '+shlex.quote(check)))
        result['artifact']=artifact
        result['verified']=artifact['content_matches'] and not result['running_at_end']
        result['contexts_after']=meta(client.poll())
        old={x['id']:x for x in result['contexts_before']}
        new={x['id']:x for x in result['contexts_after'] if x['id']!=context}
        result['preexisting_context_metadata_unchanged']=old==new
        result['desktop_status_keys']=list(desktop)
    except Exception as e:
        result['error']=str(e) if isinstance(e,(RuntimeError,ValueError)) else type(e).__name__
        if context:
            try: client.pause(context);result['error_cleanup_paused']=client.poll(context)['paused']
            except Exception: result['error_cleanup_paused']=False
    finally:
        result['audit']=client.audit
        save('live-verification.json',result)
        print(json.dumps({k:v for k,v in result.items() if k not in ('audit',)},indent=2))

if __name__=='__main__': main()
