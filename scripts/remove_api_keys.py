#!/usr/bin/env python3
"""
Security Script: Remove all hardcoded API keys from test files
"""

import os
import re

# Files that contain hardcoded API keys
files_to_clean = [
    'test_agent_a.py',
    'test_gemini_agent_a.py',
    'test_gemini_direct.py',
    'demo_complete_agent_a.py'
]

# Patterns to remove
patterns_to_remove = [
    (r"os\.environ\['GEMINI_API_KEY'\]\s*=\s*['\"]AIzaSy[^'\"]+['\"]", 
     "# SECURITY: API key removed. Set via environment variable."),
    (r"os\.environ\['OPENROUTER_API_KEY'\]\s*=\s*['\"]sk-or-[^'\"]+['\"]",
     "# SECURITY: API key removed. Set via environment variable."),
    (r"os\.environ\['GOOGLE_API_KEY'\]\s*=\s*['\"][^'\"]+['\"]",
     "# SECURITY: API key removed. Set via environment variable."),
]

security_header = """# SECURITY: Load API keys from environment variables only
# Set your API key before running:
#   Windows: set GEMINI_API_KEY=your-key-here
#   Unix/Mac: export GEMINI_API_KEY=your-key-here
# Or create a .env file (see .env.example)
"""

def clean_file(filepath):
    """Remove hardcoded API keys from a file"""
    if not os.path.exists(filepath):
        print(f"⚠️  File not found: {filepath}")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    changes_made = False
    
    # Remove hardcoded API keys
    for pattern, replacement in patterns_to_remove:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            changes_made = True
            print(f"✅ Removed API key from {filepath}")
    
    # Add security header if API key was removed
    if changes_made and security_header not in content:
        # Find the first import statement
        import_match = re.search(r'^import\s+', content, re.MULTILINE)
        if import_match:
            insert_pos = import_match.start()
            content = content[:insert_pos] + security_header + '\n' + content[insert_pos:]
    
    if changes_made:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    
    return False

def main():
    print("🔒 Security Cleanup: Removing Hardcoded API Keys")
    print("=" * 50)
    
    cleaned_count = 0
    
    for filepath in files_to_clean:
        if clean_file(filepath):
            cleaned_count += 1
    
    print("\n" + "=" * 50)
    print(f"✅ Cleaned {cleaned_count} files")
    print("🔒 All API keys removed from source code")
    print("\n💡 Users must now set API keys via:")
    print("   1. Environment variables")
    print("   2. .env file (recommended)")
    print("\nSee .env.example for template")

if __name__ == "__main__":
    main()
