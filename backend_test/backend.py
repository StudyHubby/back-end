import os
import PyPDF2
from google import genai

client = genai.Client(api_key="AIzaSyCDTI817Tn3jqk72GOfH3heJhgrz23Dgqc")

# Determine the absolute path of the directory where the script resides
script_dir = os.path.dirname(os.path.abspath(__file__))
pdf_path = os.path.join(script_dir, "test.pdf")

with open(pdf_path, "rb") as pdf_file:
    reader = PyPDF2.PdfReader(pdf_file)
    all_text = ""
    for page in reader.pages:
        page_text = page.extract_text() or ""
        all_text += page_text

#print(all_text)


""" response = client.models.generate_content(
    model="gemini-2.0-flash", contents="Summarize the following text: " + all_text
)
print(response.text) """

# Display menu options to the user
print("Select an option:")
print("1: Do chat")
print("2: Ask about lecture")
print("3: Make quizzes")
print("4: Generate multiple choice questions")
print("5: Explain like I am a 5-year-old")
print("6: Tell me if I still have work to do")

# Prompt for input
user_option = input("Enter your option (1-6): ")


# Build a prompt based on the user's choice
if user_option == '1':
    prompt = f"Engage in a friendly chat based on the following text:\n\n{all_text}"
elif user_option == '2':
    prompt = f"Ask detailed questions about the lecture based on the following text:\n\n{all_text}"
elif user_option == '3':
    prompt = f"Create a set of quizzes using the following lecture text:\n\n{all_text}"
elif user_option == '4':
    prompt = f"Generate multiple choice questions that test understanding of the following text:\n\n{all_text}"
elif user_option == '5':
    prompt = f"Explain the following text in very simple terms as if I were a 5-year-old:\n\n{all_text}"
elif user_option == '6':
    user_summary = input("Provide a simple explanation of the lecture in your own words:\n")
    prompt = f"Compare the following user-provided summary to the original text.\n\nUser Summary:\n{user_summary}\n\nLecture Content:\n{all_text}\n\nEvaluate how well the summary captures the key points, identify missing concepts, and suggest any improvements."

else:
    print("Invalid option. Please run the script again and choose a number between 1 and 6.")
    exit(1)


response = client.models.generate_content(
    model="gemini-2.0-flash", 
    contents=prompt
)

print("\nResponse:")
print(response.text)