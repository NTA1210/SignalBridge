"""Run the same end-to-end mock workflow over HTTP without any external calls.

Usage after starting uvicorn: python scripts/smoke_demo.py
"""
import os
import httpx
base=os.getenv('SIGNALBRIDGE_BASE_URL','http://127.0.0.1:8000')
with httpx.Client(base_url=base,timeout=8,headers={'X-Local-Operator':'signalbridge-local'}) as c:
    def post(path,data=None):
        r=c.post(path,json=data or {});r.raise_for_status();return r.json()
    assert c.get('/healthz').json()['ok']
    seed=post('/api/discover/demo',{'segment':'robotics embodied AI'})
    person=seed['prospects'][0]
    draft=post('/api/drafts',{'prospect_id':person['id']})
    approved=post(f"/api/drafts/{draft['id']}/approve")
    result=post(f"/api/drafts/{draft['id']}/send",{'transport':'mock'})
    assert approved['state']=='approved' and result['state']=='sent' and result['transport']=='mock'
    r=c.post(f"/api/drafts/{draft['id']}/send",json={'transport':'mock'})
    assert r.status_code==409, 'Duplicate prevention failed'
    reply=post(f"/api/drafts/{draft['id']}/simulate-reply",{'text':'Yes (synthetic)'})
    assert reply['state']=='replied'
    print('PASS mock E2E: discover -> draft -> approve -> send -> duplicate blocked -> reply')
