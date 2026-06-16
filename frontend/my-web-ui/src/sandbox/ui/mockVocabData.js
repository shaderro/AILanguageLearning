/** Mock vocabulary data for UI sandbox — production-shaped, never fetched from API. */

const MOCK_VOCAB_BASE = {
  partOfSpeech: 'Verb (reflexiv)',
  definitions: [
    '记住，记下（需要刻意记住的信息）',
    '在心里留意某事，以便之后回想',
  ],
  wordFeatures: [
    '**反身用法**：merken 常与 sich 连用，强调“为自己记住”',
    '**宾语位置**：etwas 作直接宾语，置于 merken 与 sich 之间',
    '**语域**：日常口语与书面语均可使用',
  ],
  rareSenses: [
    '在口语中偶指“注意到、察觉到”（与 sich 连用，语气较随意）',
  ],
  collocations: [
    'sich **Nummern** merken — 记住号码',
    'sich **Termine** merken — 记住日程',
    'sich **Namen** merken — 记住名字',
    'sich **Adressen** merken — 记住地址',
  ],
  grammarNotes: [
    'merken 与 sich erinnern 不同：merken 侧重“记住信息”，erinnern 侧重“回忆起”',
    '不用被动语态；始终是 **主语 + sich + 宾语 + merken**',
    '过去式：**merkte sich**；完成式：**hat sich gemerkt**',
  ],
  examples: [
    {
      original_sentence: 'Ich muss mir seine Telefonnummer merken.',
      context_explanation: 'merken 与 sich 连用，etwas（Telefonnummer）作宾语，表示“把号码记下来”。',
      source: 'Alltagsdeutsch · Kapitel 2',
    },
    {
      original_sentence: 'Kannst du dir das bitte merken?',
      context_explanation: '口语请求句；dir 为 sich 的与格形式，强调“为你自己记住”。',
      source: 'Alltagsdeutsch · Kapitel 2',
    },
    {
      original_sentence: 'Er hat sich den Termin nicht gemerkt.',
      context_explanation: 'Perfekt 形式 **hat sich gemerkt**；否定表示“没有记住约会”。',
      source: 'Alltagsdeutsch · Kapitel 5',
    },
  ],
}

export const MOCK_VOCAB_ITEMS = [
  {
    vocab_id: -9001,
    vocab_body: 'sich etwas merken',
    language: '德语',
    ...MOCK_VOCAB_BASE,
  },
  {
    vocab_id: -9002,
    vocab_body: 'sich erinnern',
    language: '德语',
    partOfSpeech: 'Verb (reflexiv)',
    definitions: ['回忆起，想起（从记忆中提取信息）'],
    wordFeatures: ['与 **an etwas** 或 **an jemanden** 连用表示“想起某事/某人”'],
    rareSenses: [],
    collocations: ['sich **an etwas erinnern**', 'sich **an die Kindheit erinnern**'],
    grammarNotes: ['强调“从记忆中调出”，与 merken（记住）语义不同'],
    examples: [
      {
        original_sentence: 'Ich erinnere mich an unseren ersten Tag.',
        context_explanation: 'sich an etwas erinnern 表示回忆起某个具体事件。',
        source: 'Alltagsdeutsch · Kapitel 4',
      },
    ],
  },
  {
    vocab_id: -9003,
    vocab_body: 'sich merken',
    language: '德语',
    partOfSpeech: 'Verb (reflexiv)',
    definitions: ['记住（省略宾语时，指记住刚提到的事）'],
    wordFeatures: ['**省略 etwas** 时，宾语由上下文推断'],
    rareSenses: [],
    collocations: ['**Merken Sie sich das!** — 请记住这个！'],
    grammarNotes: ['常用于祈使句 Merken Sie sich …'],
    examples: [
      {
        original_sentence: 'Merk dir das!',
        context_explanation: '口语祈使句，dir 为 sich 的与格；etwas 由语境省略。',
        source: 'Alltagsdeutsch · Kapitel 2',
      },
    ],
  },
  {
    vocab_id: -9004,
    vocab_body: 'festhalten (legacy)',
    language: '德语',
    legacyExplanation: `Verb

Common senses:
1. 抓住，握住
2. 坚持（观点、原则）

Word features:
- **可分动词**：fest + halten
- 与 **an etwas** 连用表示“坚持某事”

Collocations:
- **festhalten an** — 坚持
- **sich festhalten an** — 紧紧抓住

Grammar notes:
- 过去式：**hielt fest**`,
    examples: [
      {
        original_sentence: 'Er hielt sich am Geländer fest.',
        context_explanation: 'legacy 格式例句，用于测试解析失败时全白底。',
        source: 'Legacy Sample',
      },
    ],
  },
]

function buildExplanationPayload(sections, base) {
  return {
    part_of_speech: base.partOfSpeech,
    definitions: sections.definition ? base.definitions : [],
    word_features: sections.wordFeatures ? base.wordFeatures : [],
    rare_senses: sections.rareSense ? (base.rareSenses || []) : [],
    collocations: sections.collocations ? base.collocations : [],
    grammar_notes: sections.grammarNotes ? base.grammarNotes : [],
  }
}

/** Build a vocab object compatible with VocabDetailCard (structured explanation v2). */
export function buildMockVocab(itemIndex = 0, sections) {
  const item = MOCK_VOCAB_ITEMS[itemIndex] ?? MOCK_VOCAB_ITEMS[0]

  if (item.legacyExplanation) {
    return {
      vocab_id: item.vocab_id,
      vocab_body: item.vocab_body,
      language: item.language,
      explanation: item.legacyExplanation,
      examples: sections.examples ? (item.examples || []) : [],
    }
  }

  const payload = buildExplanationPayload(sections, item)

  return {
    vocab_id: item.vocab_id,
    vocab_body: item.vocab_body,
    language: item.language,
    explanation: JSON.stringify(payload),
    examples: sections.examples ? (item.examples || MOCK_VOCAB_BASE.examples) : [],
  }
}

export const DEFAULT_SANDBOX_LAYOUT = {
  uiMode: 'default',
  maxWidth: 'production',
  sections: {
    definition: true,
    wordFeatures: true,
    rareSense: true,
    collocations: true,
    grammarNotes: true,
    examples: true,
  },
}

export const MOCK_VOCAB_LIST_LENGTH = MOCK_VOCAB_ITEMS.length
