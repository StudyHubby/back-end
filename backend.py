import io
import PyPDF2
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
import os


# Import your AI client library and create a client instance.
from google import genai
client = genai.Client(api_key="API_KEY_HERE")

app = FastAPI()

@app.get("/")
async def read_index():
    # Adjust the file path if necessary
    return FileResponse(os.path.join(os.getcwd(), "index.html"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000/"],
    allow_methods=[""],
    allow_headers=[""],
)

def extract_pdf_text(file_bytes: bytes) -> str:
    """Extracts text from a PDF given its byte content."""
    pdf_file = io.BytesIO(file_bytes)
    reader = PyPDF2.PdfReader(pdf_file)
    all_text = ""
    for page in reader.pages:
        page_text = page.extract_text() or ""
        all_text += page_text
    return all_text

def parse_questions(quizz_test):
    split_test = quizz_test.split("\n")
    questions = []
    i = 0
    
    for line in split_test:
        if (len(line) > 0):
            if (i < 25):
                if (i % 5 == 0):
                    questions.append({"question": line})
                else:
                    questions[i // 5][f"option {i%5}"] = line

            else:
                questions[(i-1) % 5]["answer"] = line
                
            i += 1
    return questions



last_response = ""
all_text = ""
file_name = ""

@app.post("/upload/")
async def process_request(
    file: UploadFile = File(...),
    name: str = Form("")
):
    global all_text
    global file_name
    # Ensure the uploaded file is a PDF.
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF.")

    # Read the file and extract the text.
    file_bytes = await file.read()
    all_text = extract_pdf_text(file_bytes)
    file_name = name

    return JSONResponse({"message": "sucess"})
    

@app.post("/process/")
async def process_request(
    user_option: int = Form(...),
    user_input: str = Form("")
):
    global last_response
    global all_text

    # Build a prompt based on the user's selected option.
    # Option 1 is interpreted as a one-shot chat (for interactive chat, consider websockets or session management).
    if user_option == 1:
        prompt = f"Start a conversation with a short paragraph about the following text: {all_text}"
        if (len(last_response) > 0):
            prompt = f"Continue the following conversation with a response:\n user:\"{prompt}\",\n You:\"{last_response}\",\n user:\"{user_input}\",\n You:"
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
            ". Format it so there are 5 questions that are multiple choice with 4 choices each. And at the end, "
            "have the answer to the questions labeled at the end from 1-5. Do not add any extra text to the response."
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

    if (user_option == 4):
        return JSONResponse({"response": parse_questions(response.text)})
    last_response = response.text

    return JSONResponse({
        "response": response.text
    })

# Run the FastAPI application.
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
