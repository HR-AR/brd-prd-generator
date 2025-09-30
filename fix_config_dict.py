#!/usr/bin/env python3
"""Fix config dictionary to LLMConfig conversion in multi_llm_generator.py"""

import re

file_path = "src/core/multi_llm_generator.py"

# Read the file
with open(file_path, 'r') as f:
    content = f.read()

# Pattern 1: Fix Gemini strategy instantiation
content = re.sub(
    r'gemini_strategy = GeminiStrategy\(self\.llm_factory\._DEFAULT_CONFIGS\[ProviderName\.GEMINI\]\)',
    '''gemini_config_dict = self.llm_factory._DEFAULT_CONFIGS[ProviderName.GEMINI].copy()
        gemini_api_key = self.llm_factory._get_api_key(ProviderName.GEMINI)
        gemini_config = LLMConfig(api_key=gemini_api_key, **gemini_config_dict)
        gemini_strategy = GeminiStrategy(gemini_config)''',
    content
)

# Pattern 2: Fix OpenAI strategy instantiation
content = re.sub(
    r'openai_strategy = OpenAIStrategy\(self\.llm_factory\._DEFAULT_CONFIGS\[ProviderName\.OPENAI\]\)',
    '''openai_config_dict = self.llm_factory._DEFAULT_CONFIGS[ProviderName.OPENAI].copy()
        openai_api_key = self.llm_factory._get_api_key(ProviderName.OPENAI)
        openai_config = LLMConfig(api_key=openai_api_key, **openai_config_dict)
        openai_strategy = OpenAIStrategy(openai_config)''',
    content
)

# Pattern 3: Fix Claude strategy instantiation
content = re.sub(
    r'claude_strategy = ClaudeStrategy\(self\.llm_factory\._DEFAULT_CONFIGS\[ProviderName\.CLAUDE\]\)',
    '''claude_config_dict = self.llm_factory._DEFAULT_CONFIGS[ProviderName.CLAUDE].copy()
        claude_api_key = self.llm_factory._get_api_key(ProviderName.CLAUDE)
        claude_config = LLMConfig(api_key=claude_api_key, **claude_config_dict)
        claude_strategy = ClaudeStrategy(claude_config)''',
    content
)

# Write back
with open(file_path, 'w') as f:
    f.write(content)

print("✓ Fixed all config dictionary accesses in multi_llm_generator.py")
print("  - Converted Gemini config dict to LLMConfig")
print("  - Converted OpenAI config dict to LLMConfig")
print("  - Converted Claude config dict to LLMConfig")