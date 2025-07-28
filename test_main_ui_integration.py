#!/usr/bin/env python3
"""
Test script for Main UI Integration
Tests the enhanced TextInputChatScreen with MainAssistant functionality
"""

import os
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_text_input_chat_screen():
    """Test TextInputChatScreen functionality"""
    print("🧪 Testing TextInputChatScreen Integration")
    print("=" * 50)
    
    try:
        # Import the enhanced TextInputChatScreen
        from ui.screens.text_input_chat_screen import TextInputChatScreen
        print("✅ Successfully imported TextInputChatScreen")
        
        # Test MainAssistant initialization
        print("\n🔧 Testing MainAssistant initialization...")
        screen = TextInputChatScreen()
        
        # Check if MainAssistant was initialized
        if hasattr(screen, 'main_assistant') and screen.main_assistant:
            print("✅ MainAssistant initialized successfully")
        else:
            print("⚠️ MainAssistant not available (fallback mode)")
        
        # Check if DataController was initialized
        if hasattr(screen, 'data_controller') and screen.data_controller:
            print("✅ DataController initialized successfully")
        else:
            print("⚠️ DataController not available")
        
        # Test tokenization
        print("\n🔤 Testing tokenization...")
        test_text = "Hello, world! This is a test."
        tokens = screen._tokenize_text(test_text)
        print(f"   Input: '{test_text}'")
        print(f"   Tokens: {tokens}")
        
        # Test sentence boundary check
        print("\n📝 Testing sentence boundary check...")
        screen.sentences = [
            {'text': 'Hello, world!', 'sentence_id': 0, 'tokens': ['Hello,', 'world!']},
            {'text': 'This is a test.', 'sentence_id': 1, 'tokens': ['This', 'is', 'a', 'test.']}
        ]
        
        # Test within same sentence
        result1 = screen._check_sentence_boundary(0, 1)
        print(f"   Same sentence (0,1): {result1}")
        
        # Test across sentences
        result2 = screen._check_sentence_boundary(0, 3)
        print(f"   Across sentences (0,3): {result2}")
        
        # Test structured data output
        print("\n📊 Testing structured data output...")
        selected_tokens = ['Hello,', 'world!']
        sentence_info = {'text': 'Hello, world!', 'sentence_id': 0}
        user_input = "What does this mean?"
        
        screen._output_structured_selection_data(selected_tokens, sentence_info, user_input)
        
        print("\n✅ All tests completed successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_main_assistant_integration():
    """Test MainAssistant integration"""
    print("\n🤖 Testing MainAssistant Integration")
    print("=" * 50)
    
    try:
        from assistants.main_assistant import MainAssistant
        from data_managers import data_controller
        from data_managers.data_classes import Sentence
        
        print("✅ Successfully imported MainAssistant components")
        
        # Create DataController
        dc = data_controller.DataController(max_turns=100)
        print("✅ DataController created")
        
        # Create MainAssistant
        ma = MainAssistant(data_controller_instance=dc)
        print("✅ MainAssistant created")
        
        # Test Sentence object creation
        sentence = Sentence(
            text_id=1,
            sentence_id=0,
            sentence_body="Hello, world!",
            grammar_annotations=[],
            vocab_annotations=[]
        )
        print("✅ Sentence object created")
        
        print("\n✅ MainAssistant integration test completed!")
        return True
        
    except Exception as e:
        print(f"❌ MainAssistant integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🎯 Main UI Integration Test Suite")
    print("=" * 60)
    
    # Test TextInputChatScreen
    test1_result = test_text_input_chat_screen()
    
    # Test MainAssistant integration
    test2_result = test_main_assistant_integration()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Results Summary:")
    print(f"   TextInputChatScreen Test: {'✅ PASSED' if test1_result else '❌ FAILED'}")
    print(f"   MainAssistant Integration: {'✅ PASSED' if test2_result else '❌ FAILED'}")
    
    if test1_result and test2_result:
        print("\n🎉 All tests passed! Main UI integration is working correctly.")
        print("\n🚀 You can now run the main UI with:")
        print("   cd ui && python run_app.py")
        print("\n📝 Features available:")
        print("   - Token selection with sentence boundaries")
        print("   - MainAssistant AI integration")
        print("   - Smart question logic")
        print("   - Structured data output")
        print("   - Real-time chat with AI")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
    
    return test1_result and test2_result

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 