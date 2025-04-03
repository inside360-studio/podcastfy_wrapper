from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from fastapi.security import APIKeyQuery
import os
from typing import List
from .models import GeneratePodcastRequest, UserPodcastRequest
from podcastfy.client import generate_podcast

# Define API key (in production, this should be in a secure environment variable)
API_KEY = "tZmH2qv4PwjbXl0Ks6D8YrE3nRdCzT5oBfGaIuVxL9Jy"
api_key_query = APIKeyQuery(name="api-key", auto_error=False)

# Create a dependency to validate the API key
async def get_api_key(api_key: str = Depends(api_key_query)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return api_key

def read_file_content(file_path: str) -> str:
    """
    Try to read a file with multiple encodings to handle different text formats.
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        The content of the file as a string
        
    Raises:
        UnicodeDecodeError if the file cannot be read with any supported encoding
    """
    encodings: List[str] = ['utf-8', 'cp1252', 'iso-8859-1', 'latin1']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
            
    raise UnicodeDecodeError(
        f"Unable to read file {file_path} with any of these encodings: {encodings}"
    )

app = FastAPI(
    title="Podcastfy API",
    description="API for generating podcasts with API key protection",
)

@app.post("/generate-podcast", dependencies=[Depends(get_api_key)])
async def generate_podcast_file(request: UserPodcastRequest):
    """
    This endpoint generates a podcast audio file using Podcastfy's generate_podcast function.
    It accepts a user-friendly JSON payload and transforms it into the format expected by generate_podcast.
    """
    try:
        print("=== Request received ===")
        print(f"URLs: {request.urls}")
        print(f"Podcast Name: {request.name}")
        print(f"TTS Model: {request.tts_model}")
        
        # Set API keys in environment
        os.environ["GEMINI_API_KEY"] = request.google_key
        os.environ["OPENAI_API_KEY"] = request.openai_key
        # Only set ElevenLabs API key if it's provided
        if request.elevenlabs_key:
            os.environ["ELEVENLABS_API_KEY"] = request.elevenlabs_key
        
        # Transform to generate_podcast format
        generate_request = request.to_generate_podcast_request()
        
        # Generate podcast audio
        output_file = generate_podcast(
            text=generate_request.text,
            urls=generate_request.urls,
            image_paths=generate_request.image_paths,
            tts_model=generate_request.tts_model,
            conversation_config=generate_request.conversation_config.dict(),
            longform=generate_request.longform,
        )
        
        print(f"=== Generated output file: {output_file} ===")
        
        if not os.path.exists(output_file):
            print(f"Error: File not found at {output_file}")
            raise HTTPException(status_code=404, detail="Generated audio file not found")
        
        # Return the audio file as a response
        return FileResponse(
            output_file,
            media_type="audio/mpeg",
            filename=os.path.basename(output_file),
            content_disposition_type="inline" if request.stream_output else "attachment"
        )
    except Exception as e:
        print(f"=== Error occurred: {str(e)} ===")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-transcript", dependencies=[Depends(get_api_key)])
async def generate_transcript(request: UserPodcastRequest):
    """
    This endpoint generates a transcript using Podcastfy's generate_podcast function.
    It accepts the same JSON payload as /generate-podcast but always returns the transcript content.
    """
    try:
        print("=== Transcript Request received ===")
        print(f"URLs: {request.urls}")
        print(f"Podcast Name: {request.name}")
        
        # Set API keys in environment
        os.environ["GEMINI_API_KEY"] = request.google_key
        os.environ["OPENAI_API_KEY"] = request.openai_key
        os.environ["ELEVENLABS_API_KEY"] = request.elevenlabs_key
        
        # Transform to generate_podcast format
        generate_request = request.to_generate_podcast_request()
        
        # Generate transcript
        output_file = generate_podcast(
            text=generate_request.text,
            urls=generate_request.urls,
            image_paths=generate_request.image_paths,
            tts_model=generate_request.tts_model,
            conversation_config=generate_request.conversation_config.dict(),
            longform=generate_request.longform,
            transcript_only=True  # Always generate transcript only
        )
        
        print(f"=== Generated transcript file: {output_file} ===")
        
        if not os.path.exists(output_file):
            print(f"Error: File not found at {output_file}")
            raise HTTPException(status_code=404, detail="Generated transcript not found")
        
        # Always return the transcript content
        try:
            content = read_file_content(output_file)
            return {"transcript": content}
        except UnicodeDecodeError as e:
            print(f"Error reading transcript: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Error reading transcript: Unsupported file encoding"
            )
        except Exception as e:
            print(f"Error reading transcript: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error reading transcript: {str(e)}"
            )
            
    except Exception as e:
        print(f"=== Error occurred: {str(e)} ===")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/audio/{file_path:path}", dependencies=[Depends(get_api_key)])
async def download_file(file_path: str):
    """
    This endpoint allows downloading a generated file by its path.
    """
    try:
        print(f"=== Download requested for: {file_path} ===")
        if not os.path.exists(file_path):
            print(f"Error: File not found at {file_path}")
            raise HTTPException(status_code=404, detail="File not found")
            
        return FileResponse(
            file_path,
            media_type="audio/mpeg",
            filename=os.path.basename(file_path)
        )
    except Exception as e:
        print(f"=== Download error: {str(e)} ===")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def healthcheck():
    return {"status": "healthy"}
