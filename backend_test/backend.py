import os
import PyPDF2

# Determine the absolute path of the directory where the script resides
script_dir = os.path.dirname(os.path.abspath(__file__))
pdf_path = os.path.join(script_dir, "test.pdf")

with open(pdf_path, "rb") as pdf_file:
    reader = PyPDF2.PdfReader(pdf_file)
    all_text = ""
    for page in reader.pages:
        page_text = page.extract_text() or ""
        all_text += page_text

print(all_text)


from google import genai

client = genai.Client(api_key="AIzaSyCDTI817Tn3jqk72GOfH3heJhgrz23Dgqc")

response = client.models.generate_content(
    model="gemini-2.0-flash", contents="Explain how AI works in a few words"
)
print(response.text)
