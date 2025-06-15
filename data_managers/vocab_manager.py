import json
from typing import List, Dict
from dataclasses import asdict
from data_classes import VocabExpression, VocabExpressionExample, VocabExpressionBundle
import os
from original_text_manager import OriginalTextManager

class VocabManager:
    def __init__(self):
        self.vocab_bundles: Dict[int, VocabExpressionBundle] = {}  # vocab_id -> Bundle

    def get_new_vocab_id(self) -> int:
        if not self.vocab_bundles:
            return 1
        return max(self.vocab_bundles.keys()) + 1

    def add_new_vocab(self, vocab_body: str, explanation: str) -> int:
        new_vocab_id = self.get_new_vocab_id()
        new_vocab = VocabExpression(vocab_id=new_vocab_id, vocab_body=vocab_body, explanation=explanation)
        self.vocab_bundles[new_vocab_id] = VocabExpressionBundle(vocab=new_vocab, example=[])
        return new_vocab_id

    def add_vocab_example(self, text_manager: OriginalTextManager, vocab_id: int, text_id: int, sentence_id: int, context_explanation: str):
        if vocab_id not in self.vocab_bundles:
            raise ValueError(f"Vocab ID {vocab_id} does not exist.")
        new_example = VocabExpressionExample(
            vocab_id=vocab_id,
            text_id=text_id,
            sentence_id=sentence_id,
            context_explanation=context_explanation
        )
        self.vocab_bundles[vocab_id].example.append(new_example)
        text_manager.add_vocab_example_to_sentence(text_id, sentence_id, vocab_id)
        
    def get_vocab_by_id(self, vocab_id: int) -> VocabExpression:
        if vocab_id not in self.vocab_bundles:
            raise ValueError(f"Vocab ID {vocab_id} does not exist.")
        return self.vocab_bundles[vocab_id].vocab

    def get_examples_by_vocab_id(self, vocab_id: int) -> List[VocabExpressionExample]:
        if vocab_id not in self.vocab_bundles:
            raise ValueError(f"Vocab ID {vocab_id} does not exist.")
        return self.vocab_bundles[vocab_id].example

    def get_example_by_text_sentence_id(self, text_id: int, sentence_id: int) -> VocabExpressionExample:
        for bundle in self.vocab_bundles.values():
            for example in bundle.example:
                if example.text_id == text_id and example.sentence_id == sentence_id:
                    return example
        return None

    def save_to_file(self, path: str):
        with open(path, 'w') as f:
            json.dump({vocab_id: asdict(bundle) for vocab_id, bundle in self.vocab_bundles.items()}, f, indent=4, ensure_ascii=False)

    def load_from_file(self, path: str):
        if not os.path.exists(path):
            raise FileNotFoundError(f"The file at path {path} does not exist.")
        if not os.path.isfile(path):
            raise ValueError(f"The path {path} is not a file.")
        with open(path, 'r') as f:
            data = json.load(f)
            for vocab_id, bundle_data in data.items():
                vocab = VocabExpression(**bundle_data['vocab'])
                examples = [VocabExpressionExample(**ex) for ex in bundle_data['example']]
                self.vocab_bundles[int(vocab_id)] = VocabExpressionBundle(vocab=vocab, example=examples)
