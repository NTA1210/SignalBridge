"""Offline, repeatable candidate-assessment tests. Zero live API calls."""
import pytest
from fastapi.testclient import TestClient
from app import core
from app.main import app
from app import x_api

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('DATABASE_PATH',str(tmp_path/'test.sqlite3'))
    monkeypatch.setenv('AI_PROVIDER','template')
    monkeypatch.setenv('X_ENABLE_READ','false')
    monkeypatch.setenv('X_ENABLE_LIVE_SEND','false')
    monkeypatch.delenv('X_USER_ACCESS_TOKEN',raising=False)
    monkeypatch.delenv('X_TEST_ALLOWLIST_IDS',raising=False)
    with TestClient(app) as c:
        yield c


def post(c,payload,path):
    return c.post(path,json=payload,headers={'X-Local-Operator':'signalbridge-local'})


def patch(c,payload,path):
    return c.patch(path,json=payload,headers={'X-Local-Operator':'signalbridge-local'})


def seed(c,segment='robotics embodied AI'):
    resp=post(c,{'segment':segment},'/api/discover/demo')
    assert resp.status_code==200
    return resp.json()


def draft(c,person):
    response=post(c,{'prospect_id':person['id']},'/api/drafts')
    assert response.status_code==200,response.text
    return response.json()


def approve(c,did):
    return post(c,{},f'/api/drafts/{did}/approve')


def send(c,did,transport='mock'):
    return post(c,{'transport':transport},f'/api/drafts/{did}/send')


def test_health_and_local_write_guard(client):
    assert client.get('/healthz').json()['ok'] is True
    r=client.post('/api/discover/demo',json={'segment':'robotics'})
    assert r.status_code==403


def test_synthetic_discovery_and_explanations(client):
    result=seed(client)
    assert result['disclosure'].startswith('SYNTHETIC')
    assert result['prospects']
    assert all(p['source_kind']=='fictional_demo' for p in result['prospects'])
    assert any('robotics' in p['reason'] for p in result['prospects'])
    state=client.get('/api/state').json()
    assert len(state['prospects'])==len(result['prospects'])
    assert state['config']['x_send_enabled'] is False


def test_source_evidence_is_in_dm_and_no_fake_claims(client):
    person=seed(client)['prospects'][0]
    dm=draft(client,person)
    assert person['evidence_text'].rstrip('.') in dm['body']
    assert 'Sentry' not in dm['body']
    assert dm['state']=='draft'


def test_approval_and_send_mock_and_reply(client):
    person=seed(client)['prospects'][0]
    dm=draft(client,person)
    blocked=send(client,dm['id'])
    assert blocked.status_code==409
    approved=approve(client,dm['id'])
    assert approved.json()['state']=='approved'
    result=send(client,dm['id'])
    assert result.status_code==200
    assert result.json()['state']=='sent'
    assert result.json()['transport']=='mock'
    assert result.json()['remote_event_id'].startswith('MOCK_EVENT')
    reply=post(client,{'text':'Yes, in the demo'},f'/api/drafts/{dm["id"]}/simulate-reply')
    assert reply.status_code==200 and reply.json()['state']=='replied'
    assert client.get('/api/state').json()['activity'][0]['action']=='mock_reply_received'


def test_no_second_send_or_duplicate_draft(client):
    person=seed(client)['prospects'][0]
    d1=draft(client,person)
    d2=draft(client,person)
    assert d1['id']==d2['id']
    approve(client,d1['id'])
    assert send(client,d1['id']).status_code==200
    assert send(client,d1['id']).status_code==409


def test_recipient_alias_lock_across_campaigns(client):
    demo=seed(client)
    first=demo['prospects'][0]
    d1=draft(client,first)
    assert approve(client,d1['id']).status_code==200
    assert send(client,d1['id']).status_code==200
    cid=post(client,{'segment':'AI / robotics'},'/api/campaigns').json()['campaign_id']
    alt=post(client,{'campaign_id':cid,'display_name':'Same fictional tester','handle':first['handle'].upper(),
                     'role':'AI researcher','bio':'Dummy','evidence_text':'This is a separate demo note.'},'/api/prospects')
    assert alt.status_code==200
    d2=draft(client,alt.json())
    assert approve(client,d2['id']).status_code==200
    assert send(client,d2['id']).status_code==409


def test_alias_lock_by_x_id_even_if_handle_changes(client):
    cid=post(client,{'segment':'robotics'},'/api/campaigns').json()['campaign_id']
    def add(handle):
        return post(client,{'campaign_id':cid,'display_name':'Consenting tester','handle':handle,
          'x_user_id':'123456789012','role':'Robotics builder','bio':'test',
          'evidence_text':'Works on test robotics systems.'},'/api/prospects').json()
    d1=draft(client,add('test_one'))
    approve(client,d1['id'])
    assert send(client,d1['id']).status_code==200
    d2=draft(client,add('test_two'))
    approve(client,d2['id'])
    assert send(client,d2['id']).status_code==409


def test_edit_before_approve_only(client):
    person=seed(client)['prospects'][0]
    d=draft(client,person)
    assert patch(client,{'body':'Hi! Let us discuss your original robotics project.'},f'/api/drafts/{d["id"]}').status_code==200
    assert approve(client,d['id']).status_code==200
    assert patch(client,{'body':'Changed after approval now'},f'/api/drafts/{d["id"]}').status_code==409


def test_live_send_fails_closed_without_config(client):
    cid=post(client,{'segment':'AI robotics'},'/api/campaigns').json()['campaign_id']
    person=post(client,{'campaign_id':cid,'display_name':'Consenting test','handle':'test_tester',
        'x_user_id':'123456789','role':'Robot engineer','bio':'Testing X integration',
        'evidence_text':'Opted in to test robotics project interactions.','consent_confirmed':True},'/api/prospects').json()
    d=draft(client,person)
    approve(client,d['id'])
    assert send(client,d['id'],'x_api').status_code==400
    assert client.get('/api/state').json()['drafts'][0]['state']=='approved'


def test_no_live_send_without_allowlist(client,monkeypatch):
    monkeypatch.setenv('X_ENABLE_LIVE_SEND','true')
    monkeypatch.setenv('X_USER_ACCESS_TOKEN','fake_token_test_only')
    monkeypatch.setenv('X_TEST_ALLOWLIST_IDS','987654321')
    cid=post(client,{'segment':'robotics'},'/api/campaigns').json()['campaign_id']
    person=post(client,{'campaign_id':cid,'display_name':'Other recipient',
        'handle':'not_allowlisted','x_user_id':'123456789','role':'Robotics',
        'evidence_text':'Consented to a proof-of-concept test.','consent_confirmed':True},'/api/prospects').json()
    d=draft(client,person);approve(client,d['id'])
    assert send(client,d['id'],'x_api').status_code==400


def test_mock_reply_disallowed_for_real_unconfirmed(client):
    p=seed(client)['prospects'][0]
    d=draft(client,p)
    assert post(client,{},f'/api/drafts/{d["id"]}/simulate-reply').status_code==409


def test_x_read_off_by_default(client):
    r=post(client,{'segment':'AI robotics','x_query':'robotics -is:retweet'},'/api/discover/x')
    assert r.status_code==400 and 'disabled' in r.json()['detail'].lower()


def test_failed_provider_never_automatically_retries(client,monkeypatch):
    monkeypatch.setenv('X_ENABLE_LIVE_SEND','true')
    monkeypatch.setenv('X_USER_ACCESS_TOKEN','not_a_live_token')
    monkeypatch.setenv('X_TEST_ALLOWLIST_IDS','1122334455')
    def unavailable(*a,**k):raise TimeoutError('network timeout')
    monkeypatch.setattr(x_api,'send_dm',unavailable)
    cid=post(client,{'segment':'AI robotics'},'/api/campaigns').json()['campaign_id']
    p=post(client,{'campaign_id':cid,'display_name':'Agreed Tester','handle':'agreedtest1',
        'x_user_id':'1122334455','role':'Robotics engineer','bio':'robot',
        'evidence_text':'Agreed to the technical test demo.','consent_confirmed':True},'/api/prospects').json()
    d=draft(client,p);approve(client,d['id'])
    assert send(client,d['id'],'x_api').status_code==502
    state=client.get('/api/state').json()
    assert state['drafts'][0]['state']=='uncertain'
    assert send(client,d['id'],'x_api').status_code==409


def test_unsourced_prospect_rejected(client):
    cid=post(client,{'segment':'robotics'},'/api/campaigns').json()['campaign_id']
    r=post(client,{'campaign_id':cid,'display_name':'Test Person','handle':'test_a',
        'role':'Robotics', 'evidence_text':'short'},'/api/prospects')
    assert r.status_code==422


def test_x_event_parser_reads_real_reply_data_only(monkeypatch):
    """Test adapter response shape without reaching the network."""
    monkeypatch.setenv('X_ENABLE_READ','true')
    monkeypatch.setenv('X_USER_ACCESS_TOKEN','test_token')
    def response(method,url,**kwargs):
        assert method=='GET' and '/dm_conversations/with/123/dm_events' in url
        return {'data':[{'id':'1','sender_id':'123','event_type':'MessageCreate','text':'Hi','created_at':'2026-11-12T10:00:00Z'},
                        {'id':'2','sender_id':'888','event_type':'MessageCreate','text':'Outgoing','created_at':'2026-11-12T10:01:00Z'}]}
    monkeypatch.setattr(x_api,'_request',response)
    events=x_api.get_replies('123')
    assert len(events)==1 and events[0]['text']=='Hi'


def test_x_send_adapter_uses_documented_endpoint(monkeypatch):
    monkeypatch.setenv('X_ENABLE_LIVE_SEND','true')
    monkeypatch.setenv('X_TEST_ALLOWLIST_IDS','123')
    monkeypatch.setenv('X_USER_ACCESS_TOKEN','test_token')
    def fake_request(method,url,**kwargs):
        assert method=='POST' and url.endswith('/2/dm_conversations/with/123/messages')
        assert kwargs['json']=={'text':'Hello'}
        return {'data':{'dm_event_id':'event123','dm_conversation_id':'conv123'}}
    monkeypatch.setattr(x_api,'_request',fake_request)
    result=x_api.send_dm('123','Hello')
    assert result['remote_event_id']=='event123'
