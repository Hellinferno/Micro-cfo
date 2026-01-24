import os
import sys
from dotenv import load_dotenv

load_dotenv()

print("--- SYSTEM SANITY CHECK ---")
print(f"Python Version: {sys.version}")

# Check Environment Variables
gemini_key = os.getenv("GEMINI_API_KEY")
openrouter_key = os.getenv("OPENROUTER_API_KEY")

print(f"GEMINI_API_KEY Configured: {bool(gemini_key)}")
if gemini_key:
    print(f"GEMINI_API_KEY Prefix: {gemini_key[:5]}...")

print(f"OPENROUTER_API_KEY Configured: {bool(openrouter_key)}")

# Check Dependencies
try:
    import requests
    print("Requests Library: OK")
except ImportError as e:
    print(f"Requests Library: FAIL ({e})")

try:
    from fastapi import FastAPI
    print("FastAPI: OK")
except ImportError as e:
    print(f"FastAPI: FAIL ({e})")

try:
    import google.generativeai as genai
    print("Google Generative AI: OK")
except ImportError as e:
    print(f"Google Generative AI: FAIL ({e})")

print("--- CHECK COMPLETE ---")
