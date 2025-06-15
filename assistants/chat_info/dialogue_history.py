from data_managers.data_classes import Sentence
from assistants.sub_assistants.summarize_dialogue_history import SummarizeDialogueHistoryAssistant

class DialogueHistory:
    def __init__(self, max_turns):
        self.max_turns = max_turns
        self.messages_history = []
        self.summary = str()
        self.summarize_dialogue_assistant = SummarizeDialogueHistoryAssistant()

    def add_message(self, user_input: str, ai_response: str, quoted_sentence: Sentence):
        self.messages_history.append({
            "user": user_input,
            "ai": ai_response,
            "quote": quoted_sentence
        })
        self.keep_in_max_turns()

    def _summarize_and_clear(self):
        summary = self.summarize_dialogue_history()
        self.summary = summary
        self.messages_history.clear()
        pass

    def message_history_to_string(self) -> str:
        return "\n".join(
            f"User: {msg['user']}\nAI: {msg['ai']}\nQuote: {msg['quote'].sentence_body}"
            for msg in self.messages_history
        )
    
    def summarize_dialogue_history(self) -> str:
        dialogue_history_str = self.message_history_to_string()
        if not dialogue_history_str:
            return "No dialogue history to summarize."
        print("Summarizing dialogue history...")
        quoted_sentence = self.messages_history[-1]['quote'].sentence_body if self.messages_history else ""
        print("Quoted sentence for summary:", quoted_sentence)
        summary = self.summarize_dialogue_assistant.run(dialogue_history_str, self.messages_history[-1]['quote'], verbose=True)
        if isinstance(summary, str):
            print("Summary is: \n" + summary)
            return summary
        elif isinstance(summary, list) and summary:
            return summary[0].get("summary", "No summary available.")
        else:
            return "No summary available."

    def keep_in_max_turns(self):
        self._summarize_and_clear() if len(self.messages_history) > self.max_turns else None

