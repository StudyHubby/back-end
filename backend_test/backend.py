import os
import PyPDF2
from google import genai
import time # Needed for potential delays or TTL management

API_KEY = "AIzaSyCDTI817Tn3jqk72GOfH3heJhgrz23Dgqc"
PDF_FILENAME = "test.pdf"
# Use a model compatible with CachedContent and your generation needs
# 'gemini-1.5-flash-latest' or 'gemini-1.5-pro-latest' are good candidates.
MODEL_NAME = "gemini-1.5-flash-latest"
CACHE_TTL_SECONDS = 3600 # Cache for 1 hour

# --- Initialization ---
try:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel(MODEL_NAME)
except Exception as e:
    print(f"Error initializing Gemini client: {e}")
    exit(1)

    
# --- PDF Processing ---
script_dir = os.path.dirname(os.path.abspath(__file__))
pdf_path = os.path.join(script_dir, PDF_FILENAME)
all_text = ""

try:
    with open(pdf_path, "rb") as pdf_file:
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
    # Create the cache
    pdf_cache = genai.caching.CachedContent.create(
        model=model.model_name, # Use the same model name used for generation
        display_name="lecture_pdf_context",
        system_instruction="You are an assistant analyzing a lecture transcript provided in the cached content. Base all your responses strictly on this text.",
        contents=[all_text], # The actual content to cache
        ttl=time.Duration(seconds=CACHE_TTL_SECONDS),
    )
    print(f"Cache created successfully. Name: {pdf_cache.name}")
    # The cache name (pdf_cache.name) is what you'll use later

except Exception as e:
    print(f"Error creating cached content: {e}")
    print("Proceeding without cache. Each request will send the full text.")
    # We can continue without cache, but it will be less efficient


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
    # It's often better to let the user ask *their* question
    user_question = input("What specifically would you like to ask about the lecture? ")
    user_instruction = f"Based *only* on the lecture content, answer the following question: {user_question}"
    # Alternative if you want the AI to generate questions:
    # user_instruction = "Generate some detailed questions a student might ask about the lecture content."
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
        response = model.generate_content(
            [pdf_cache, user_instruction], # Combine cache reference and user instruction
            # You might want to add generation_config here if needed
            # generation_config=genai.types.GenerationConfig(...)
        )
    else:
        # *** Fallback: Send full text if caching failed ***
        print("Warning: Cache not available. Sending full text.")
        # Rebuild the prompt including the full text
        full_prompt = f"System Instruction: You are an assistant analyzing the following lecture transcript. Base all your responses strictly on this text.\n\nLecture Content:\n{all_text}\n\nUser Request:\n{user_instruction}"
        response = model.generate_content(
            full_prompt
            # generation_config=genai.types.GenerationConfig(...)
         )

    # --- Display Response ---
    print("\nResponse:")
    # Handle potential lack of text in response or safety blocks
    if response.parts:
         print(response.text)
    elif response.prompt_feedback:
         print(f"Content generation blocked. Reason: {response.prompt_feedback.block_reason}")
         if response.prompt_feedback.safety_ratings:
              for rating in response.prompt_feedback.safety_ratings:
                   print(f"  - {rating.category}: {rating.probability}")
    else:
         print("No response text received.")


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