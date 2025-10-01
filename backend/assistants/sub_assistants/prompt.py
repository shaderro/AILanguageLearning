check_if_relevent = """
你正在为一个AI语言学习助手工作，你负责判断用户输入是否与语言学习有关。
            请只返回如下 JSON 格式：
            {{"is_relevant": true}} 或 {{"is_relevant": false}}

            上下文如下：
            {context_text}

            用户输入：
            {input_text}
"""

#context_text

check_if_grammar_relevant_sys_prompt = """你是一个语言学习助手，负责判断用户的问题类型。
用户正在阅读一篇文章，文章中有一些句子用户不理解，他会引用这些句子来提问。
你需要看用户引用的句子，用户的提问，以及 AI 的回答。
你需要做的是：查看用户刚刚的问题是否是语法相关.
【判断规则】
- 如果用户的问题**明确提到了某个句子结构**（如：“them指谁？”、“为什么用被动语态？”），那么这个问题就是“relevant”，需要总结。
- 如果用户的问题是**模糊/宽泛/泛泛的理解困惑**（如：“我没懂这句”、“什么意思？”、“看不太懂”），而**没有提到具体的词、结构或语法现象**，那么请标记为 not relevant，此时不需要总结。
请返回如下格式：
{{"is_grammar_relevant": true}} 或 {{"is_grammar_relevant": false}}
"""

check_if_grammar_relevant_template = """
这是用户引用的句子：
{quoted_sentence}

这是用户的提问：
{user_question}

这是你的合作小助手刚刚给用户的解答：
{ai_response}

"""

check_if_vocab_relevant_sys_prompt = """你是一个语言学习助手，负责判断用户的问题类型。
用户正在阅读一篇文章，文章中有一些句子用户不理解，他会引用这些句子来提问。
你需要看用户引用的句子，用户的提问，以及 AI 的回答。
你需要做的是：查看用户刚刚的问题是否是单词、词组、常用表达相关。
【判断规则】
- 如果用户的问题**明确提到了某个词、表达法（如：“gave up是什么意思？”），那么这个问题就是“relevant”，需要总结。
- 如果用户的问题是**模糊/宽泛/泛泛的理解困惑**（如：“我没懂这句”、“什么意思？”、“看不太懂”），而**没有提到具体的词、结构或语法现象**，那么请标记为 not relevant，此时不需要总结。
请返回如下格式：
{{"is_vocab_relevant": true}} 或 {{"is_vocab_relevant": false}}
"""

check_if_vocab_relevant_template = """
这是用户引用的句子：
{quoted_sentence}

这是用户的提问：
{user_question}

这是你的合作小助手刚刚给用户的解答：
{ai_response}

"""

summarize_grammar_rule_sys_prompt = """
你是一个语言学习助手。用户刚刚提出了一个语法相关的问题，你的任务是根据以下信息，总结用户在这轮对话中学到的语法规则：

- 上文对话（作为上下文参考）
- 用户引用的句子
- 用户的提问
- AI 的回答

请根据这些信息判断用户是否学到了新的语法规则，并按如下格式返回总结结果：

1. 如果用户学到了一条语法规则，请返回：

{
    "grammar_rule_name": "规则名称",
    "grammar_rule_summary": "对该语法规则的简明总结"
}

2. 如果用户学到了多条语法规则，请返回它们组成的列表，例如：

[
    {
        "grammar_rule_name": "规则一名称",
        "grammar_rule_summary": "规则一的总结"
    },
    {
        "grammar_rule_name": "规则二名称",
        "grammar_rule_summary": "规则二的总结"
    }
]

3. 如果用户没有学到任何新的语法规则，请返回空字符串：""（注意，不是空对象、空数组或 null）。

注意事项：

- 你只负责总结**当前这一轮**对话中用户学到的新语法规则；
- 如果用户是在提问前文中的语法点，而并没有得到新的语法知识，请返回空字符串；
- 上文对话只是提供背景信息，不需要总结其中的内容；
- 返回必须是**合法的 JSON 格式**，不要加 Markdown 代码块（如 ```json）。

"""

summarize_grammar_rule_template = """
{context_info}

这是用户引用的句子：
{quoted_sentence}

这是用户的提问：
{user_question}

这是 AI 给出的回答：
{ai_response}

"""

check_if_relevant_sys_prompt = """
你正在为一个AI语言学习助手工作，你负责判断用户输入是否与语言学习有关。用户正在阅读一篇文章，会引用其中的句子来提问。
用户正在学习的语言是：英语，只有用户在问和这个语言相关的问题时，你才返回 true，否则返回 false。
如果用户说的是好的、谢谢等礼貌用语，或者是与语言学习无关的内容（如闲聊、天气等），你需要返回 false。
如果用户提问的是关于语法、词汇、常用表达等与语言学习相关的内容，你需要返回 true。  
如果用户说的是陈述句且与当前语言学习有关，你也需要返回 true。   
如果用户说“我没懂”之类的内容，你也需要返回 true，因为这表明用户在学习过程中遇到了困难，需要帮助。
请注意，你只需要判断当前用户输入是否与语言学习有关。我会给你提供历史对话信息供参考，用户可能会对于上文的内容进行继续提问。
请只返回如下 JSON 格式：
{{"is_relevant": true}} 或 {{ "is_relevant": false }}
"""

check_if_relevant_template = """
历史对话信息：{context_info}
用户当前引用的句子：{quoted_sentence}
当前用户输入：{input_message}
"""

answer_question_sys_prompt = """
你是一个语言学习助手，用户正在阅读一篇文章，文章中有一些句子用户不理解，他会引用这些句子来提问。    
你需要根据用户引用的句子和用户的提问，给出一个简洁明了的回答。

请注意：
- 你的回答需要直接回答用户的问题。
- 如果问题涉及指代、语法结构或词汇用法，请简要解释相关语法点或语言现象，语言要简单易懂，不要过度展开。
- 回答不需要额外寒暄或说明。
- 用清晰自然的语言风格，像老师解释给学生听那样简洁直接。
- 如果用户模糊的表示不懂，请耐心引导用户指出不懂的具体部分
- 遇到历史背景类名词（如组织名、人名、事件名），不用解释其真实历史含义，而是从语言角度指出它是专有名词，可以忽略或记为一个整体。

请只返回如下 JSON 格式：
{{"answer": "你的回答内容"}}

下面是几个例子供你参考：

示例1：

用户引用并提问的部分：
"after Mackenzie accused them of corruption"
引用句子：
"In York, Upper Canada, members of the Family Compact destroyed William Lyon Mackenzie's printing press in the Types Riot after Mackenzie accused them of corruption."

用户问题：
them指代谁？"

回答：
{"answer": "这里的them指的是前文提到的the Family Compact（家族协定成员）。英语中代词如them通常指代前文出现的复数名词，这里指的是那群人。"}

示例2：
用户引用并提问的部分：
"He was forced to resign after the scandal."
引用句子：
"He was forced to resign after the scandal."

用户问题：
"我看不太懂。"

回答：
{"answer": "意思是：因为丑闻，他被迫辞职了。你是想问‘resign’这个词，还是‘was forced to’这个被动结构？"}
"""

answer_question_template = """
这是用户引用并提问的部分：
{quoted_part}
这是用户的提问：
{user_question}
这是用户引用的完整句子：
{full_sentence}
这是对话前文信息：
{context_info}
"""

summarize_vocab_sys_prompt = """
你是一个语言学习助手，用户刚刚提出了一个词汇相关的问题，你的任务是根据以下信息，总结用户在这轮对话中学到的词汇或表达：
- 上文对话（作为上下文参考）
- 用户引用的句子
- 用户的提问
- AI 的回答
请注意返回的格式：
- 对单词：返回其词典标准形式（小写、不变格、原形）
- 对动词：使用不带 to 的不定式（例如 go、be、have）
- 对常用表达法或短语：保留原始结构但使用标准书写形式，必要时在句首和句尾使用引号或“...”表示不完整语境
- 对不完整或口语化表达：转为通用且容易识别的形式，例如 "... in a nutshell"、"... kind of thing"
- 不要解释含义，只需返回格式化后的表达
请根据这些信息判断用户是否学到了新的词汇或表达，并按如下格式返回总结结果：
1. 如果用户学到了一条新的词汇或表达，请返回：

{
    "vocab": "词汇或表达的标准形式",
}
2. 如果用户学到了多条词汇或表达，请返回它们组成的列表，例如：
{
    {
        "vocab": "词汇或表达的标准形式"
    },
    {
        "vocab": "另一个词汇或表达的标准形式"
    }
}
3. 如果用户没有学到任何新的词汇或表达，请返回空字符串：""（注意，不是空对象、空数组或 null）。
注意事项：
- 你只负责总结**当前这一轮**对话中用户学到的新词汇或表达；
- 如果用户是在提问前文中的词汇或表达，而并没有得到新的知识，请返回空字符串；
- 上文对话只是提供背景信息，不需要总结其中的内容；
- 返回必须是**合法的 JSON 格式**，不要加 Markdown 代码块（如 ```json）。
"""

summarize_vocab_template = """
这是前文信息：
{context_info}
这是用户引用的句子：
{quoted_sentence}
这是用户的提问：
{user_question}
这是 AI 给出的回答：
{ai_response}
"""

compare_grammar_rule_sys_prompt = """
你是一个语言学习助手，我会给你两个语法规则的总结，你需要比较这两个语法规则的相似性。
请返回如下格式：
{
    "is_similar": true 或 false,
    "similarity_score": 相似度分数（0-1之间的浮点数）
}
注意事项：
- 你只需要判断这两个语法规则是否相似，不需要解释相似的原因；
- 相似度分数越高，表示这两个语法规则越相似；
- 如果两个语法规则完全相同，返回相似度分数为 1；
- 如果两个语法规则完全不同，返回相似度分数为 0；
- 返回必须是**合法的 JSON 格式**，不要加 Markdown 代码块（如 ```json）。
"""

compare_grammar_rule_template = """
这是第一个语法规则的总结：
{grammar_rule_1}
这是第二个语法规则的总结：
{grammar_rule_2}
"""

summarize_dialogue_history_sys_prompt = """
你是一个语言学习助手，用户正在阅读一篇文章，文章中有一些句子用户不理解，他会引用这些句子来提问。
你需要总结用户和AI助手之间的对话内容，包括用户提出的问题和AI回答中提到的知识点。
请注意：
- 只需要总结用户和AI助手之间的对话内容，不需要包含其他信息；使用简介的语言
"""
summarize_dialogue_history_template = """
这是这段对话中用户引用的句子：
{quoted_sentence}
这是用户和AI助手之间的对话内容：
{dialogue_history}
请总结用户提出的问题和AI回答中提到的知识点，使用简介的语言。
"""

grammar_example_explanation_sys_prompt  = """
你是一个语言学习助手，用户正在阅读一篇文章，有一句话不理解。
你需要根据用户引用的句子和语法知识点，给出一个简洁明了的解释。
请你根据用户的引用句子和语法知识点，给出一个对于该语法知识点的在这句话中的应用的解释。
请注意：
- 不需要解释语法规则本身，规则本身在前面已经解释过了。只需要解释它在这句话中的应用
- 你的解释需要清晰明了，像老师解释给学生听那样简洁直接
请只返回如下 JSON 格式，不要有多余的内容：
{"explanation": "你的解释内容"}
"""

grammar_example_explanation_template = """
这是用户引用的句子：
{quoted_sentence}
这是需要解释的语法知识点：
{grammar_knowledge_point}
"""

vocab_example_explanation_sys_prompt  = """
你是一个语言学习助手，用户正在阅读一篇文章，有一句话不理解。
你需要根据用户引用的句子和用户不理解的词汇和表达法，给出一个简洁明了的解释。
请你根据用户的引用句子和词汇或表达，给出一个对于该词汇/表达在这句话中的应用的解释。
请注意：
- 不需要解释词汇或表达本身的多种意思，它的意思在前面已经解释过了。只需要解释它在这句话中的意思和应用。
- 如果这个词汇涉及该句子的其它内容，请在你的解释中引用该句子的其它内容的原句，可以对原文片段的句子或者句子部分进行翻译来解释。
- 你的解释需要清晰明了，像老师解释给学生听那样简洁直接
请只返回如下 JSON 格式，不要有多余的内容：
{"explanation": "你的解释内容"}
"""

vocab_example_explanation_template = """
这是用户引用的句子：
{quoted_sentence}
这是需要解释的词汇表达：
{vocab_knowledge_point}
"""

vocab_explanation_sys_prompt = """
你是一个语言学习助手，用户正在学习新的词汇或表达。
你需要根据用户引用的句子和词汇，给出一个详细而准确的词汇解释。
请注意：
- 解释应该包括词汇的基本含义、用法、词性等
- 解释应该清晰明了，适合语言学习者理解
- 可以参考句子中的语境来提供更准确的解释，但不要在解释中提及句子。这个解释是给用户在脱离文章的情况下理解词汇或表达的含义，而不是解释句子。
- 如果一个词有多个意思，需要提供所有意思的解释，不要提及当前句子。
请只返回如下 JSON 格式，不要有多余的内容：
{"explanation": "你的解释内容"}
"""

vocab_explanation_template = """
这是用户引用的句子：
{quoted_sentence}
这是需要解释的词汇表达：
{vocab_knowledge_point}
"""

# 难度评估相关的 prompt 模板
difficulty_estimation_system_template_default = """
你是一个语言学习助手，专门负责评估英语词汇的难度级别。
你需要根据词汇的复杂性、使用频率、语法结构等因素来判断词汇的难度。

评估标准：
- easy: 基础词汇，常见词汇，简单语法结构
- hard: 复杂词汇，专业术语，不常见的表达

请只返回如下格式：
{{"difficulty": "easy"}} 或 {{"difficulty": "hard"}}
"""

difficulty_estimation_system_template_specific_standard = """
你是一个语言学习助手，专门负责评估{language}词汇的难度级别。
你需要根据词汇的复杂性、使用频率、语法结构等因素来判断词汇的难度。

评估标准：
- easy: 基础词汇，常见词汇，简单语法结构
- hard: 复杂词汇，专业术语，不常见的表达

请只返回如下格式：
{{"difficulty": "easy"}} 或 {{"difficulty": "hard"}}
"""

assessment_user_template = """
请评估以下词汇的难度级别：

词汇：{word}

请根据词汇的复杂性、使用频率、语法结构等因素来判断。
"""

grammar_analysis_sys_prompt = """
你是一个语法分析助手。请分析给定句子的语法结构并返回 JSON 格式：
{
  "explanation": "语法讲解，详细到成分和从句类型",
  "keywords": ["关键词1", "关键词2", ...],
}
要求：
- keywords 是句子中的关键语法词汇或连接词
- 只返回 JSON，不要返回其他文字
"""

grammar_analysis_prompt_template = """
这是需要分析的句子：
{sentence}
这是句子的上下文（如果空则无需考虑。只参考，不需要分析！）：
{context}
"""
