from assistants.sub_assistants.prompt import vocab_explanation_sys_prompt, vocab_explanation_template
from assistants.sub_assistants.sub_assistant import SubAssistant

class VocabExplanationAssistant(SubAssistant):
    def __init__(self):
        super().__init__(
            sys_prompt=vocab_explanation_sys_prompt,
            max_tokens=200,
            parse_json=True
        )
    
    def build_prompt(self, sentence, vocab):
        """
        构建词汇解释的prompt
        
        Args:
            sentence: 句子对象
            vocab: 词汇或表达
            
        Returns:
            str: 格式化的prompt
        """
        return vocab_explanation_template.format(
            quoted_sentence=sentence.sentence_body,
            vocab_knowledge_point=vocab
        )
    
    def run(self, sentence, vocab):
        """
        根据句子和词汇生成词汇解释
        
        Args:
            sentence: 句子对象
            vocab: 词汇或表达
            
        Returns:
            str: 词汇解释
        """
        return super().run(sentence, vocab) 