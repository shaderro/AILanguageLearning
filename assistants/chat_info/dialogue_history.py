from data_managers.data_classes import Sentence
from assistants.sub_assistants.summarize_dialogue_history import SummarizeDialogueHistoryAssistant
import json

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

    def save_to_file(self, path: str):
        data = {
            "summary": self.summary,
            "messages": [
                {
                    "user": msg["user"],
                    "ai": msg["ai"],
                    "quote": {
                        "text_id": msg["quote"].text_id,
                        "sentence_id": msg["quote"].sentence_id,
                        "sentence_body": msg["quote"].sentence_body,
                        "grammar_annotations": msg["quote"].grammar_annotations,
                        "vocab_annotations": msg["quote"].vocab_annotations,
                    }
                }
                for msg in self.messages_history
            ]
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_from_file(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                    print(f"[Warning] File {path} is empty. Starting with empty record.")
                    return
            data = json.loads(content)
        self.summary = data.get("summary", "")
        self.messages_history = [
            {
                "user": item["user"],
                "ai": item["ai"],
                "quote": Sentence(
                    text_id=item["quote"]["text_id"],
                    sentence_id=item["quote"]["sentence_id"],
                    sentence_body=item["quote"]["sentence_body"],
                    grammar_annotations=item["quote"]["grammar_annotations"],
                    vocab_annotations=item["quote"]["vocab_annotations"]
                )
            }
            for item in data.get("messages", [])
        ]

