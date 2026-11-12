// Analyze Text uses its own browser-local store, independent of account login.
const LOCAL_READING_KEY='linktext.analyze.local.v2';
const localServerRequest=readingRequest;
function readLocalArticles(){return JSON.parse(localStorage.getItem(LOCAL_READING_KEY)||'[]')}
function writeLocalArticles(rows){localStorage.setItem(LOCAL_READING_KEY,JSON.stringify(rows))}
readingRequest=async function(path,options={}){
 const requestUrl=new URL(path,location.origin);path=requestUrl.pathname;
 const rows=readLocalArticles(),body=options.body?JSON.parse(options.body):{};
 if(path==='/analyze'){
  const existing=rows.find(a=>a.request_key===body.request_key);if(existing)return existing;
  const response=await fetch(`${apiBase()}/api/v2/german-reading/analyze`,{method:'POST',credentials:'omit',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const data=await response.json();if(!response.ok)throw new Error(typeof data.detail==='string'?data.detail:'Analysis failed');
  const id=Date.now();let index=0;
  for(const group of ['vocab_knowledge_points','grammar_knowledge_points'])for(const p of data[group]||[]){p.knowledge_point_id=id*100+index++;p.learn_status='not_mastered'}
  Object.assign(data,{text_id:id,title:body.title,raw_text:body.text,level:body.level,reading_mode:body.reading_mode,visibility:'private',ids_are_persisted:true,status:'completed',request_key:body.request_key});
  rows.unshift(data);writeLocalArticles(rows);return data;
 }
 if(path==='/articles')return {articles:rows.map(a=>({...a,preview:a.raw_text.slice(0,240),word_count:a.raw_text.trim().split(/\s+/).length}))};
 if(path==='/knowledge-points')return {knowledge_points:rows.flatMap(a=>['vocab_knowledge_points','grammar_knowledge_points'].flatMap(group=>(a[group]||[]).map(p=>({id:p.knowledge_point_id,text_id:a.text_id,title:a.title,kind:group==='grammar_knowledge_points'?'grammar':String(p.vocab_body||'').includes(' ')?'expression':'vocabulary',payload:p,status:p.learn_status||'not_mastered'}))))};
 const progressMatch=path.match(/^\/knowledge-points\/(\d+)\/progress$/);
 if(progressMatch){for(const a of rows)for(const group of ['vocab_knowledge_points','grammar_knowledge_points']){const p=(a[group]||[]).find(p=>p.knowledge_point_id===Number(progressMatch[1]));if(p){p.learn_status=body.status;writeLocalArticles(rows);return {status:body.status}}}throw new Error('Knowledge point not found')}
 const match=path.match(/^\/articles\/(\d+)(\/review)?$/);
 if(match){const a=rows.find(a=>a.text_id===Number(match[1]));if(!a)throw new Error('Local article not found');const language=requestUrl.searchParams.get('ui_language')||reviewUiLanguage();const cached=a.reviews?.[language];if(!match[2])return {...a,review:cached?.generation_version===2?cached:undefined};if(cached?.generation_version===2&&cached.question_status==='completed')return cached;
 const points=['vocab_knowledge_points','grammar_knowledge_points'].flatMap((group,i)=>(a[group]||[]).map(p=>({id:`${i?'grammar':'vocab'}:${i?p.rule_id:p.vocab_id}`,type:i?'grammar':'vocabulary',display_name:p.display_name||p.vocab_body,explanation:p.explanation,sentence_contexts:(p.examples||[]).map(e=>e.sentence_body).filter(Boolean)})));
 const response=await fetch(`${apiBase()}/api/v2/german-reading/guest-review`,{method:'POST',credentials:'omit',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:a.raw_text,points,level:a.level,ui_language:language})});const data=await response.json();if(!response.ok)throw new Error(typeof data.detail==='string'?data.detail:'Review generation failed');a.review={...data,question_status:'completed',ui_language:language,generation_version:2};a.reviews={...a.reviews,[language]:a.review};writeLocalArticles(rows);return a.review;
 }
 return localServerRequest(requestUrl.pathname+requestUrl.search,options);
};

