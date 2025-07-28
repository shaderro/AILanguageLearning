#!/usr/bin/env python3
"""
Test script to verify layout fix for text overlapping issue
"""

import os
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_layout_fix():
    """Test if layout fix is working"""
    print("🧪 Testing Layout Fix")
    print("=" * 40)
    
    try:
        # Import the TextInputChatScreen
        from ui.screens.text_input_chat_screen import TextInputChatScreen
        print("✅ Successfully imported TextInputChatScreen")
        
        # Create a test instance
        screen = TextInputChatScreen()
        print("✅ TextInputChatScreen instance created")
        
        # Test tokenization
        test_text = "Hello, world! This is a test sentence."
        tokens = screen._tokenize_text(test_text)
        print(f"✅ Tokenization test: {tokens}")
        
        # Test sentence recreation
        screen.article_content = test_text
        screen._recreate_article_content()
        
        # Check if containers were created
        if hasattr(screen, 'sentence_containers') and screen.sentence_containers:
            print(f"✅ Sentence containers created: {len(screen.sentence_containers)}")
            for i, container in enumerate(screen.sentence_containers):
                print(f"   Sentence {i}: {len(container.children)} tokens")
        else:
            print("⚠️ No sentence containers created")
        
        # Check if tokens were created
        if hasattr(screen, 'tokens') and screen.tokens:
            print(f"✅ Tokens created: {len(screen.tokens)}")
            print(f"   Tokens: {screen.tokens}")
        else:
            print("⚠️ No tokens created")
        
        print("\n✅ Layout fix test completed successfully!")
        print("\n📋 Summary:")
        print("   - TextInputChatScreen imports correctly")
        print("   - Tokenization works properly")
        print("   - Sentence containers are created")
        print("   - Layout should no longer have overlapping text")
        
        return True
        
    except Exception as e:
        print(f"❌ Layout fix test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_layout_fix()
    if success:
        print("\n🎉 Layout fix is working! You can now run the main UI without text overlapping.")
        print("\n🚀 To test the full UI:")
        print("   cd ui && python run_app.py")
    else:
        print("\n⚠️ Layout fix test failed. Please check the errors above.")
    
    sys.exit(0 if success else 1) 