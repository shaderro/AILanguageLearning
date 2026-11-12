import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
const source=readFileSync(new URL('../../frontend/my-web-ui/public/analyze-text/flow.js',import.meta.url),'utf8');
const helpers=source.slice(source.indexOf('function reviewUiLanguage()'),source.indexOf('function submitQuiz()'));
const sandbox=vm.createContext({assert});
vm.runInContext(`
let language='en';
const localStorage={getItem:()=>language};
const escapeHtml=text=>String(text).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
const sentences=[{id:1,de:'Die Teilung Deutschlands.'}];
${helpers}
const point={de:'die Teilung',spans:[{sentenceId:1,start:4,end:11}]};
const question={question_type:'vocabulary_in_context',question:'Was bedeutet Teilung? Die Teilung Deutschlands.'};
const stem=reviewQuestionStem(question,point,sentences[0].de);
assert.equal(stem,'What does “die Teilung” mean in this sentence?');
assert.ok(!stem.includes('Deutschlands'));
assert.ok(reviewQuestionMarkup(stem,point).includes('<strong>die Teilung</strong>'));
assert.equal(reviewContextMarkup(sentences[0].de,point),'Die <strong>Teilung</strong> Deutschlands.');
language='zh';
assert.equal(reviewQuestionStem(question,point,sentences[0].de),'“die Teilung”在这句话中是什么意思？');
assert.equal(reviewQuestionMarkup('<script>',{de:'<script>'}),'<strong>&lt;script&gt;</strong>');
`,sandbox);
console.log('Review formatting checks passed');
