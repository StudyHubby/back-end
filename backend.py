import io
import PyPDF2
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse

# Import your AI client library and create a client instance.
from google import genai
client = genai.Client(api_key="AIzaSyCDTI817Tn3jqk72GOfH3heJhgrz23Dgqc")

app = FastAPI()

def extract_pdf_text(file_bytes: bytes) -> str:
    """Extracts text from a PDF given its byte content."""
    pdf_file = io.BytesIO(file_bytes)
    reader = PyPDF2.PdfReader(pdf_file)
    all_text = ""
    for page in reader.pages:
        page_text = page.extract_text() or ""
        all_text += page_text
    return all_text

@app.post("/process/")
async def process_request(
    file: UploadFile = File(...),
    user_option: int = Form(...),
    user_input: str = Form("")
):
    # Ensure the uploaded file is a PDF.
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF.")

    # Read the file and extract the text.
    file_bytes = await file.read()
    all_text = extract_pdf_text(file_bytes)

    # Build a prompt based on the user's selected option.
    # Option 1 is interpreted as a one-shot chat (for interactive chat, consider websockets or session management).
    if user_option == 1:
        # For an interactive chat scenario, you might need to manage conversation history.
        # Here we simulate one prompt by simply appending the user input to some context.
        conversation_context = (
            "The following conversation is based on a PDF file:\n\n" +
            all_text + "\n\n"
        )
        prompt = conversation_context + f"User: {user_input}\nAI:"
    elif user_option == 2:
        prompt = (
            f"Respond to the question: \"{user_input}\" based on the following text:\n\n" +
            all_text
        )
    elif user_option == 3:
        prompt = (
            "Create an in depth summary about the following text:\n\n" +
            all_text
        )
    elif user_option == 4:
        prompt = (
            "Generate multiple choice questions that test understanding of the following text:\n\n" +
            all_text +
            ". Format it so there are 10 questions that are multiple choice. And at the end, "
            "have the answer to the questions labeled at the end from 1-10. Before you list the answers, "
            "list out 10 underscores then list the answers with the corresponding number."
        )
    elif user_option == 5:
        prompt = (
            "Explain the following text in very simple terms as if I were a 5-year-old:\n\n" +
            all_text
        )
    elif user_option == 6:
        prompt = (
            "Compare the following user-provided summary to the original text.\n\n" +
            f"User Summary:\n{user_input}\n\nLecture Content:\n{all_text}\n\n" +
            "Evaluate how well the summary captures the key points, identify missing concepts, and suggest any improvements."
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid option. Please choose a number between 1 and 6.")

    # Generate a response using your AI service.
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )

    return JSONResponse({
        "response": response.text
    })

# Run the FastAPI application.
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
