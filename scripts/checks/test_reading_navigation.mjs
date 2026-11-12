import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const source = readFileSync(new URL('../../frontend/my-web-ui/public/analyze-text/flow.js', import.meta.url), 'utf8');
const functions = ['revisitSentence', 'advancePoint', 'advanceSentence'].map(name => {
  const line = source.split(/\r?\n/).find(line => line.startsWith(`function ${name}(`));
  assert.ok(line, `${name} is defined`);
  return line;
}).join('\n');
const context = vm.createContext({ assert });
vm.runInContext(`
  let sentenceIndex=5, furthestSentenceIndex=5, activePointOffset=2;
  let readingExpanded=true, translated=true, readingModeState='normal';
  let readingReturnState=null, revisitKnowledgeOpen=false, readingTransition=false;
  const sentences=Array(10), window={scrollTo(){}}, requestAnimationFrame=()=>{};
  function renderReading(){furthestSentenceIndex=Math.max(furthestSentenceIndex,sentenceIndex)}
  function currentPoints(){return [0,1,2]}
  ${functions}
  revisitSentence(2);
  revisitSentence(1);
  advancePoint();
  assert.equal(sentenceIndex,5,'Continue returns to the original current sentence');
  assert.equal(activePointOffset,2,'Knowledge point position is restored');
  assert.equal(readingExpanded,true,'Explanation state is restored');
  assert.equal(translated,true,'Translation state is restored');
  assert.equal(readingModeState,'normal');
  assert.equal(furthestSentenceIndex,5,'Review does not reveal a new sentence');
  advanceSentence();
  assert.equal(sentenceIndex,6,'Normal advancement still reveals the next sentence');
  revisitSentence(0);
  advanceSentence();
  assert.equal(sentenceIndex,6,'Sentence-level Continue also returns to current');
`, context);
console.log('Reading navigation checks passed');
