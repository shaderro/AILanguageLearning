// Standalone Analyze Text flow. No imports or styles are applied to Main Assistant.
let importedText='', importedTitle='', importedFile=null, isDemo=false, busy=false, libraryRows=[], reviewOriginalAnswers=null;
let activePointOffset=0, readingExpanded=false;
// Figma 2496:1381: 18.75%–30% of the 8s timeline = 900ms;
// old card 0 → -52px / opacity 1 → 0, new card +52 → 0px / 0 → 1.
const READING_MOTION={duration:900,easing:'ease-in-out',distance:44};
let renderedSentenceIndex=-1,readingAnimations=[],readingTransition=false;
let furthestSentenceIndex=0,readingModeState='normal',readingArticleSentences=null;
let revisitKnowledgeOpen=false;
let readingReturnState=null;
const reduceMotion=()=>matchMedia('(prefers-reduced-motion: reduce)').matches;
const $=id=>document.getElementById(id);
const mode=()=>document.querySelector('input[name="readingMode"]:checked').value;
function showView(id){
  if(id!=='readingView'){readingAnimations.forEach(a=>a.cancel());readingAnimations=[];readingTransition=false}
  const stages={sourceView:'analysis',statusView:'analysis',libraryView:'library',prepView:'preview',readingView:'reading',quizView:'review',doneView:'completed'};
  sessionState.current_stage=stages[id]||id;
  document.querySelectorAll('.view').forEach(v=>v.classList.toggle('active',v.id===id));
  document.body.classList.toggle('is-reading',id==='readingView');
  window.scrollTo({top:0,behavior:'instant'});
  if(id==='prepView')renderCard();if(id==='readingView')renderReading();if(id==='quizView')renderQuiz();
  const heading=document.querySelector('#'+id+' h1');if(heading){heading.tabIndex=-1;heading.focus({preventScroll:true})}
}
function sourceError(message){$('sourceError').textContent=message;$('sourceError').classList.remove('hidden')}
function setBusy(value){busy=value;document.querySelectorAll('#sourceView .primary').forEach(b=>b.disabled=value);$('fileAnalyze').disabled=value||!importedFile}
function updateCount(){const raw=$('customText').value,words=raw.trim()?raw.trim().split(/\s+/).length:0;$('wordCount').textContent=`${words} / 800 words · ${raw.length.toLocaleString()} / 12,000 characters`;$('wordCount').classList.toggle('over',words>800||raw.length>12000)}
$('customText').addEventListener('input',updateCount);
function selectFile(file){if(!file)return;if(!/\.(txt|md|pdf)$/i.test(file.name)){sourceError('Choose a TXT, MD or PDF file.');return}if(file.size>10*1024*1024){sourceError('Choose a file smaller than 10 MB.');return}importedFile=file;$('fileName').textContent=file.name;$('fileAnalyze').disabled=false}
$('sourceFile').addEventListener('change',e=>selectFile(e.target.files[0]));
for(const event of ['dragenter','dragover'])$('dropzone').addEventListener(event,e=>{e.preventDefault();$('dropzone').classList.add('drag-active')});
for(const event of ['dragleave','drop'])$('dropzone').addEventListener(event,e=>{e.preventDefault();$('dropzone').classList.remove('drag-active');if(event==='drop')selectFile(e.dataTransfer.files[0])});
async function importSource(kind){
  if(busy)return;$('sourceError').classList.add('hidden');setBusy(true);
  try{
    let raw='',title='';
    if(kind==='paste'){raw=$('customText').value.trim();title=$('pasteTitle').value.trim()}
    else if(kind==='file'){
      if(!importedFile)throw new Error('Choose a file first.');title=$('fileTitle').value.trim()||importedFile.name.replace(/\.[^.]+$/,'');
      if(/\.pdf$/i.test(importedFile.name)){const form=new FormData();form.append('file',importedFile);const token=localStorage.getItem('access_token');const response=await fetch(`${apiBase()}/api/v2/german-reading/import/file`,{method:'POST',headers:token?{Authorization:`Bearer ${token}`}:{},credentials:'include',body:form});const data=await response.json();if(!response.ok)throw new Error(data.detail||'Unable to read the PDF.');raw=data.text}
      else raw=(await importedFile.text()).trim();
    }else{
      const url=$('sourceUrl').value;const data=await readingRequest('/import/url',{method:'POST',body:JSON.stringify({url})});raw=data.text;title=$('urlTitle').value.trim()||data.title||'Web article';
    }
    if(!raw.trim())throw new Error('No readable text was found.');
    if(raw.length>12000||raw.trim().split(/\s+/).length>800)throw new Error('Choose a shorter passage: up to 800 words and 12,000 characters.');
    importedText=raw;importedTitle=title||'German reading';isDemo=false;$('demoBadge').classList.add('hidden');
    $('statusTitle').textContent='Article uploaded successfully';$('statusDescription').textContent='Your content is ready. Start the analysis when you’re ready.';
    $('statusSymbol').textContent='✓';$('statusSymbol').classList.remove('loading');$('statusLabel').textContent='NEXT · ANALYZE YOUR ARTICLE';$('statusGuidance').textContent='We’ll identify vocabulary and grammar, then prepare your article for reading.';
    $('fileSummary').textContent=`${importedTitle} · ${raw.split(/\s+/).length} words · ${mode()} mode`;$('statusActions').classList.remove('hidden');showView('statusView');
  }catch(e){sourceError(e.message||'Unable to import this content.')}finally{setBusy(false)}
}
function resetLearning(){cardIndex=0;sentenceIndex=0;quoteIndex=0;expanded=false;translated=false;activePointOffset=0;readingExpanded=false;known.clear();points.filter(p=>p.learnStatus==='mastered').forEach(p=>known.add(p.id));seen.clear();answers={};reviewOriginalAnswers=null;learningIds=points.filter(p=>!known.has(p.id)).map(p=>p.id);reviewQuestions=[];reviewGenerationPromise=null;reviewGenerationError='';confirmedAnswers.clear();quizIndex=0;quizPhase='idle';sessionState.article=articleText;sessionState.sentences=sentences;sessionState.knowledge_points=points;sessionState.user_answers=answers;sessionState.quiz_completed=false;if(!isDemo&&savedReview?.question_status==='completed'&&savedReview.ui_language===reviewUiLanguage()){try{reviewQuestions=validateQuizQuestions(savedReview.questions,points.map(p=>p.id));sessionState.quiz_questions=reviewQuestions;reviewGenerationPromise=Promise.resolve(reviewQuestions)}catch(e){savedReview=null}}}
async function startPreview(){
  if(busy)return;busy=true;$('statusActions').classList.add('hidden');$('statusSymbol').textContent='';$('statusSymbol').classList.add('loading');$('statusTitle').textContent='Analyzing your article';$('statusDescription').textContent='Identifying useful vocabulary and grammar for your level.';$('statusLabel').textContent='ANALYSIS IN PROGRESS';$('statusGuidance').textContent='Keep this page open. Your content will appear here when analysis is complete.';
  try{const signature=importedText+'|'+$('levelSelect').value+'|'+mode();if(signature!==analysisRequestSignature){analysisRequestKey=null;analysisRequestSignature=signature}
    const data=await readingRequest('/analyze',{method:'POST',body:JSON.stringify({text:importedText,title:importedTitle,level:$('levelSelect').value,reading_mode:mode(),request_key:analysisRequestKey||(analysisRequestKey=crypto.randomUUID())})});
    if(data.status!=='completed')throw new Error('Analysis is still processing. Open it from your library shortly.');
    if(!data.text_id)toast('This article is temporary. Sign in before analyzing to save it to your library.');mapAnalysisToUi(data);if(!sentences.length)throw new Error('No readable sentences were found.');articleText=importedText;persistedArticleId=data.text_id;resetLearning();analysisRequestKey=null;document.querySelector('.title').textContent=data.title||importedTitle;history.replaceState(null,'',data.text_id?`?text_id=${data.text_id}`:location.pathname);showView('prepView');
  }catch(e){$('statusSymbol').classList.remove('loading');$('statusSymbol').textContent='!';$('statusTitle').textContent='Your article is not ready yet';$('statusDescription').textContent=e.message;$('statusGuidance').textContent='Your text is still available. Return to edit it, or retry the analysis.';$('statusActions').classList.remove('hidden');if(/分析或保存失败/.test(e.message))analysisRequestKey=null}
  finally{busy=false}
}
function previewProgress(){return `<div class="preview-meter" aria-label="Knowledge point progress"><span>${Math.min(cardIndex+1,points.length)} / ${points.length}</span><div class="progress"><i style="width:${points.length?(cardIndex+1)/points.length*100:100}%"></i></div></div>`}
function renderCard(){
  const host=$('flashCard');document.querySelector('.card-wrap>.card-meta').classList.add('hidden');$('cardProgress').parentElement.classList.add('hidden');
  if(cardIndex>=points.length){host.innerHTML=`<div class="flash ready"><span class="meta">Preview complete · ${known.size} already known</span><div class="progress"><i style="width:100%"></i></div><span class="kind">READY TO READ</span><h2>Ready to read the original?</h2><p>${points.length-known.size} expressions will return while you read.</p><div class="actions"><button class="softbtn" onclick="cardIndex=Math.max(0,points.length-1);renderCard()">Review preview</button><button class="primary" onclick="startReading()">Start reading →</button></div></div>`;return}
  const p=points[cardIndex],example=p.simpleExample||sentences.find(s=>p.sentenceIds.includes(s.id))?.de||'';
  host.innerHTML=`<div class="flash">${previewProgress()}<div class="preview-heading"><h2 lang="de">${escapeHtml(p.de)}</h2>${p.category?`<div class="meta">${escapeHtml(p.category)}</div>`:''}</div><div class="example-box" lang="de">${p.type==='语法重点'?grammarExample(p):renderSimpleExample(example)}</div>${expanded?`<div class="explanation" id="previewExplanation"><div class="kind">EXPLANATION</div>${renderExplanation(p,true)}</div><div class="actions"><button class="softbtn" aria-expanded="true" aria-controls="previewExplanation" onclick="expanded=false;renderCard()">Hide explanation</button><button class="primary" onclick="nextCard(false)">Keep learning →</button></div>`:`<div class="actions"><button class="softbtn" aria-expanded="false" onclick="expanded=true;renderCard()">Show explanation</button><button class="primary" onclick="nextCard(true)">I know this →</button></div>`}</div>`;
}
function currentPoints(){return (sentences[sentenceIndex]?.points||[]).filter(k=>points[k])}
function pointMarkup(s,index){const spans=[];points.forEach((p,k)=>(p.spans||[]).filter(x=>x.sentenceId===s.id).forEach(x=>spans.push({...x,k})));spans.sort((a,b)=>a.start-b.start);let html='',cursor=0;const active=currentPoints()[activePointOffset];for(const span of spans){if(span.start<cursor)continue;html+=escapeHtml(s.de.slice(cursor,span.start))+`<button class="expression ${span.k===active?'highlight':''}" onclick="event.stopPropagation();focusPoint(${span.k})">${escapeHtml(s.de.slice(span.start,span.end))}</button>`;cursor=span.end}return html+escapeHtml(s.de.slice(cursor))}
function focusPoint(index){const offset=currentPoints().indexOf(index);if(offset<0)return;activePointOffset=offset;revisitKnowledgeOpen=true;readingExpanded=true;renderReading();if(readingModeState==='revisit')$('knowledgeDetail').scrollIntoView({block:'nearest',behavior:reduceMotion()?'instant':'smooth'})}
function showKnowledgePoint(index){focusPoint(index)}
function renderReading(){
  if(readingArticleSentences!==sentences){readingArticleSentences=sentences;furthestSentenceIndex=sentenceIndex;readingModeState='normal';readingReturnState=null}
  if(readingModeState!=='revisit')furthestSentenceIndex=Math.max(furthestSentenceIndex,Math.min(sentenceIndex,sentences.length-1));
  document.querySelector('.reading').classList.toggle('reading-browse',readingModeState!=='normal');
  document.querySelector('.reading').classList.toggle('reading-revisit',readingModeState==='revisit');
  const done=sentenceIndex>=sentences.length;$('readingDone').classList.toggle('hidden',!done);document.querySelector('.stage-foot').classList.toggle('hidden',done);$('knowledgeDetail').innerHTML='';$('readingPause').innerHTML='';
  $('sentenceCount').textContent=done?`Read ${sentences.length} sentences`:`Sentence ${sentenceIndex+1} / ${sentences.length}`;const percent=sentences.length?Math.min(100,(sentenceIndex+1)/sentences.length*100):0;$('readProgress').style.width=percent+'%';$('readPercent').textContent=Math.round(percent)+'%';
  document.querySelector('.wordcount').textContent=`${sentences.length} sentences · ${points.length} expressions`;
  renderSentenceStage(done);
  if(done){$('readingDone').innerHTML='<h2>You’ve reached the end.</h2><p>Review the expressions you marked for learning.</p><button class="primary" onclick="finishReading()">Finish reading →</button>';return}
  quoteIndex=sentenceIndex;$('quotedSentence').textContent=sentences[sentenceIndex].de;
  const ids=currentPoints(),p=points[ids[activePointOffset]];
  if(p){$('knowledgeDetail').innerHTML=`<div class="knowledge-pause"><h3 lang="de">${escapeHtml(p.de)}</h3>${readingExpanded?`<div class="explanation" id="readingExplanation">${renderReadingExplanation(p)||renderExplanation(p,true)}</div>`:'<p class="recall-prompt">Do you remember this expression?</p>'}<div class="actions"><button class="softbtn" aria-expanded="${readingExpanded}" onclick="readingExpanded=!readingExpanded;renderReading()">${readingExpanded?'Hide explanation':'See explanation'}</button><button class="primary" onclick="advancePoint()">I remember, continue →</button></div></div>`}
  if(readingModeState==='revisit'&&!revisitKnowledgeOpen)$('knowledgeDetail').replaceChildren();
  $('nextSentence').classList.toggle('hidden',Boolean(p)&&(readingModeState!=='revisit'||revisitKnowledgeOpen));$('nextSentence').textContent=readingModeState==='revisit'?'Continue →':'Next sentence →';$('readerHint').textContent='';
  const previewBack=document.querySelector('.reading .back');if(previewBack)previewBack.textContent='← Preview';
  fitReadingHeight();
}
// Use the same reading budget with or without a knowledge card.
function fitReadingHeight(){
  const pane=document.querySelector('.reading'),history=$('sentenceList').querySelector('.history-window'),slot=$('sentenceList').querySelector('.current-slot');
  if(!pane||!history||!slot||!$('readingView').classList.contains('active'))return;
  if(readingModeState!=='normal'){history.style.maxHeight='none';history.dataset.overflow=false;return}
  const reserved=parseFloat(getComputedStyle(pane).getPropertyValue('--recall-space'));
  const bottom=window.innerHeight-40;
  const stageTop=$('sentenceList').getBoundingClientRect().top;
  const stageHeight=Math.max(0,Math.min(310,bottom-stageTop-reserved))*4/3;
  history.style.maxHeight=Math.max(0,stageHeight-slot.getBoundingClientRect().height)+'px';
  history.scrollTop=history.scrollHeight;
  history.dataset.overflow=history.scrollTop>0;
}
window.addEventListener('resize',fitReadingHeight);
function expandReadingHistory(){
  const history=$('sentenceList').querySelector('.history-window');
  if(readingModeState!=='normal'||!history||history.scrollHeight<=history.clientHeight)return;
  const oldScroll=history.scrollTop;
  readingModeState='browse';document.querySelector('.reading').classList.add('reading-browse');fitReadingHeight();
  // Keep the visible text anchored while revealing the rest of the article.
  window.scrollBy({top:oldScroll,behavior:'instant'});
}
document.querySelector('.reading').addEventListener('wheel',event=>{if(event.deltaY<0)expandReadingHistory()},{passive:true});
document.querySelector('.reading').addEventListener('keydown',event=>{if(['ArrowUp','PageUp','Home'].includes(event.key))expandReadingHistory()});
let readingTouchY=0;
document.querySelector('.reading').addEventListener('touchstart',event=>{readingTouchY=event.touches[0].clientY},{passive:true});
document.querySelector('.reading').addEventListener('touchmove',event=>{if(event.touches[0].clientY>readingTouchY)expandReadingHistory()},{passive:true});
function renderSentenceStage(done){
  const list=$('sentenceList');
  if(!list.querySelector('.history-window'))list.innerHTML='<div class="history-window" tabindex="0" aria-label="Previously read sentences"><div class="history-content"></div></div><div class="current-slot"></div>';
  const history=list.querySelector('.history-content'),windowEl=list.querySelector('.history-window'),slot=list.querySelector('.current-slot');
  const changed=renderedSentenceIndex!==sentenceIndex,forward=changed&&renderedSentenceIndex>=0&&sentenceIndex===renderedSentenceIndex+1&&!done;
  const oldCard=forward?slot.querySelector('.sentence.current')?.cloneNode(true):null;
  const oldSlotTop=slot.getBoundingClientRect().top,oldScrollTop=windowEl.scrollTop;
  readingAnimations.forEach(a=>a.cancel());readingAnimations=[];slot.querySelectorAll('.outgoing').forEach(e=>e.remove());
  const previousCount=Math.min(sentenceIndex,sentences.length-1);
  for(const child of [...history.children])if(Number(child.dataset.sentenceIndex)>=previousCount)child.remove();
  for(let i=0;i<previousCount;i++){
    let row=history.querySelector(`[data-sentence-index="${i}"]`);
    if(!row){row=document.createElement('button');row.className='sentence past';row.type='button';row.dataset.sentenceIndex=i;row.lang='de';row.title='Read this sentence again';row.onclick=()=>revisitSentence(i);row.textContent=sentences[i].de;history.appendChild(row)}
  }
  let card=slot.querySelector('.sentence.current');
  if(done){renderedSentenceIndex=sentenceIndex;return}
  if(!card||changed){card=document.createElement('div');card.className='sentence current';card.dataset.sentenceIndex=sentenceIndex;slot.replaceChildren(card)}
  const s=sentences[sentenceIndex];card.innerHTML=`<div lang="de">${pointMarkup(s,sentenceIndex)}</div><div class="sentence-tools"><button class="iconbtn" onclick="speakCurrent()" aria-label="Read sentence aloud"><img src="/assets/analyze-text/speaker.svg" width="18" height="18" alt=""></button><button class="softbtn small" onclick="toggleTranslation()">${translated?'Hide translation':'Translate'}</button></div>${translated?`<div class="sentence-translation">${escapeHtml(s.zh||'No translation returned for this sentence.')}</div>`:''}`;
  let following=list.querySelector('.following-sentences');
  if(!following){following=document.createElement('div');following.className='following-sentences';list.appendChild(following)}
  following.replaceChildren();
  if(readingModeState==='revisit')for(let i=sentenceIndex+1;i<=furthestSentenceIndex;i++){
    const row=document.createElement('button');row.type='button';row.className='sentence past';row.dataset.sentenceIndex=i;row.lang='de';row.textContent=sentences[i].de;row.onclick=()=>revisitSentence(i);following.appendChild(row);
  }
  if(changed&&!done)windowEl.scrollTop=windowEl.scrollHeight;
  windowEl.dataset.overflow=windowEl.scrollHeight>windowEl.clientHeight&&windowEl.scrollTop>0;
  if(forward&&!reduceMotion()){
    const timing={duration:READING_MOTION.duration,easing:READING_MOTION.easing,fill:'none'};
    const slotGrowth=slot.getBoundingClientRect().top-oldSlotTop;
    // While the history grows, the previous sentence already remains in place.
    // Only cross-fade the old card once the history viewport starts scrolling.
    if(oldCard&&slotGrowth<1){oldCard.classList.add('outgoing');oldCard.setAttribute('aria-hidden','true');oldCard.inert=true;slot.appendChild(oldCard);const exit=oldCard.animate([{transform:'translateY(0)'},{transform:'translateY(-44px)'}],timing);exit.finished.then(()=>oldCard.remove()).catch(()=>oldCard.remove());readingAnimations.push(exit,oldCard.animate([{opacity:1},{opacity:0}],{duration:300,easing:'cubic-bezier(0.16,1,0.3,1)',fill:'forwards'}))}
    readingAnimations.push(card.animate([{opacity:0},{opacity:1}],{duration:300,easing:'cubic-bezier(0.16,1,0.3,1)'}));
    readingAnimations.push(card.animate([{transform:'translateY(44px)'},{transform:'translateY(0)'}],timing));
    const scrollDistance=windowEl.scrollTop-oldScrollTop;
    if(scrollDistance>0)readingAnimations.push(history.animate([{transform:`translateY(${scrollDistance}px)`},{transform:'translateY(0)'}],timing));
    readingTransition=true;Promise.allSettled(readingAnimations.map(a=>a.finished)).then(()=>{readingTransition=false});
  }
  renderedSentenceIndex=sentenceIndex;
}
function revisitSentence(index){if(readingTransition)return;if(readingModeState!=='revisit')readingReturnState={sentenceIndex,activePointOffset,translated,readingExpanded};revisitKnowledgeOpen=false;readingModeState='revisit';sentenceIndex=index;activePointOffset=0;translated=false;readingExpanded=false;renderReading();requestAnimationFrame(()=>{const card=$('sentenceList').querySelector('.current-slot');card.scrollIntoView({block:'nearest',behavior:reduceMotion()?'instant':'smooth'})})}
function advancePoint(){if(readingModeState==='revisit'){advanceSentence();return}if(activePointOffset<currentPoints().length-1){activePointOffset++;readingExpanded=false;renderReading()}else advanceSentence()}
function advanceSentence(){if(readingTransition||sentenceIndex>=sentences.length)return;if(readingModeState==='revisit'){const saved=readingReturnState;sentenceIndex=saved?.sentenceIndex??furthestSentenceIndex;activePointOffset=saved?.activePointOffset??0;readingExpanded=saved?.readingExpanded??false;translated=saved?.translated??false;readingReturnState=null;revisitKnowledgeOpen=false}else{sentenceIndex=furthestSentenceIndex+1;activePointOffset=0;readingExpanded=false;translated=false}readingModeState='normal';window.scrollTo({top:0,behavior:'instant'});renderReading()}
function startReading(){renderedSentenceIndex=-1;furthestSentenceIndex=0;readingModeState='normal';$('sentenceList').replaceChildren();sentenceIndex=0;activePointOffset=0;translated=false;readingExpanded=false;learningIds=points.filter(p=>!known.has(p.id)).map(p=>p.id);showView('readingView')}
function renderQuiz(){
  if(!document.querySelector('#quizView h1')){const heading=document.createElement('h1');heading.textContent='Recall the expressions you just met';document.querySelector('#quizView .stage-label').after(heading)}
  const host=$('quizList'),button=$('quizSubmit');button.classList.remove('hidden');button.disabled=false;
  if(quizPhase==='loading'){host.innerHTML='<div class="stage-empty"><div class="spinner"></div><h2>Preparing your review…</h2><p>Creating questions from the expressions marked for learning.</p></div>';button.textContent='Creating questions…';button.disabled=true;return}
  if(quizPhase==='error'){host.innerHTML=`<div class="stage-empty"><h2>Your review is not ready yet</h2><p>${escapeHtml(quizError)}</p><p>Your reading progress is still here.</p></div>`;button.textContent='Try again';button.onclick=requestReviewQuiz;return}
  if(!reviewQuestions.length){host.innerHTML='<div class="stage-empty"><h2>No expressions to review this time</h2><p>Everything was marked as already known.</p></div>';button.textContent='Finish session';button.onclick=finishSession;return}
  const q=currentQuizQuestion();if(!q){renderCompletion();showView('doneView');return}
  const confirmed=confirmedAnswers.has(q.question_id),selected=answers[q.question_id],isReview=quizPhase==='mistakeReview',point=points.find(p=>q.related_knowledge_point_ids.includes(p.id)),context=sentences.find(s=>point?.sentenceIds.includes(s.id))?.de||'';
  host.innerHTML=`<article class="qcard"><div class="quiz-progress" aria-label="${isReview?'Mistake review':'Question'} progress"><span class="question-meta">${isReview?reviewQueueIndex+1:quizIndex+1} / ${isReview?reviewQueue.length:reviewQuestions.length}</span><div class="progress"><i style="width:${(isReview?reviewQueueIndex+1:quizIndex+1)/(isReview?reviewQueue.length:reviewQuestions.length)*100}%"></i></div></div><h2>${reviewQuestionMarkup(reviewQuestionStem(q,point,context),point)}</h2>${context?`<div class="example-box" lang="de">${reviewContextMarkup(context,point)}</div>`:''}<div class="quiz-options" role="group" aria-label="Answer options">${q.options.map((option,index)=>`<button class="answer ${selected===index?'selected':''} ${confirmed&&index===q.correct_answer?'correct':''} ${confirmed&&selected===index&&selected!==q.correct_answer?'wrong':''}" aria-pressed="${selected===index}" ${confirmed?'disabled':''} onclick="chooseAnswer(${index})">${String.fromCharCode(65+index)}. &nbsp;${escapeHtml(option)}</button>`).join('')}</div></article>${confirmed?`<div class="quiz-feedback ${selected===q.correct_answer?'':'wrong'}" role="status"><strong>${selected===q.correct_answer?'Correct answer':'Incorrect · Correct answer: '+String.fromCharCode(65+q.correct_answer)}</strong><p>${escapeHtml(q.explanation)}</p></div>`:''}`;
  button.textContent=confirmed?(isReview?'Continue →':quizIndex===reviewQuestions.length-1?'View results →':'Next question →'):'Confirm answer';button.disabled=!confirmed&&selected===undefined;button.onclick=confirmed?continueQuiz:submitQuiz;
}
function chooseAnswer(index){const q=currentQuizQuestion();if(!q||confirmedAnswers.has(q.question_id))return;answers[q.question_id]=index;renderQuiz()}
function reviewUiLanguage(){return localStorage.getItem('ui_language')==='en'?'English':'Chinese'}
function reviewQuestionStem(question,point,context){
  if(point&&['vocabulary_in_context','expression_usage'].includes(question.question_type))return reviewUiLanguage()==='English'?`What does “${point.de}” mean in this sentence?`:`“${point.de}”在这句话中是什么意思？`;
  return String(question.question).replace(context||'\u0000','').replace(/[：:]\s*$/,'').trim();
}
function reviewQuestionMarkup(text,point){
  const label=String(point?.de||'');
  if(label&&String(text).includes(label)){const chunks=String(text).split(label);return chunks.map(escapeHtml).join(`<strong>${escapeHtml(label)}</strong>`)}
  return String(text).split(/(“[^”]+”|„[^“]+“|"[^"]+"|'[^']+'|「[^」]+」)/g).map((part,index)=>index%2?`<strong>${escapeHtml(part)}</strong>`:escapeHtml(part)).join('');
}
function reviewContextMarkup(text,point){
  const sentence=sentences.find(s=>s.de===text),spans=(point?.spans||[]).filter(s=>s.sentenceId===sentence?.id).sort((a,b)=>a.start-b.start);
  let result='',cursor=0;
  for(const span of spans){if(span.start<cursor||span.end>text.length)continue;result+=escapeHtml(text.slice(cursor,span.start))+`<strong>${escapeHtml(text.slice(span.start,span.end))}</strong>`;cursor=span.end}
  if(!spans.length&&point?.de){const label=String(point.de).replace(/^(?:der|die|das)\s+/i,'');if(text.includes(label))return text.split(label).map(escapeHtml).join(`<strong>${escapeHtml(label)}</strong>`)}
  return result+escapeHtml(text.slice(cursor));
}
function submitQuiz(){const q=currentQuizQuestion();if(!q||answers[q.question_id]===undefined)return;confirmedAnswers.add(q.question_id);renderQuiz()}
function reviewMistakes(){reviewQueue=reviewQuestions.map((q,i)=>answers[q.question_id]!==q.correct_answer?i:-1).filter(i=>i>=0);if(!reviewQueue.length)return;reviewOriginalAnswers={...answers};reviewQueue.forEach(i=>confirmedAnswers.delete(reviewQuestions[i].question_id));reviewQueueIndex=0;quizPhase='mistakeReview';showView('quizView')}
function renderCompletion(message=''){
  if(!document.querySelector('.done-result')){const result=document.createElement('div');result.className='done-result';document.querySelector('.done').appendChild(result);result.append($('quizSummary'),$('mistakeList'),document.querySelector('.completion-actions'))}
  const scoreAnswers=reviewOriginalAnswers||answers,total=reviewQuestions.length,correct=reviewQuestions.filter(q=>scoreAnswers[q.question_id]===q.correct_answer).length,wrong=reviewQuestions.filter(q=>scoreAnswers[q.question_id]!==q.correct_answer);
  $('doneTitle').textContent='Session complete.';$('doneSummary').textContent=message||`You read ${sentences.length} sentences and reviewed ${total} expression${total===1?'':'s'}.`;
  $('quizSummary').innerHTML=`<div class="score">${total?`${correct} / ${total} correct · ${Math.round(correct/total*100)}%`:'Reading complete'}</div><p>${wrong.length?`${wrong.length} expression${wrong.length>1?'s':''} to revisit`:'All done. Well done.'}</p>`;
  $('mistakeList').innerHTML=wrong.map(q=>`<div class="mistake-item"><h3>${escapeHtml(q.question)}</h3><p>Your answer: ${escapeHtml(q.options[scoreAnswers[q.question_id]]||'Not answered')}</p><p>Correct answer: ${escapeHtml(q.options[q.correct_answer])}</p><p>${escapeHtml(q.explanation)}</p></div>`).join('');$('reviewMistakesButton').classList.toggle('hidden',!wrong.length);$('reviewMistakesButton').textContent='Review mistakes';$('finishSessionButton').textContent='Finish session';
}
async function openSavedArticle(id){try{const data=await readingRequest(`/articles/${id}`);if(data.status!=='completed')throw new Error(data.status==='failed'?'Analysis failed. Please import this article again.':'This article is still processing. Try again shortly.');mapAnalysisToUi(data);articleText=data.raw_text;persistedArticleId=data.text_id;isDemo=false;$('demoBadge').classList.add('hidden');resetLearning();$('levelSelect').value=data.level||'B1';document.querySelector('.title').textContent=data.title;history.replaceState(null,'',data.text_id?`?text_id=${data.text_id}`:location.pathname);showView('prepView')}catch(e){toast(e.message)}}
async function showLibrary(){showView('libraryView');$('libraryContent').innerHTML='<p>Loading your library…</p>';try{const data=await readingRequest('/articles');libraryRows=data.articles||[];filterLibrary('private')}catch(e){$('libraryContent').innerHTML=`<div class="stage-empty"><h2>Sign in to view your library</h2><p>${escapeHtml(e.message)}</p><a class="softbtn" href="/?page=article">Open Main Assistant to sign in ↗</a><button class="back" onclick="loadDemo()">Try the sample flow</button></div>`}}
function loadLibrary(){return showLibrary()}
function finishSession(){
  if('speechSynthesis' in window)speechSynthesis.cancel();
  persistedArticleId=null;savedReview=null;articleText='';points=[];sentences=[];isDemo=false;resetLearning();
  importedText='';importedTitle='';analysisRequestKey=null;analysisRequestSignature=null;
  $('demoBadge').classList.add('hidden');$('customText').value='';updateCount();
  history.replaceState(null,'',location.pathname);showView('sourceView');toast('Session finished. Your saved articles remain in your library.');
}
function saveProgress(point,status){if(isDemo)return;return saveLiveProgress(point,status)}
function startReviewGeneration(){if(!isDemo)return generateLiveReview();reviewGenerationPromise=Promise.resolve(demoQuestions);return reviewGenerationPromise}
function loadDemo(){
  isDemo=true;persistedArticleId=null;history.replaceState(null,'',location.pathname+'?sample=1');$('demoBadge').classList.remove('hidden');articleText='Die Berliner Mauer war das Symbol der Teilung Deutschlands. Sie trennte Familien und Freunde über Jahrzehnte hinweg. Heute erinnert ein Denkmal an diese Zeit.';
  sentences=[{id:1,de:'Die Berliner Mauer war das Symbol der Teilung Deutschlands.',zh:'柏林墙曾是德国分裂的象征。',points:[0]},{id:2,de:'Sie trennte Familien und Freunde über Jahrzehnte hinweg.',zh:'它将亲人与朋友分隔了数十年。',points:[1]},{id:3,de:'Heute erinnert ein Denkmal an diese Zeit.',zh:'今天，一座纪念碑让人们想起这段岁月。',points:[]}];
  points=[{id:'demo-vocab',type:'重点词汇',de:'die Teilung',meaning:'分裂；划分。这里指德国的分裂。',simpleExample:'Die Teilung Deutschlands dauerte viele Jahre.',sentenceIds:[1],spans:[]},{id:'demo-grammar',type:'语法重点',de:'über … hinweg',meaning:'表示一段时间的持续：长达……，跨越……。',simpleExample:'Sie blieben über Jahre hinweg Freunde.',translation:'他们多年来一直是朋友。',sentenceIds:[2],spans:[],exampleHighlights:['über','hinweg']}];
  points.forEach((p,i)=>{const text=sentences[i].de,term=i===0?'Teilung':'über Jahrzehnte hinweg',start=text.indexOf(term);p.spans=[{sentenceId:i+1,start,end:start+term.length}]});resetLearning();document.querySelector('.title').textContent='Die Berliner Mauer: Geschichte';showView('prepView');
}
const demoQuestions=[{question_id:'demo-q1',question_type:'vocabulary_in_context',question:'What does “Teilung” mean in this sentence?',options:['Reunification','Division','A political decision','A long border'],correct_answer:1,explanation:'Teilung means division. Here it refers to the division of Germany.',related_knowledge_point_ids:['demo-vocab']},{question_id:'demo-q2',question_type:'grammar_understanding',question:'What does “über Jahrzehnte hinweg” express?',options:['Before one decade','For a few days','Over several decades','Within one moment'],correct_answer:2,explanation:'Über … hinweg expresses duration across a period of time.',related_knowledge_point_ids:['demo-grammar']}];
// Standalone entry initialization. Authentication is shared only through the existing token.
const readingHeader=document.createElement('div');readingHeader.className='reading-fixed-header';
document.querySelector('.reading').prepend(readingHeader);
readingHeader.append(document.querySelector('.reading>.stage-label'),document.querySelector('.reading>.title'),document.querySelector('.reading>.progress-row'));
const entryParams=new URLSearchParams(location.search);if(entryParams.get('text_id'))openSavedArticle(Number(entryParams.get('text_id')));else if(entryParams.has('sample'))loadDemo();




let librarySource='public',libraryLevel='All';
function filterLibrary(source){librarySource=source;libraryLevel='All';renderLibrary()}
function setLibraryLevel(level){libraryLevel=level;renderLibrary()}
function renderLibrary(){
 const sourceRows=libraryRows.filter(a=>librarySource==='public'?a.visibility==='public':a.visibility!=='public');
 const rows=sourceRows.filter(a=>libraryLevel==='All'||a.level===libraryLevel);
 $('libraryCount').textContent=`${sourceRows.length} articles · German`;
 document.querySelectorAll('.library-tabs button').forEach((b,i)=>b.setAttribute('aria-selected',String((i===0)===(librarySource==='public'))));
 $('libraryFilters').innerHTML=librarySource==='public'?`<div class="library-filter"><span>Difficulty</span>${['All','A1','A2','B1','B2','C1','C2'].map(l=>`<button aria-pressed="${l===libraryLevel}" onclick="setLibraryLevel('${l}')">${l}</button>`).join('')}</div>`:'';
 $('libraryContent').innerHTML=rows.length?rows.map(a=>`<button class="library-card" onclick="openSavedArticle(${Number(a.text_id)})"><h2>${escapeHtml(a.title)}</h2><div class="library-meta"><span class="library-badge">${escapeHtml(a.level||'German')}</span><span>${Number(a.word_count)||0} words${a.status!=='completed'?' · '+escapeHtml(a.status):''}</span></div><p>${escapeHtml(a.preview||'')}</p><span class="library-read">Read →</span></button>`).join(''):'<div class="stage-empty"><h2>No articles here yet</h2><p>Add an article to start reading.</p><button class="primary" onclick="showView(\'sourceView\')">Add Article</button></div>';
}

let knowledgeRows=[];
async function showKnowledge(){showView('knowledgeView');$('knowledgeGrid').textContent='Loading knowledge…';try{const data=await readingRequest('/knowledge-points');knowledgeRows=data.knowledge_points||[];renderKnowledge()}catch(e){$('knowledgeStats').textContent='';$('knowledgeGrid').textContent=e.message}}
function knowledgeLabel(p){return String(p.payload.vocab_body||p.payload.display_name||'Knowledge point')}
function renderKnowledge(){const kind=$('knowledgeKind').value,status=$('knowledgeStatus').value,q=$('knowledgeSearch').value.trim().toLocaleLowerCase();const all=knowledgeRows.filter(p=>!kind||p.kind===kind);let rows=all.filter(p=>(!status||p.status===status)&&(!q||(knowledgeLabel(p)+' '+String(p.payload.explanation||'')).toLocaleLowerCase().includes(q)));if($('knowledgeSort').value==='difficulty'){const rank={not_mastered:0,learning:1,mastered:2};rows.sort((a,b)=>rank[a.status]-rank[b.status])}const mastered=all.filter(p=>p.status==='mastered').length,percent=all.length?Math.round(mastered/all.length*100):0;$('knowledgeStats').innerHTML=`<strong>${all.length} knowledge points</strong><span>·</span><span>${mastered} mastered</span><span>·</span><span>${all.length-mastered} to review</span><div class="progress"><i style="width:${percent}%"></i></div><span>${percent}%</span>`;$('knowledgeGrid').innerHTML=rows.length?rows.map(p=>`<button class="knowledge-card" onclick="openKnowledge(${p.id})"><strong>${escapeHtml(knowledgeLabel(p))}</strong><p>${escapeHtml(String(p.payload.explanation||''))}</p><small class="${p.status}">● ${p.status==='mastered'?'Mastered':p.status==='learning'?'Learning':'Not mastered'}</small></button>`).join(''):'<p>No knowledge points found. Analyze an article while signed in to save knowledge here.</p>'}
function openKnowledge(id){const p=knowledgeRows.find(p=>p.id===id);if(!p)return;$('knowledgeDetails').innerHTML=`<h2>${escapeHtml(knowledgeLabel(p))}</h2>${knowledgeExplanationDetails(p.payload)}<p>From: ${escapeHtml(p.title)}</p><label>Mastery <select onchange="updateKnowledge(${p.id},this.value)">${['not_mastered','learning','mastered'].map(s=>`<option value="${s}" ${p.status===s?'selected':''}>${s.replaceAll('_',' ')}</option>`).join('')}</select></label><button class="softbtn" onclick="document.getElementById('knowledgeDialog').close();openSavedArticle(${p.text_id})">Open article →</button>`;$('knowledgeDialog').showModal()}
async function updateKnowledge(id,status){try{await readingRequest(`/knowledge-points/${id}/progress`,{method:'PUT',body:JSON.stringify({status})});knowledgeRows.find(p=>p.id===id).status=status;const point=points.find(p=>p.persistedId===id);if(point)point.learnStatus=status;renderKnowledge();toast('Mastery saved')}catch(e){toast(e.message);$('knowledgeDialog').close()}}


function knowledgeExplanationDetails(payload){
 const explanation=String(payload.explanation||'').trim();
 const contexts=(payload.examples||[]).map(example=>({sentence:String(example.sentence_body||''),text:String(example.context_explanation||example.explanation_context||'').trim()})).filter(item=>item.text);
 const direct=String(payload.context_explanation||payload.explanation_context||'').trim();
 if(direct&&!contexts.some(item=>item.text===direct))contexts.unshift({sentence:'',text:direct});
 return `<section class="knowledge-explanation"><h3>Explanation</h3><p>${escapeHtml(explanation||'No explanation available.')}</p></section><section class="knowledge-explanation"><h3>Context explanation</h3>${contexts.length?contexts.map(item=>`<div>${item.sentence?`<blockquote lang="de">${escapeHtml(item.sentence)}</blockquote>`:''}<p>${escapeHtml(item.text)}</p></div>`).join(''):'<p>No context explanation available.</p>'}</section>`;
}
