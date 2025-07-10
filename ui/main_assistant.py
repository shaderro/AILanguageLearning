# main_assistant.py
class MainAssistant:
    def answer(self, user_input, referenced_sentence=None):
        # 模拟AI逻辑，返回一个字符串
        if "grammar" in user_input.lower():
            return "This is a grammar point explanation."
        else:
            return "I don't understand, but here's a try!"
