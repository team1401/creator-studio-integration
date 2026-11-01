"""Resume only the dedicated context recorded by this test; never redispatch."""
from verify_live import *

def main():
    original=json.loads((ROOT/'live-verification.json').read_text())
    ctx=original['context']; path=original['artifact_path']
    c=A0Client('http://100.108.186.69:50080',budget=45,timeout=40)
    c.login(**vault_login());c.owned.add(ctx)
    result={'context':ctx,'original_failure_retained':'live-verification.json'}
    try:
        initial=c.poll(ctx)
        result['initial_paused']=initial['paused']
        c.resume(ctx); result['resume_readback']=not c.poll(ctx)['paused']
        deadline=time.monotonic()+180
        while time.monotonic()<deadline:
            p=c.poll(ctx)
            own=next(x for x in p['contexts'] if x['id']==ctx)
            save('dedicated-trace.json',{'context':ctx,'paused':p['paused'],'logs':p['logs']})
            if not own['running']:break
            time.sleep(6)
        result['running']=own['running']
        if own['running']:
            c.pause(ctx); result['deadline_paused']=c.poll(ctx)['paused']
        check="import pathlib,json,hashlib; p=pathlib.Path("+repr(path)+"); exists=p.is_file() and not p.is_symlink(); b=p.read_bytes() if exists else b''; print(json.dumps({'exists':exists,'content_matches':b==b'integration verified\\n','bytes':len(b),'sha256':hashlib.sha256(b).hexdigest() if exists else None,'resolved_path':str(p.resolve())}))"
        result['artifact']=json.loads(ssh('docker exec agent-zero-1 python3 -c '+shlex.quote(check)))
        result['verified']=result['artifact']['content_matches'] and not own['running']
        result['contexts_after']=meta(c.poll())
        result['preexisting_context_metadata_unchanged']={x['id']:x for x in original['contexts_before']}=={x['id']:x for x in result['contexts_after'] if x['id']!=ctx}
        # Read-only existing desktop state; no ensure/start action.
        d=c.post('plugins/_desktop/desktop_session',{'action':'state','include_screenshot':False,'context_id':ctx})
        save('desktop-state.json',d)
        result['ui_authenticated_http']=c.request('GET','/').status_code
        import requests
        result['ui_anonymous_http']=requests.get(c.base+'/',allow_redirects=False,timeout=10).status_code
    except Exception as e:
        result['error']=str(e) if isinstance(e,RuntimeError) else type(e).__name__
        try:c.pause(ctx);result['cleanup_paused']=c.poll(ctx)['paused']
        except Exception:result['cleanup_paused']=False
    result['audit']=c.audit
    save('continuation-verification.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='audit'},indent=2))
if __name__=='__main__':main()
