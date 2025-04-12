import google.generativeai as genai
import os

# --- Configuration ---
# Make sure API_KEY is configured correctly (e.g., using os.getenv)
API_KEY = "AIzaSyCDTI817Tn3jqk72GOfH3heJhgrz23Dgqc" # Replace with your secure method
if not API_KEY:
    print("Error: API key not configured.")
    exit(1)

genai.configure(api_key=API_KEY)

# --- List Models Supporting Caching ---
print("Available models and their supported generation methods:")
print("-" * 60)
found_caching_model = False
for m in genai.list_models():
  # Check if 'createCachedContent' is listed in the supported methods
  if 'createCachedContent' in m.supported_generation_methods:
    print(f"Model Name: {m.name}")
    print(f"  Display Name: {m.display_name}")
    print(f"  Supported Methods: {m.supported_generation_methods}")
    print("-" * 60)
    found_caching_model = True

if not found_caching_model:
    print("\nNo models found supporting 'createCachedContent' with your current API key/settings.")
else:
    print("\nRecommendation: Choose one of the models listed above for the CACHE_MODEL_NAME.")
