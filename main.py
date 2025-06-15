# main.py
from original_text_manager import OriginalTextManager
from grammar_rule_manager import GrammarRuleManager
from data_classes import OriginalText
from vocab_manager import VocabManager
from data_controller import DataController
from assistant import LanguageAssistant

def test_original_text_manager():
    """
    manager = OriginalTextManager()
    manager.add_text("Test Text 1")
    manager.add_text("Test Text 2")

    # Test adding sentences
    manager.add_sentence_to_text(1, "This is the first sentence.")
    manager.add_sentence_to_text(1, "This is the second sentence.")
    manager.add_sentence_to_text(2, "This is a sentence in the second text.")

    text1 = manager.get_text_by_id(1)
    print(f"Text ID: {text1.text_id}, Title: {text1.text_title}")
    for sentence in text1.text_by_sentence:
        print(f"Sentence ID: {sentence.sentence_id}, Body: {sentence.sentence_body}")
    
    text2 = manager.get_text_by_id(2)
    print(f"Text ID: {text2.text_id}, Title: {text2.text_title}")
    for sentence in text2.text_by_sentence:
        print(f"Sentence ID: {sentence.sentence_id}, Body: {sentence.sentence_body}")

    text1 = manager.get_text_by_title("Test Text 1")
    print(f"Text ID: {text1.text_id}, Title: {text1.text_title}")
    for sentence in text1.text_by_sentence:
        print(f"Sentence ID: {sentence.sentence_id}, Body: {sentence.sentence_body}")

    text2 = manager.get_text_by_title("Test Text 2")
    print(f"Text ID: {text2.text_id}, Title: {text2.text_title}")
    for sentence in text2.text_by_sentence:
        print(f"Sentence ID: {sentence.sentence_id}, Body: {sentence.sentence_body}")

    print(manager.list_texts_by_title())

    manager.remove_text_by_id(1)
    print("After removing text with ID 1:")
    print(manager.list_texts_by_title())

    manager.save_to_file("test_new_origianl_text_manager.json")
    print("Saved to file.")
    """
    # Test loading from file
    manager = OriginalTextManager()
    manager.load_from_file("test_new_origianl_text_manager.json")
    title_list = manager.list_titles()
    print("List of titles after loading from file:")
    print(title_list)

def test_grammar_rule_manager():
    grammar_manager = GrammarRuleManager()
    text_manager = OriginalTextManager()
    text_manager.add_text("Test Text 1")
    text_manager.add_sentence_to_text(1, "This is the first sentence.")
    grammar_manager.add_new_rule("Test Rule 1", "This is a test rule explanation.")
    grammar_manager.add_grammar_example(text_manager, 1, 1, 1, "This is a test example context.")
    #grammar_manager.add_grammar_example(text_manager, 1, 1, 2, "This is another test example context.")
    grammar_manager.save_to_file("test_grammar_rule_manager.json")
    text_manager.save_to_file("test_new_origianl_text_manager.json")
    print("Saved to file.")
    # Test loading from file
    grammar_manager.load_from_file("test_grammar_rule_manager.json")
    text_manager.load_from_file("test_new_origianl_text_manager.json")
    print("Loaded from file.")
    rule = grammar_manager.get_example_by_text_sentence_id(1, 1)
    print(f"Rule ID: {rule.rule_id}, Text ID: {rule.text_id}, Sentence ID: {rule.sentence_id}, Context: {rule.explanation_context}")
    examples = grammar_manager.get_examples_by_rule_id(1)
    print("Examples for Rule ID 1:")
    for example in examples:
        print(f"Text ID: {example.text_id}, Sentence ID: {example.sentence_id}, Context: {example.explanation_context}")

def test_vocab_manager():
    vocab_manager = VocabManager()
    vocab_manager.add_new_vocab("Test Vocab 1", "This is a test vocab explanation.")
    text_manager = OriginalTextManager()
    text_manager.add_text("Test Text 1")
    text_manager.add_sentence_to_text(1, "This is the first sentence.")
    vocab_manager.add_vocab_example(text_manager, 1, 1, 1, "This is a test example context.")

    vocab_manager.save_to_file("test_vocab_manager.json")
    text_manager.save_to_file("test_new_origianl_text_manager.json")
    print("Saved to file.")
    # Test loading from file
    vocab_manager.load_from_file("test_vocab_manager.json")
    text_manager.load_from_file("test_new_origianl_text_manager.json")
    print("Loaded from file.")
    examples = vocab_manager.get_examples_by_vocab_id(1)
    print("Examples for Rule ID 1:")
    for example in examples:
        print(f"Text ID: {example.text_id}, Sentence ID: {example.sentence_id}, Context: {example.context_explanation}")
    sentence = text_manager.get_text_by_id(1).text_by_sentence[0]
    print(f"Sentence ID: {sentence.sentence_id}, Body: {sentence.sentence_body}")

def test_data_controller():
    data_controller = DataController()
    data_controller.add_new_text("Test Text 1")
    data_controller.add_sentence_to_text(1, "This is the first sentence.")
    data_controller.add_new_grammar_rule("Test Rule 1", "This is a test rule explanation.")
    data_controller.add_grammar_example(1, 1, 1, "This is a test example context.")
    data_controller.save_data("test_grammar_rule_manager.json", "test_vocab_manager.json", "test_new_origianl_text_manager.json")
    print("Saved to file.")
    # Test loading from file
    data_controller.load_data("test_grammar_rule_manager.json", "test_vocab_manager.json", "test_new_origianl_text_manager.json")
    print("Loaded from file.")
    rule = data_controller.grammar_manager.get_rule_by_id(1)
    print(f"Rule ID: {rule.rule_id}, Name: {rule.name}, Explanation: {rule.explanation}")
    grammar_examples = data_controller.grammar_manager.get_examples_by_rule_id(1)
    #vocab_examples = data_controller.vocab_manager.get_examples_by_vocab_id(1)
    print("Grammar Example:")
    for example in grammar_examples:
        print(f"Text ID: {example.text_id}, Sentence ID: {example.sentence_id}, Context: {example.explanation_context}")
    #print("Vocab Example:")
    #for example in vocab_examples:
    #    print(f"Text ID: {example.text_id}, Sentence ID: {example.sentence_id}, Context: {example.context_explanation}")

def test_langeuage_assistant():
    assistant = LanguageAssistant()
    assistant.reset()
    assistant.run()

def main():
    test_langeuage_assistant()
   

if __name__ == "__main__":
    main()