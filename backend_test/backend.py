import os
import PyPDF2
# Correct import for the Gemini library
import google.generativeai as genai
# from google.genai import types # types is usually accessed via genai.types
import datetime # Import datetime for timedelta

# --- Configuration ---
# WARNING: Avoid hardcoding API keys. Use environment variables or a secure method.
# API_KEY = os.getenv("GEMINI_API_KEY") # Example using environment variable
API_KEY = "AIzaSyCDTI817Tn3jqk72GOfH3heJhgrz23Dgqc" # Your original key (replace with secure method)
if not API_KEY:
    print("Error: GEMINI_API_KEY environment variable not set.")
    exit(1)

PDF_FILENAME = "test.pdf"
# Use a model compatible with CachedContent and your generation needs
MODEL_NAME = "models/gemini-1.5-flash-001"
CACHE_TTL_SECONDS = 3600 # Cache for 1 hour

# --- Initialization ---
try:
    # Correct configuration call
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel(MODEL_NAME)
except AttributeError as e:
     print(f"Error initializing Gemini client: {e}")
     print("This might be due to an old library version. Try upgrading: pip install --upgrade google-generativeai")
     exit(1)
except Exception as e:
    print(f"Error initializing Gemini client: {e}")
    exit(1)


# --- PDF Processing ---
# Consider using 'pypdf' instead of 'PyPDF2' as it's actively maintained
script_dir = os.path.dirname(os.path.abspath(__file__))
pdf_path = os.path.join(script_dir, PDF_FILENAME)
all_text = ""

try:
    with open(pdf_path, "rb") as pdf_file:
        # Consider switching to pypdf: from pypdf import PdfReader
        reader = PyPDF2.PdfReader(pdf_file)
        if not reader.pages:
             print(f"Error: No pages found in PDF: {pdf_path}")
             exit(1)
        for page in reader.pages:
            page_text = page.extract_text() or "" # Handle empty pages
            all_text += page_text + "\n" # Add newline between pages
except FileNotFoundError:
    print(f"Error: PDF file not found at {pdf_path}")
    exit(1)
# Consider more specific exceptions for PyPDF2 if needed
except Exception as e:
    print(f"Error reading PDF file: {e}")
    exit(1)

if not all_text.strip():
    print("Error: Extracted text from PDF is empty.")
    exit(1)

# --- Create Cached Content ---
pdf_cache = None
try:
    print("Creating content cache for the PDF text...")
    pdf_cache = genai.caching.CachedContent.create(
        model=model.model_name, # Use the same model name used for generation
        display_name="lecture_pdf_context",
        system_instruction= "You are an assistant analyzing a lecture transcript provided in the cached content. Base all your responses strictly on this text.",
        contents=[all_text], # The actual content to cache
        # Correct way to specify TTL using datetime.timedelta
        ttl=datetime.timedelta(seconds=CACHE_TTL_SECONDS),
    )
    print(f"Cache created successfully. Name: {pdf_cache.name}")
    # The cache name (pdf_cache.name) is what you'll use later

except Exception as e:
    # Catching specific exceptions like PermissionDeniedError might be useful
    print(f"Error creating cached content: {e}")
    print("Proceeding without cache. Each request will send the full text.")
    # We can continue without cache, but it will be less efficient

# --- (Rest of your user interaction and generation code remains the same) ---

# --- User Interaction ---
print("\nSelect an option (based on the loaded PDF):")
print("1: Do chat")
print("2: Ask about lecture")
print("3: Make quizzes")
print("4: Generate multiple choice questions")
print("5: Explain like I am a 5-year-old")
print("6: Tell me if I still have work to do (based on my summary)")

user_option = input("Enter your option (1-6): ")

# --- Build Prompt (Instruction Part Only) ---
user_instruction = "" # This will contain only the task-specific instruction

if user_option == '1':
    user_instruction = "Engage in a friendly chat based *only* on the provided lecture content."
elif user_option == '2':
    user_question = input("What specifically would you like to ask about the lecture? ")
    user_instruction = f"Based *only* on the lecture content, answer the following question: {user_question}"
elif user_option == '3':
    user_instruction = "Create a set of quiz questions (e.g., short answer, fill-in-the-blank) using *only* the provided lecture text."
elif user_option == '4':
    user_instruction = "Generate multiple-choice questions with answers that test understanding of the provided lecture text. Base questions and answers *only* on the text."
elif user_option == '5':
    user_instruction = "Explain the main points of the lecture text in very simple terms, as if explaining to a 5-year-old. Use *only* information from the text."
elif user_option == '6':
    user_summary = input("Provide a simple explanation of the lecture in your own words:\n")
    user_instruction = f"Compare the following user-provided summary to the original lecture text.\n\nUser Summary:\n{user_summary}\n\nEvaluate how well the summary captures the key points from the lecture, identify any significant missing concepts mentioned in the lecture, and suggest improvements based *only* on the lecture content."
else:
    print("Invalid option. Please run the script again and choose a number between 1 and 6.")
    if pdf_cache:
        try:
            print(f"Deleting cache: {pdf_cache.name}")
            pdf_cache.delete()
        except Exception as e:
            print(f"Warning: Failed to delete cache {pdf_cache.name}: {e}")
    exit(1)


# --- Generate Content using Cache (or fallback) ---
print("\nGenerating response...")
try:
    if pdf_cache:
        # *** Use the cache ***
        # Pass the cache object directly and the new user instruction
        print(f"Using cache: {pdf_cache.name}") # Add log
        response = model.generate_content(
            [pdf_cache, user_instruction], # Combine cache reference and user instruction
             generation_config=genai.types.GenerationConfig(
                # Add temperature or other configs if needed
             )
        )
    else:
        # *** Fallback: Send full text if caching failed ***
        print("Warning: Cache not available. Sending full text.")
        # Rebuild the prompt including the full text and system instruction
        # (Note: The system instruction is part of the cache, so include it here if not using cache)
        full_prompt = f"""System: You are an assistant analyzing the following lecture transcript. Base all your responses strictly on this text.

Lecture Content:
{all_text}

User Request:
{user_instruction}"""
        response = model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                # Add temperature or other configs if needed
            )
         )

    # --- Display Response ---
    print("\nResponse:")
    # Improved response handling
    try:
        print(response.text)
    except ValueError: # Handle cases where accessing .text might fail due to blocking
        if response.prompt_feedback:
             print(f"Content generation blocked. Reason: {response.prompt_feedback.block_reason}")
             if response.prompt_feedback.safety_ratings:
                  for rating in response.prompt_feedback.safety_ratings:
                       print(f"  - {rating.category}: {rating.probability}")
        else:
             print("No response text received and no blocking reason found.")
    except AttributeError: # Handle cases where response might not have expected attributes
        print("Unexpected response format received.")
        print(response)


except Exception as e:
    print(f"\nAn error occurred during content generation: {e}")

finally:
    # --- Clean up Cache ---
    if pdf_cache:
        try:
            print(f"\nDeleting cache: {pdf_cache.name}")
            pdf_cache.delete()
            print("Cache deleted successfully.")
        except Exception as e:
            print(f"Warning: Failed to delete cache {pdf_cache.name}: {e}")