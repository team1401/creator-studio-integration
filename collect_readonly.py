"""Read-only deployment and link evidence; never starts a desktop."""
from verify_live import *
import requests

def main():
    c=A0Client('http://<agent-zero-host>:50080',budget=10)
    c.login(**vault_login())
    links=[]
    for path in ('/','/desktop/session/agent-zero-desktop/'):
        r=c.request('GET',path)
        a=requests.get(c.base+path,timeout=10,allow_redirects=False)
        entry={'url':c.base+path,'authenticated_http':r.status_code,'anonymous_http':a.status_code,'available':r.status_code==200}
        if r.status_code in (302,307) and path.startswith('/desktop/'):
            from urllib.parse import urlsplit, urljoin
            target=urlsplit(urljoin(c.base+path,r.headers.get('Location','')))
            if target.netloc=='<agent-zero-host>:50080' and target.path.startswith('/desktop/') and not target.query:
                final=c.request('GET',target.path)
                entry.update({'redirect_url':c.base+target.path,'final_http':final.status_code,'available':final.status_code==200})
        links.append(entry)
    for url in ('http://<agent-zero-host>:50081/',):
        r=requests.get(url,timeout=10,allow_redirects=False)
        links.append({'url':url,'anonymous_http':r.status_code,'authentication_verified':False})
    save('link-verification.json',{'links':links,'audit':c.audit})
    # docker inspect JSON may contain environment secrets: capture privately, allowlist only.
    all_containers=json.loads(ssh('docker inspect $(docker ps -aq)'))
    containers=[]
    for d in all_containers:
        v={'name':d['Name'].lstrip('/'),'id':d['Id'],'status':d['State']['Status'],'started_at':d['State']['StartedAt'],'image':d['Config']['Image']}
        if v['name'].startswith('agent-zero-'):
            v.update({'privileged':d['HostConfig']['Privileged'],'memory_bytes':d['HostConfig']['Memory'],'nano_cpus':d['HostConfig']['NanoCpus'],'ports':d['NetworkSettings']['Ports'],'mounts':d['Mounts'],'dockerman':d['Config']['Labels'].get('net.unraid.docker.managed')})
        containers.append(v)
    listeners=ssh('ss -ltnH')
    import re
    ports=sorted(set(int(m[1]) for line in listeners.splitlines() if (m:=re.search(r'\s\S+:(\d+)\s+\S+\s*$',line))))
    native=ssh("test -f /boot/config/plugins/dockerMan/templates-user/my-agent-zero-1.xml && test -f /boot/config/plugins/dockerMan/templates-user/my-agent-zero-2.xml && printf 'both native templates present\\n'; df -h /var/lib/docker /mnt/fastssd; stat -c '%a %n' /mnt/fastssd/AppData/agent-zero-1/usr/.env")
    source=ssh("docker exec agent-zero-1 sh -c 'git -C /a0 describe --tags --always; sha256sum /a0/api/message_async.py /a0/api/message.py /a0/api/poll.py /a0/api/pause.py /a0/api/chat_create.py /a0/api/csrf_token.py'")
    save('deployment-facts.json',{'containers':containers,'listening_tcp_ports':ports,'candidate_50082_not_listening':50082 not in ports,'port_note':'Read-only observation, not reservation; recheck immediately before native deployment.','native':native,'live_source':source})
    print(json.dumps({'links':links,'candidate_50082_not_listening':50082 not in ports,'container_count':len(containers)},indent=2))
if __name__=='__main__':main()
