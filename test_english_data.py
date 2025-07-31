#!/usr/bin/env python3
"""
Test English data loading
"""

import os
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from ui.services.language_learning_binding_service import LanguageLearningBindingService
from data_managers.data_controller import DataController

def main():
    """Test English data loading"""
    print("🚀 Testing English data loading...")
    
    # Initialize data controller
    data_controller = DataController(max_turns=10)
    
    # Initialize binding service
    binding_service = LanguageLearningBindingService(data_controller=data_controller)
    
    # Get grammar data
    grammar_bundles = binding_service.get_data("grammar_bundles")
    print(f"📊 Grammar bundles: {type(grammar_bundles)}, count: {len(grammar_bundles) if grammar_bundles else 0}")
    
    if grammar_bundles:
        print("📝 Sample grammar rules:")
        for i, (rule_id, bundle) in enumerate(list(grammar_bundles.items())[:3]):
            print(f"  {i+1}. ID: {rule_id}")
            print(f"     Name: {bundle.rule.name}")
            print(f"     Explanation: {bundle.rule.explanation[:100]}...")
            print()
    
    # Get vocabulary data
    vocab_bundles = binding_service.get_data("vocab_bundles")
    print(f"📊 Vocabulary bundles: {type(vocab_bundles)}, count: {len(vocab_bundles) if vocab_bundles else 0}")
    
    if vocab_bundles:
        print("📝 Sample vocabulary expressions:")
        for i, (vocab_id, bundle) in enumerate(list(vocab_bundles.items())[:3]):
            print(f"  {i+1}. ID: {vocab_id}")
            print(f"     Body: {bundle.vocab.vocab_body}")
            print(f"     Explanation: {bundle.vocab.explanation[:100]}...")
            print()
    
    print("✅ English data loading test completed!")

if __name__ == "__main__":
    main() 