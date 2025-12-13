import { BaseButtonDemo } from '../components/base/BaseButton.demo';
import { BaseCardDemo } from '../components/base/BaseCard.demo';
import { BaseBadgeDemo } from '../components/base/BaseBadge.demo';
import { BaseModalDemo } from '../components/base/BaseModal.demo';
import { BaseInputDemo } from '../components/base/BaseInput.demo';
import { BaseSpinnerDemo } from '../components/base/BaseSpinner.demo';
import { ConfirmDialogDemo } from '../components/base/ConfirmDialog.demo';
import { LoadingOverlayDemo } from '../components/base/LoadingOverlay.demo';
import { ArticlePreviewCard } from '../components/features/article/ArticlePreviewCard';
import VocabReviewCard from '../components/features/review/VocabReviewCard';
import GrammarReviewCard from '../components/features/review/GrammarReviewCard';
import VocabDetailCard from '../components/features/vocab/VocabDetailCard';
import GrammarDetailCard from '../components/features/grammar/GrammarDetailCard';
import VocabNotationCard from '../modules/article/components/notation/VocabNotationCard';
import ToastNotice from '../modules/article/components/ToastNotice';
import ArticleViewer from '../modules/article/components/ArticleViewer';
import { NotationContext } from '../modules/article/contexts/NotationContext';
import { SelectionProvider } from '../modules/article/selection/SelectionContext';
import TokenInlineTranslationDemo from '../components/features/translation/TokenInlineTranslation.demo';
import { TranslationDebugProvider } from '../contexts/TranslationDebugContext';
import { tokens } from '../design-tokens';
import { useState, useRef } from 'react';

const demoSections = [
  {
    title: 'BaseButton',
    description: '统一按钮样式，支持 variant/size/fullWidth/loading。',
    component: BaseButtonDemo,
  },
  {
    title: 'BaseCard',
    description: '增强卡片结构，内置 header/footer/actions 与交互态。',
    component: BaseCardDemo,
  },
  {
    title: 'BaseBadge',
    description: '语义标签组件，适配状态/语言/难度等场景。',
    component: BaseBadgeDemo,
  },
  {
    title: 'BaseModal',
    description: '模态框容器，支持标题、描述、footer 按钮。',
    component: BaseModalDemo,
  },
  {
    title: 'BaseInput',
    description: '统一输入框样式，支持 label/helper/error/prefix/suffix。',
    component: BaseInputDemo,
  },
  {
    title: 'BaseSpinner',
    description: '加载指示器，可配置尺寸与语义色。',
    component: BaseSpinnerDemo,
  },
  {
    title: 'ConfirmDialog',
    description: '基于 BaseModal 的确认操作模态框，附带 meta 信息展示。',
    component: ConfirmDialogDemo,
  },
  {
    title: 'LoadingOverlay',
    description: '局部或全屏的加载遮罩，可搭配 BaseSpinner。',
    component: LoadingOverlayDemo,
  },
];

const functionSections = [
  {
    title: 'ArticlePreviewCard',
    description: '文章列表中的预览卡片，基于 BaseCard + BaseButton 实现。',
    component: function ArticlePreviewCardDemo() {
      return (
        <ArticlePreviewCard
          title="Some Name Of An Article which is too long to display"
          wordCount="1500"
          noteCount="5"
          preview="This is a two-line preview sentence of this article. If it's too long, it will only display the first two line... Check it out!"
          onEdit={() => {}}
          onDelete={() => {}}
          onRead={() => {}}
        />
      );
    },
  },
  {
    title: 'VocabReviewCard',
    description: '词汇复习卡片，用于词汇学习和复习场景，支持显示释义、例句导航和复习反馈。',
    component: function VocabReviewCardDemo() {
      return (
        <VocabReviewCard
          vocab={{
            vocab_id: 1,
            vocab_body: 'vertreten',
            explanation: '表示伸展、活动 (肢体)；代表、代理 (某人或某组织)；坚持、维护 (观点或立场)；扭伤、挫伤 (肢体)',
            examples: [
              {
                original_sentence: 'Er vertritt die Ansicht, dass...',
                context_explanation: '在这个句子中，vertreten 表示"代表、坚持"某个观点。'
              },
              {
                original_sentence: 'Ich muss mir die Beine vertreten.',
                context_explanation: '这里 vertreten 表示"伸展、活动"腿脚的意思。'
              }
            ]
          }}
          currentProgress={2}
          totalProgress={3}
          onClose={() => console.log('关闭')}
          onPrevious={() => console.log('上一个')}
          onNext={() => console.log('下一个')}
          onDontKnow={() => console.log('不认识')}
          onKnow={() => console.log('认识')}
        />
      );
    },
  },
  {
    title: 'GrammarReviewCard',
    description: '语法复习卡片，用于语法规则学习和复习场景，支持显示释义、例句导航和复习反馈。',
    component: function GrammarReviewCardDemo() {
      return (
        <GrammarReviewCard
          grammar={{
            rule_id: 1,
            rule_name: '现在完成时',
            rule_summary: '现在完成时表示过去发生的动作对现在造成的影响或结果，或者表示从过去开始一直持续到现在的动作或状态。结构：have/has + 过去分词。',
            examples: [
              {
                original_sentence: 'I have finished my homework.',
                context_explanation: '这个句子使用现在完成时，表示"完成作业"这个动作已经完成，对现在的影响是作业已经做完了。'
              },
              {
                original_sentence: 'She has lived in Beijing for five years.',
                context_explanation: '这里使用现在完成时，表示"居住"这个动作从过去开始一直持续到现在，已经持续了五年。'
              }
            ]
          }}
          currentProgress={2}
          totalProgress={3}
          onClose={() => console.log('关闭')}
          onPrevious={() => console.log('上一个')}
          onNext={() => console.log('下一个')}
          onDontKnow={() => console.log('不认识')}
          onKnow={() => console.log('认识')}
        />
      );
    },
  },
  {
    title: 'VocabDetailCard',
    description: '词汇详情卡片，用于展示词汇的完整信息，包括释义、语法说明和例句，支持上一个/下一个导航。',
    component: function VocabDetailCardDemo() {
      const [currentIndex, setCurrentIndex] = useState(0);
      
      const vocabList = [
        {
          vocab_id: 1,
          vocab_body: 'erstrecken',
          part_of_speech: '动词',
          explanation: '1. 延伸, 伸展 (指空间上的扩展)\n2. 持续, 延续 (指时间上的跨度)',
          grammar_notes: 'sich erstrecken — 延伸, 扩展 (反身动词用法)\nerstrecken über + Akk. — 延伸覆盖某区域',
          examples: [
            {
              original_sentence: 'Der Wald erstreckt sich über mehrere Kilometer.',
              context_explanation: '森林绵延数公里。这里使用反身形式 \'sich erstrecken\' 表示空间上的延伸。',
              text_title: '德国地理',
              source: 'qa'
            },
            {
              original_sentence: 'Die Verhandlungen erstreckten sich über mehrere Monate.',
              context_explanation: '谈判持续了数月。这里 erstrecken 表示时间上的延续。',
              text_title: '商务德语',
              source: 'qa'
            },
            {
              original_sentence: 'Das Gebirge erstreckt sich von Norden nach Süden.',
              context_explanation: '山脉从北向南延伸。这里表示地理空间上的扩展。',
              text_title: '地理知识',
              source: 'qa'
            }
          ],
          source: 'qa'
        },
        {
          vocab_id: 2,
          vocab_body: 'vertreten',
          part_of_speech: '动词',
          explanation: '1. 表示伸展、活动 (肢体)\n2. 代表、代理 (某人或某组织)\n3. 坚持、维护 (观点或立场)\n4. 扭伤、挫伤 (肢体)',
          examples: [
            {
              original_sentence: 'Er vertritt die Ansicht, dass...',
              context_explanation: '在这个句子中，vertreten 表示"代表、坚持"某个观点。'
            },
            {
              original_sentence: 'Ich muss mir die Beine vertreten.',
              context_explanation: '这里 vertreten 表示"伸展、活动"腿脚的意思。'
            }
          ],
          source: 'qa'
        }
      ];

      const handlePrevious = () => {
        if (currentIndex > 0) {
          setCurrentIndex(currentIndex - 1);
        }
      };

      const handleNext = () => {
        if (currentIndex < vocabList.length - 1) {
          setCurrentIndex(currentIndex + 1);
        }
      };

      return (
        <VocabDetailCard
          vocab={vocabList[currentIndex]}
          onPrevious={currentIndex > 0 ? handlePrevious : null}
          onNext={currentIndex < vocabList.length - 1 ? handleNext : null}
          currentIndex={currentIndex}
          totalCount={vocabList.length}
        />
      );
    },
  },
  {
    title: 'GrammarDetailCard',
    description: '语法详情卡片，用于展示语法规则的完整信息，包括规则说明和例句，支持上一个/下一个导航。',
    component: function GrammarDetailCardDemo() {
      const [currentIndex, setCurrentIndex] = useState(0);
      
      const grammarList = [
        {
          rule_id: 1,
          rule_name: '现在完成时',
          rule_summary: '现在完成时表示过去发生的动作对现在造成的影响或结果，或者表示从过去开始一直持续到现在的动作或状态。\n结构：have/has + 过去分词。\n常用于表示经验、完成、持续等含义。',
          examples: [
            {
              original_sentence: 'I have finished my homework.',
              context_explanation: '这个句子使用现在完成时，表示"完成作业"这个动作已经完成，对现在的影响是作业已经做完了。',
              text_title: '英语语法基础',
              source: 'qa'
            },
            {
              original_sentence: 'She has lived in Beijing for five years.',
              context_explanation: '这里使用现在完成时，表示"居住"这个动作从过去开始一直持续到现在，已经持续了五年。',
              text_title: '英语时态',
              source: 'qa'
            },
            {
              original_sentence: 'We have never been to Japan.',
              context_explanation: '这个句子使用现在完成时表示经验，说明"去日本"这个经历从未发生过。',
              text_title: '英语语法',
              source: 'qa'
            }
          ],
          source: 'qa'
        },
        {
          rule_id: 2,
          rule_name: '被动语态',
          rule_summary: '被动语态表示主语是动作的承受者，而不是执行者。\n结构：be + 过去分词。\n当动作的执行者不重要或不知道时，常用被动语态。',
          examples: [
            {
              original_sentence: 'The book was written by a famous author.',
              context_explanation: '这个句子使用被动语态，强调"书"是被写的对象，而作者是谁虽然提到但不是重点。',
              text_title: '英语语法',
              source: 'qa'
            },
            {
              original_sentence: 'The window was broken yesterday.',
              context_explanation: '这里使用被动语态，因为我们不知道是谁打破了窗户，或者打破窗户的人不重要。',
              text_title: '英语语法',
              source: 'qa'
            }
          ],
          source: 'qa'
        }
      ];

      const handlePrevious = () => {
        if (currentIndex > 0) {
          setCurrentIndex(currentIndex - 1);
        }
      };

      const handleNext = () => {
        if (currentIndex < grammarList.length - 1) {
          setCurrentIndex(currentIndex + 1);
        }
      };

      return (
        <GrammarDetailCard
          grammar={grammarList[currentIndex]}
          onPrevious={currentIndex > 0 ? handlePrevious : null}
          onNext={currentIndex < grammarList.length - 1 ? handleNext : null}
          currentIndex={currentIndex}
          totalCount={grammarList.length}
        />
      );
    },
  },
  {
    title: 'VocabNotationCard',
    description: '内联词汇注释卡片，用于在文章中显示词汇的解释和上下文说明，支持悬停显示。',
    component: function VocabNotationCardDemo() {
      const anchorRef = useRef(null)
      const [isVisible, setIsVisible] = useState(true)
      
      return (
        <div className="relative p-8 bg-gray-100 rounded-lg">
          <div className="mb-4">
            <p className="text-sm text-gray-600 mb-2">悬停在下面的文本上查看词汇注释卡片：</p>
            <span 
              ref={anchorRef}
              className="inline-block px-2 py-1 border-b-2 border-green-500 cursor-pointer hover:bg-green-50 transition-colors"
              onMouseEnter={() => setIsVisible(true)}
              onMouseLeave={() => setIsVisible(false)}
            >
              erstrecken
            </span>
          </div>
          
          <VocabNotationCard
            isVisible={isVisible}
            note="这是一个测试注释"
            textId={1}
            sentenceId={1}
            tokenIndex={0}
            anchorRef={anchorRef}
            getVocabExampleForToken={async (textId, sentenceId, tokenIndex) => {
              // 模拟 API 调用
              return {
                vocab_id: 1,
                context_explanation: '在这个句子中，"erstrecken" 表示"延伸、伸展"的意思，通常用于描述空间上的扩展，如森林延伸数公里。'
              }
            }}
          />
        </div>
      );
    },
  },
  {
    title: 'ToastNotice (知识点提示)',
    description: '在 article chat view 中自动生成 vocab/grammar 后显示的 toast 提示，支持多个 toast 同时显示，每个 toast 自动渐隐消失。',
    component: function ToastNoticeDemo() {
      // 示例消息
      const exampleMessages = [
        '🆕 语法: 现在完成时 知识点已总结并加入列表',
        '🆕 词汇: erstrecken 知识点已总结并加入列表',
        '🆕 语法: 被动语态 知识点已总结并加入列表',
      ];
      
      return (
        <div className="relative min-h-[400px]">
          <div className="mb-6">
            <p className="text-sm text-gray-600 mb-4">
              以下是在 article chat view 中自动生成 vocab/grammar 后显示的 toast 提示 UI：
            </p>
          </div>
          
          {/* Toast 容器 - 相对定位，显示在 demo 区域内 */}
          <div 
            className="relative flex flex-col items-center gap-4"
          >
            {exampleMessages.map((msg, index) => (
              <div key={index} className="relative">
                <ToastNotice
                  message={msg}
                  isVisible={true}
                  duration={999999} // 设置很长的 duration，让它们保持显示
                  onClose={() => {}}
                />
              </div>
            ))}
          </div>
          
          <div className="mt-8 p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600">
              <strong>说明：</strong>
              <br />
              • Toast 使用 success-200 背景色和黑色文字
              <br />
              • 在 article chat view 中，多个 toast 会依次显示，每个间隔 600ms
              <br />
              • 每个 toast 显示 2 秒后自动渐隐消失
              <br />
              • 多个 toast 会垂直堆叠显示，每个间距 64px
            </p>
          </div>
        </div>
      );
    },
  },
  {
    title: 'ArticleViewer (文章阅读视图)',
    description: '文章阅读和交互视图，支持 token 选择、句子选择、词汇解释等功能。这是真实 UI 的完整复制，用于在 UIDemo 中进行修改和测试。',
    component: function ArticleViewerDemo() {
      // 🔧 使用一个测试文章 ID（需要确保后端有这个文章，或者使用模拟数据）
      // 注意：这里使用真实的 ArticleViewer，所以需要真实的 articleId
      // 如果后端没有数据，可以创建一个 mock 版本的 ArticleViewer
      const testArticleId = '1763895389'; // 使用一个存在的文章 ID，或者根据实际情况修改
      
      // 🔧 创建简化的 NotationContext 值（用于 UIDemo）
      const mockNotationContext = {
        // Grammar notations
        grammarNotations: [],
        getGrammarNotationsForSentence: () => [],
        getGrammarRuleById: () => null,
        hasGrammarNotation: () => false,
        isLoadingGrammar: false,
        errorGrammar: null,
        
        // Vocab notations
        vocabNotations: [],
        getVocabNotationsForSentence: () => [],
        getVocabExampleForToken: async () => null,
        hasVocabNotation: () => false,
        isLoadingVocab: false,
        errorVocab: null,
        
        // Cache refresh
        refreshCache: () => {},
        
        // Cache updates
        addGrammarNotationToCache: () => {},
        addVocabNotationToCache: () => {},
        addGrammarRuleToCache: () => {},
        addVocabExampleToCache: () => {},
        
        // Create
        createVocabNotation: async () => ({ success: false }),
      };
      
      return (
        <SelectionProvider>
          <NotationContext.Provider value={mockNotationContext}>
            <div className="w-full">
              <div className="mb-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                <p className="text-sm text-blue-800">
                  <strong>注意：</strong>这是真实的 ArticleViewer 组件，需要有效的 articleId 才能显示内容。
                  <br />
                  当前使用的测试 articleId: <code className="bg-blue-100 px-2 py-1 rounded">{testArticleId}</code>
                  <br />
                  如果文章不存在，请修改 <code className="bg-blue-100 px-2 py-1 rounded">testArticleId</code> 或确保后端有对应的文章数据。
                </p>
              </div>
              
              <div className="border border-gray-300 rounded-lg overflow-hidden" style={{ height: '600px' }}>
                <ArticleViewer
                  articleId={testArticleId}
                  onTokenSelect={(tokenIds, tokens, sentenceIndex) => {
                    console.log('🔍 [UIDemo] Token selected:', { tokenIds, tokens, sentenceIndex });
                  }}
                  isTokenAsked={(textId, sentenceId, tokenId) => {
                    // 模拟检查 token 是否已被提问
                    return false;
                  }}
                  markAsAsked={async (textId, sentenceId, tokenId) => {
                    console.log('🔍 [UIDemo] Mark as asked:', { textId, sentenceId, tokenId });
                    return true;
                  }}
                  getNotationContent={(textId, sentenceId, tokenId) => {
                    // 模拟获取 notation 内容
                    return null;
                  }}
                  setNotationContent={(textId, sentenceId, tokenId, content) => {
                    console.log('🔍 [UIDemo] Set notation content:', { textId, sentenceId, tokenId, content });
                  }}
                  onSentenceSelect={(sentenceIndex, sentenceText, sentence) => {
                    console.log('🔍 [UIDemo] Sentence selected:', { sentenceIndex, sentenceText, sentence });
                  }}
                />
              </div>
              
              <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600">
                  <strong>功能说明：</strong>
                  <br />
                  • 支持点击选择单个 token，拖拽选择多个 token
                  <br />
                  • 支持点击选择整个句子
                  <br />
                  • 悬停在词汇上可以查看解释（如果有）
                  <br />
                  • 支持语法和词汇标注显示
                  <br />
                  • 所有交互事件都会在控制台输出日志
                  <br />
                  <br />
                  <strong>在 UIDemo 中修改：</strong>
                  <br />
                  • 可以在这里测试和修改 ArticleViewer 的功能
                  <br />
                  • 修改完成后，将更改同步到真实的 ArticleViewer 组件
                </p>
              </div>
            </div>
          </NotationContext.Provider>
        </SelectionProvider>
      );
    },
  },
  {
    title: 'TokenInlineTranslation',
    description: '内联翻译组件，提供 hover 单词显示翻译的功能，支持自定义延迟、语言和 tooltip 位置。',
    component: function TokenInlineTranslationDemoWrapper() {
      return (
        <TranslationDebugProvider>
          <TokenInlineTranslationDemo />
        </TranslationDebugProvider>
      );
    },
  },
];

const colorGroups = [
  {
    title: 'Primary',
    items: Object.entries(tokens.colors.primary).map(([key, value]) => ({ name: key, value })),
  },
  {
    title: 'Success',
    items: Object.entries(tokens.colors.success).map(([key, value]) => ({ name: key, value })),
  },
  {
    title: 'Warning',
    items: Object.entries(tokens.colors.warning).map(([key, value]) => ({ name: key, value })),
  },
  {
    title: 'Danger',
    items: Object.entries(tokens.colors.danger).map(([key, value]) => ({ name: key, value })),
  },
  {
    title: 'Gray',
    items: Object.entries(tokens.colors.gray).map(([key, value]) => ({ name: key, value })),
  },
  {
    title: 'Semantic / Text',
    items: Object.entries(tokens.colors.semantic.text).map(([key, value]) => ({ name: key, value })),
  },
  {
    title: 'Semantic / Background',
    items: Object.entries(tokens.colors.semantic.bg).map(([key, value]) => ({ name: key, value })),
  },
  {
    title: 'Semantic / Border',
    items: Object.entries(tokens.colors.semantic.border).map(([key, value]) => ({ name: key, value })),
  },
];

export default function UIDemoPage() {
  return (
    <TranslationDebugProvider>
    <div className="min-h-[calc(100vh-64px)] bg-gray-50 pb-16">
      <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
        <header className="mb-10 space-y-3">
          <p className="text-sm font-semibold uppercase tracking-wide text-blue-600">
            UI Design System / Base Components
          </p>
          <h1 className="text-3xl font-bold text-gray-900">基础组件 Demo</h1>
          <p className="text-gray-600">
            通过访问 <code className="rounded bg-gray-100 px-1.5 py-0.5 text-sm">?api=db&amp;page=UIDemo</code>{' '}
            可快速预览当前已实现的基础组件。所有示例均直接引用组件本身，便于验证样式与交互。
          </p>
        </header>

        <div className="space-y-8">
          {demoSections.map(({ title, description, component: Component }) => (
            <section
              key={title}
              className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm"
            >
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
                  <p className="text-sm text-gray-500">{description}</p>
                </div>
              </div>
              <div className="mt-6">
                <Component />
              </div>
            </section>
          ))}
        </div>

        {/* Color varients */}
        <div className="mt-12 space-y-6">
          <header className="space-y-2">
            <h2 className="text-2xl font-bold text-gray-900">Color varients</h2>
            <p className="text-gray-600">
              设计 token 中的当前颜色集合，按类别分组展示。
            </p>
          </header>
          <div className="grid gap-6 md:grid-cols-2">
            {colorGroups.map((group) => (
              <section
                key={group.title}
                className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm"
              >
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">{group.title}</h3>
                  <span className="text-sm text-gray-500">{group.items.length} colors</span>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {group.items.map(({ name, value }) => (
                    <div
                      key={name}
                      className="rounded-xl border border-gray-100 overflow-hidden bg-white shadow-sm"
                    >
                      <div
                        className="h-16 w-full"
                        style={{ backgroundColor: value }}
                      ></div>
                      <div className="px-3 py-2 flex flex-col gap-1">
                        <span className="text-xs font-medium text-gray-700 uppercase tracking-wide">{name}</span>
                        <span className="text-sm text-gray-600">{value}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            ))}
          </div>
        </div>

        <div className="mt-12 space-y-8">
          <header className="space-y-2">
            <h2 className="text-2xl font-bold text-gray-900">Function Components</h2>
            <p className="text-gray-600">
              基于基础组件组合出的业务组件示例，将逐步扩展。
            </p>
          </header>
          {functionSections.map(({ title, description, component: Component }) => (
            <section
              key={title}
              className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm"
            >
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h3 className="text-xl font-semibold text-gray-900">{title}</h3>
                  <p className="text-sm text-gray-500">{description}</p>
                </div>
              </div>
              <div className="mt-6">
                <Component />
              </div>
            </section>
          ))}
        </div>
      </div>
    </div>
    </TranslationDebugProvider>
  );
}


