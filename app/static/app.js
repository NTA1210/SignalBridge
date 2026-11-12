/* Local-only candidate evaluation UI. No third-party SDK, tracking or auto-send. */
let STORE = { campaigns: [], prospects: [], drafts: [], activity: [], config: {} };
let selectedId = null;
let currentTab = 'workspace';
const $ = id => document.getElementById(id);
const esc = str => String(str ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const short = (s,n=170) => String(s ?? '').length > n ? String(s).slice(0,n-1) + '…' : String(s ?? '');
const date = value => value ? new Date(value).toLocaleString(undefined,{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}) : '';
const safeSource = url => /^https:\/\/(x\.com|twitter\.com)\//i.test(url || '') ? url : '';
function notify(message,fail=false){const el=$('toast');el.textContent=message;el.hidden=false;el.style.background=fail?'#8a4b38':'#21483e';clearTimeout(notify.timer);notify.timer=setTimeout(()=>{el.hidden=true},3800)}
function error(message){$('app-error').hidden=false;$('app-error').textContent=message;notify(message,true)}
async function api(path, method='GET', body=null){
  const opts={method,headers:{'X-Local-Operator':'signalbridge-local'}};
  if(body!==null){opts.headers['Content-Type']='application/json';opts.body=JSON.stringify(body)}
  let response;
  try{response=await fetch(path,opts)}catch(e){throw new Error('Cannot reach local server. Start uvicorn.');}
  let result={};try{result=await response.json()}catch(_){result={detail:'Unexpected server response'}}
  if(!response.ok)throw new Error(typeof result.detail==='string'?result.detail:`Request failed (${response.status})`);
  return result;
}
async function refresh(){STORE=await api('/api/state');if(selectedId&&!STORE.prospects.some(p=>p.id===selectedId))selectedId=null;if(!selectedId&&STORE.prospects.length)selectedId=STORE.prospects[0].id;render()}
async function action(path,method='POST',body=null,done='Saved'){try{$('app-error').hidden=true;const result=await api(path,method,body);await refresh();notify(done);return result}catch(e){error(e.message);return null}}
function setTab(tab){currentTab=tab;$('nav-workspace').classList.toggle('active',tab==='workspace');$('nav-audit').classList.toggle('active',tab==='audit');document.getElementById(tab==='workspace'?'discovery-section':'audit-section').scrollIntoView({behavior:'smooth',block:'start'})}
const draftFor = id => STORE.drafts.find(d=>d.prospect_id===id);
const statusLabel = state => ({draft:'DRAFT',approved:'APPROVED',sending:'SENDING',sent:'SENT',uncertain:'UNCERTAIN',replied:'REPLIED'})[state]||'NOT STARTED';
const statusClass = state => state==='sent'||state==='replied'?'pill-sent':state==='approved'?'pill-approved':state==='uncertain'?'pill-uncertain':'pill-quiet';
function render(){
  const ds=STORE.drafts,ps=STORE.prospects,conf=STORE.config;
  $('provider-chip').textContent=(conf.ai_provider==='openai'?'LLM DRAFTS':'TEMPLATE DRAFTS')+' / '+(conf.x_send_enabled?'X ENABLED':'MOCK SAFE');
  $('mode-label').textContent=conf.x_send_enabled?'Live X transport enabled (restricted).':'Demo mode is synthetic and local by default.';
  $('mode-desc').textContent=conf.x_send_enabled?'Live sends require your approval, a consent flag and a test-recipient allowlist.':'Mock sends never reach X. A real X adapter exists but is switched off unless you enable it.';
  $('stat-people').textContent=ps.length;
  $('stat-review').textContent=ds.filter(x=>x.state==='draft').length;
  $('stat-sent').textContent=ds.filter(x=>['sent','replied'].includes(x.state)).length;
  $('stat-replies').textContent=ds.filter(x=>x.state==='replied').length;
  $('people-count').textContent=ps.length;
  $('prospect-list').innerHTML=ps.length?ps.map(p=>{
    const d=draftFor(p.id),initials=p.display_name.split(' ').slice(0,2).map(s=>s[0]||'').join('').toUpperCase(),isDemo=p.source_kind==='fictional_demo';
    return `<button type="button" class="person-card ${p.id===selectedId?'selected':''}" data-person="${esc(p.id)}">
      <span class="person-avatar">${esc(initials)}</span><span class="person-text"><span class="person-head"><strong>${esc(p.display_name)}</strong><span>${esc(p.score)}/100</span></span>
      <div class="person-role">@${esc(p.handle)} · ${esc(p.role)}</div>
      <div class="person-reason">${esc(p.reason)}</div>
      <span class="person-tags"><span>${isDemo?'SYNTHETIC DATA':p.source_kind==='x_api_recent_post'?'X POST SOURCE':'MANUAL SOURCE'}</span>${d?`<span>${esc(statusLabel(d.state))}</span>`:''}</span></span></button>`
  }).join(''):`<div class="empty">Enter a segment and click <strong>Discover demo</strong> to load fictional examples.</div>`;
  document.querySelectorAll('[data-person]').forEach(btn=>btn.addEventListener('click',()=>{selectedId=btn.dataset.person;render()}));
  renderDetails();renderAudit();
}
function renderDetails(){
  const p=STORE.prospects.find(x=>x.id===selectedId),out=$('detail-container');
  if(!p){$('detail-status').textContent='NO SELECTION';out.innerHTML='<div class="empty detail-empty"><div class="empty-symbol">✳</div><h3>Choose a prospect</h3><p>Inspect their evidence before generating a message.</p></div>';return}
  const d=draftFor(p.id),src=safeSource(p.evidence_url),demo=p.source_kind==='fictional_demo',init=p.display_name.split(' ').slice(0,2).map(x=>x[0]).join('').toUpperCase();
  $('detail-status').textContent=d?statusLabel(d.state):'RESEARCHED';$('detail-status').className='pill '+statusClass(d?.state);
  let block=`<div class="detail-person"><div class="person-avatar">${esc(init)}</div><div><h3>${esc(p.display_name)}</h3><p>@${esc(p.handle)} · ${esc(p.role)}</p></div></div>
    <section class="detail-section"><label>Why this person fits</label><p>${esc(p.reason)}</p><span class="foot-chip">Scored with transparent keyword signals · ${esc(p.score)} / 100</span></section>
    <section class="detail-section"><label>Evidence to ground the message</label><p class="evidence">“${esc(p.evidence_text)}”</p>
    ${src?`<a class="evidence-url" href="${esc(src)}" target="_blank" rel="noopener noreferrer">View original X post ↗</a>`:`<div class="inline-note">${demo?'FICTIONAL SCENARIO — evidence is not a real social post.':'This evidence was provided manually; verify before using in real outreach.'}</div>`}</section>`;
  if(!d){block+=`<section class="detail-section"><label>Message preparation</label><p>No DM has been drafted yet. Generate an evidence-based message to start human review.</p><div class="detail-actions"><button class="btn btn-primary" id="create-draft">✳ Create message draft</button></div></section>`;out.innerHTML=block;$('create-draft').onclick=()=>action('/api/drafts','POST',{prospect_id:p.id},'Draft prepared for review');return}
  const editable=d.state==='draft'||d.state==='rejected';
  block+=`<section class="detail-section"><label>${d.state==='draft'?'Review and edit personalized draft':'Message & delivery record'}</label><textarea id="draft-body" rows="5" ${editable?'':'readonly'}>${esc(d.body)}</textarea>
  <div class="detail-actions">
  ${editable?`<button class="btn btn-plain" id="save-draft">Save edits</button><button class="btn btn-primary" id="approve-draft">✓ Approve message</button>`:''}
  ${d.state==='approved'?`<button class="btn btn-primary" id="mock-send">↗ Send to mock transport</button><button class="btn btn-line" id="real-send" ${STORE.config.x_send_enabled?'':'disabled'}>Send via real X API</button>`:''}
  ${d.state==='sent'&&d.transport==='mock'?`<button class="btn btn-plain" id="simulate-reply">↳ Simulate consenting reply</button>`:''}
  ${d.state==='sent'&&d.transport==='x_api'?`<button class="btn btn-plain" id="sync-reply">↻ Sync actual X replies</button>`:''}
  </div>
  ${d.state==='approved'?`<div class="alert-inline">Human approval recorded. Mock delivery does not contact real people.${STORE.config.x_send_enabled?' Real send is restricted to explicitly consented, allowlisted test IDs.':''}</div>`:''}
  ${d.state==='uncertain'?`<div class="alert-inline">Delivery outcome UNKNOWN. Automatic retry is prohibited. Inspect X account history before taking any further action.</div>`:''}
  ${d.state==='sent'||d.state==='replied'?`<div class="inline-note">Transport: ${esc(d.transport.toUpperCase())} · Event ID: ${esc(d.remote_event_id)} · ${esc(d.sent_at?date(d.sent_at):'')}</div>`:''}
  ${d.state==='replied'?`<div class="alert-inline">A reply was recorded. Follow-up is a human decision; no automatic response will be sent.</div>`:''}
  </section>`;
  out.innerHTML=block;
  if($('save-draft'))$('save-draft').onclick=()=>action(`/api/drafts/${d.id}`,'PATCH',{body:$('draft-body').value},'Edited draft saved');
  if($('approve-draft'))$('approve-draft').onclick=async()=>{
    if($('draft-body').value!==d.body){const result=await action(`/api/drafts/${d.id}`,'PATCH',{body:$('draft-body').value},'Edited message saved');if(!result)return;}
    await action(`/api/drafts/${d.id}/approve`,'POST',null,'Human approval recorded');
  };
  if($('mock-send'))$('mock-send').onclick=()=>action(`/api/drafts/${d.id}/send`,'POST',{transport:'mock'},'MOCK DM sent locally — no actual X message');
  if($('real-send'))$('real-send').onclick=async()=>{
    if(!confirm('This sends a REAL DM via X API. Have you independently verified the recipient owns an allowlisted test account, consented and approved this text?'))return;
    await action(`/api/drafts/${d.id}/send`,'POST',{transport:'x_api'},'X API returned a remote event ID');
  };
  if($('simulate-reply'))$('simulate-reply').onclick=()=>action(`/api/drafts/${d.id}/simulate-reply`,'POST',{text:'Happy to discuss this! (Synthetic reply)'},'Synthetic reply recorded');
  if($('sync-reply'))$('sync-reply').onclick=()=>action(`/api/drafts/${d.id}/sync-replies`,'POST',null,'X DM lookup completed');
}
function renderAudit(){const el=$('audit-items');el.innerHTML=STORE.activity.length?STORE.activity.map(a=>`<div class="audit-row"><span class="audit-icon">✓</span><div class="audit-body"><strong>${esc(a.action.replaceAll('_',' ').replace(/\b\w/g,c=>c.toUpperCase()))}</strong>${esc(short(a.detail,140))}</div><time>${esc(date(a.at))}</time></div>`).join(''):'<div class="empty">Actions will appear here after you create and approve a draft.</div>'}
async function discover(isX){const segment=$('segment').value.trim();if(segment.length<3){error('Enter at least three characters for a segment');return};const payload=isX?{segment,x_query:$('x-query').value.trim()}:{segment};const endpoint=isX?'/api/discover/x':'/api/discover/demo';const res=await action(endpoint,'POST',payload,isX?'X post authors imported; review evidence':'Synthetic prospects loaded — no X calls');if(res?.prospects?.length){selectedId=res.prospects[0].id;render();$('workflow-section').scrollIntoView({behavior:'smooth',block:'start'})}}
$('run-demo').addEventListener('click',()=>discover(false));
$('run-x').addEventListener('click',()=>discover(true));
$('nav-audit').addEventListener('click',()=>setTab('audit'));
$('nav-workspace').addEventListener('click',()=>setTab('workspace'));
$('manual-form').addEventListener('submit',async e=>{
 e.preventDefault();const f=new FormData(e.target);let cid=STORE.campaigns[0]?.id;
 if(!cid){const campaign=await action('/api/campaigns','POST',{segment:$('segment').value},'Campaign created');cid=campaign?.campaign_id}
 if(!cid)return;
 const payload={campaign_id:cid,display_name:f.get('display_name'),handle:f.get('handle'),role:f.get('role'),bio:f.get('bio')||'',evidence_text:f.get('evidence_text'),evidence_url:f.get('evidence_url')||'',x_user_id:f.get('x_user_id')||'',consent_confirmed:!!f.get('consent_confirmed')};
 const p=await action('/api/prospects','POST',payload,'Sourced prospect saved');if(p?.id){selectedId=p.id;e.target.reset();render()}
});
refresh().catch(e=>error(e.message));
