#!/usr/bin/env python3
"""
Main UI Runner with MainAssistant Integration
This script runs the enhanced language learning app with AI assistant functionality
"""

import os
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def main():
    """Main entry point"""
    print("🎯 Starting Enhanced Language Learning App")
    print("=" * 60)
    print("📋 Features:")
    print("   ✅ MainAssistant AI Integration")
    print("   ✅ Smart Question Logic")
    print("   ✅ Token Selection with Sentence Boundaries")
    print("   ✅ Structured Data Output")
    print("   ✅ Punctuation Merging")
    print("   ✅ Real-time AI Chat")
    print("=" * 60)
    
    try:
        # Import and run the main UI
        from ui.run_app import LangUIApp
        app = LangUIApp()
        app.run()
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all required modules are available")
        return 1
    except Exception as e:
        print(f"❌ Runtime error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("👋 App closed successfully")
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 