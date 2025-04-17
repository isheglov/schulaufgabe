import os
import uuid
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import aiofiles

app = FastAPI()

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    session_id = str(uuid.uuid4())
    upload_dir = f"/tmp/{session_id}"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, "input.jpg")
    async with aiofiles.open(file_path, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)
    return JSONResponse({"session_id": session_id}) 
