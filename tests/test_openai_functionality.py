#!/usr/bin/env python3
"""
OpenAI API Key Testing Script

This script tests the OpenAI API key configuration and functionality
to ensure chat and RAG features will work properly.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add project path
sys.path.append('/home/user/agents/meditwin-agents')

from src.config.settings import settings
from src.utils.logging import logger, log_openai_request
import time

# Try importing OpenAI
try:
    import openai
    from openai import OpenAI
except ImportError:
    print("❌ OpenAI package not found. Installing...")
    os.system("uv add openai")
    import openai
    from openai import OpenAI


class OpenAITester:
    """Test OpenAI API functionality."""
    
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.chat_model = settings.openai_model_chat
        self.search_model = settings.openai_model_search
        self.client = None
        
        # Test results
        self.results = {
            "api_key_valid": False,
            "chat_model_working": False,
            "embeddings_working": False,
            "search_model_working": False,
            "total_tests": 4,
            "passed_tests": 0
        }
    
    def print_config(self):
        """Print current OpenAI configuration."""
        print("🔧 OPENAI CONFIGURATION")
        print("=" * 50)
        print(f"API Key: {self.api_key[:10]}...{self.api_key[-4:] if len(self.api_key) > 14 else 'INVALID'}")
        print(f"Chat Model: {self.chat_model}")
        print(f"Search Model: {self.search_model}")
        print()
    
    def test_api_key_validity(self):
        """Test if the API key is valid."""
        print("🔑 Testing API Key Validity...")
        
        try:
            self.client = OpenAI(api_key=self.api_key)
            
            # Try to list models to validate API key
            start_time = time.time()
            models = self.client.models.list()
            duration = time.time() - start_time
            
            log_openai_request("models.list", "validation", duration=duration)
            
            self.results["api_key_valid"] = True
            self.results["passed_tests"] += 1
            print(f"✅ API Key is valid - Found {len(models.data)} available models")
            
            # List some available models
            model_names = [model.id for model in models.data if 'gpt' in model.id][:5]
            print(f"   Available GPT models: {', '.join(model_names)}")
            
        except Exception as e:
            print(f"❌ API Key validation failed: {str(e)}")
            self.results["api_key_valid"] = False
            
        print()
    
    def test_chat_completion(self):
        """Test chat completion functionality."""
        print("💬 Testing Chat Completion...")
        
        if not self.client:
            print("❌ Cannot test chat - API key validation failed")
            return
        
        try:
            start_time = time.time()
            
            response = self.client.chat.completions.create(
                model=self.chat_model,
                messages=[
                    {"role": "system", "content": "You are a helpful medical assistant. Respond briefly."},
                    {"role": "user", "content": "What is hypertension?"}
                ],
                max_tokens=100,
                temperature=0.1
            )
            
            duration = time.time() - start_time
            tokens_used = response.usage.total_tokens if response.usage else None
            
            log_openai_request("chat.completions", self.chat_model, tokens_used, duration)
            
            self.results["chat_model_working"] = True
            self.results["passed_tests"] += 1
            
            print(f"✅ Chat completion successful")
            print(f"   Model: {response.model}")
            print(f"   Tokens used: {tokens_used}")
            print(f"   Duration: {duration:.2f}s")
            print(f"   Response: {response.choices[0].message.content[:100]}...")
            
        except Exception as e:
            print(f"❌ Chat completion failed: {str(e)}")
            self.results["chat_model_working"] = False
            
        print()
    
    def test_embeddings(self):
        """Test embeddings functionality for RAG."""
        print("🔍 Testing Embeddings (for RAG)...")
        
        if not self.client:
            print("❌ Cannot test embeddings - API key validation failed")
            return
        
        try:
            start_time = time.time()
            
            response = self.client.embeddings.create(
                model="text-embedding-ada-002",
                input="Patient presents with chest pain and shortness of breath."
            )
            
            duration = time.time() - start_time
            tokens_used = response.usage.total_tokens if response.usage else None
            
            log_openai_request("embeddings.create", "text-embedding-ada-002", tokens_used, duration)
            
            embedding = response.data[0].embedding
            
            self.results["embeddings_working"] = True
            self.results["passed_tests"] += 1
            
            print(f"✅ Embeddings generation successful")
            print(f"   Model: {response.model}")
            print(f"   Embedding dimensions: {len(embedding)}")
            print(f"   Tokens used: {tokens_used}")
            print(f"   Duration: {duration:.2f}s")
            
        except Exception as e:
            print(f"❌ Embeddings generation failed: {str(e)}")
            self.results["embeddings_working"] = False
            
        print()
    
    def test_search_model(self):
        """Test search-enabled model for web search."""
        print("🔎 Testing Search Model...")
        
        if not self.client:
            print("❌ Cannot test search model - API key validation failed")
            return
        
        try:
            start_time = time.time()
            
            # Note: The search model functionality may require specific setup
            response = self.client.chat.completions.create(
                model=self.search_model,
                messages=[
                    {"role": "user", "content": "What are the latest guidelines for treating hypertension in 2024?"}
                ],
                max_tokens=150,
                temperature=0.1
            )
            
            duration = time.time() - start_time
            tokens_used = response.usage.total_tokens if response.usage else None
            
            log_openai_request("chat.completions", self.search_model, tokens_used, duration)
            
            self.results["search_model_working"] = True
            self.results["passed_tests"] += 1
            
            print(f"✅ Search model working")
            print(f"   Model: {response.model}")
            print(f"   Tokens used: {tokens_used}")
            print(f"   Duration: {duration:.2f}s")
            print(f"   Response: {response.choices[0].message.content[:100]}...")
            
        except Exception as e:
            print(f"❌ Search model failed: {str(e)}")
            if "does not exist" in str(e).lower():
                print("   Note: Search model may not be available with this API key")
            self.results["search_model_working"] = False
            
        print()
    
    def print_summary(self):
        """Print test summary."""
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        success_rate = (self.results["passed_tests"] / self.results["total_tests"]) * 100
        
        print(f"Tests Passed: {self.results['passed_tests']}/{self.results['total_tests']}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        print("Detailed Results:")
        print(f"  ✅ API Key Valid: {'Yes' if self.results['api_key_valid'] else 'No'}")
        print(f"  ✅ Chat Model: {'Yes' if self.results['chat_model_working'] else 'No'}")
        print(f"  ✅ Embeddings: {'Yes' if self.results['embeddings_working'] else 'No'}")
        print(f"  ✅ Search Model: {'Yes' if self.results['search_model_working'] else 'No'}")
        print()
        
        if self.results["passed_tests"] >= 3:
            print("🎉 OpenAI integration is ready for production!")
            print("   Chat and RAG functionality should work properly.")
        elif self.results["passed_tests"] >= 2:
            print("⚠️  Basic OpenAI functionality working, but some features may be limited.")
        else:
            print("❌ OpenAI integration needs attention before using chat/RAG features.")
        
        return self.results
    
    def run_all_tests(self):
        """Run all OpenAI tests."""
        print("🧪 OPENAI API TESTING STARTED")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        self.print_config()
        
        # Run tests in sequence
        self.test_api_key_validity()
        self.test_chat_completion()
        self.test_embeddings()
        self.test_search_model()
        
        # Print summary
        self.print_summary()
        
        return self.results


def main():
    """Main test function."""
    tester = OpenAITester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if results["passed_tests"] >= 3:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure


if __name__ == "__main__":
    main()
