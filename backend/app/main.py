"""FastAPI application for AI Voice Conversation System."""

import logging
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional

from .conversation_manager import ConversationManager
from .clients.asr_client import ASRClient
from .clients.llm_client import LLMClient
from .clients.tts_client import TTSClient
from .stream_processor import StreamProcessor
from .config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Voice Conversation API",
    description="Real-time AI voice conversation system",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize clients
asr_client = ASRClient()
llm_client = LLMClient()
tts_client = TTSClient()

# Initialize conversation manager
conversation_manager = ConversationManager(
    asr_client=asr_client,
    llm_client=llm_client,
    tts_client=tts_client
)

logger.info("Application initialized")
logger.info(f"Config: {config.get_masked_config()}")

# Mount frontend static files
frontend_path = Path(__file__).parent.parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
    logger.info(f"Serving frontend from: {frontend_path}")


@app.get("/")
async def root():
    """Redirect to frontend."""
    from fastapi.responses import FileResponse
    index_path = frontend_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "AI Voice Conversation API", "docs": "/docs"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "ai-voice-conversation",
        "version": "1.0.0"
    }


@app.post("/api/conversation/start")
async def start_conversation(
    initial_prompt: Optional[str] = None
):
    """
    Start a new conversation session.
    
    Args:
        initial_prompt: Optional custom initial greeting
        
    Returns:
        Session ID and initial greeting
    """
    try:
        # Create new session
        session_id = conversation_manager.create_session()
        
        logger.info(f"Started conversation: {session_id}")
        
        return {
            "session_id": session_id,
            "message": "Conversation started. Use /api/conversation/stream to receive events."
        }
        
    except Exception as e:
        logger.error(f"Error starting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/conversation/audio")
async def upload_audio(
    session_id: str = Query(..., description="Session ID"),
    file: UploadFile = File(..., description="Audio file")
):
    """
    Upload audio file for processing.
    
    Args:
        session_id: Conversation session ID
        file: Audio file (webm format)
        
    Returns:
        Confirmation message
    """
    try:
        # Validate session
        conversation_manager.get_session(session_id)
        
        # Read audio data
        audio_data = await file.read()
        
        logger.info(f"Received audio for session {session_id}: {len(audio_data)} bytes")
        
        return {
            "session_id": session_id,
            "message": "Audio received. Processing will be streamed via /api/conversation/stream"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error uploading audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/conversation/stream")
async def stream_conversation(
    session_id: str = Query(..., description="Session ID"),
    action: str = Query("start", description="Action: 'start' or 'process'"),
    audio_file: Optional[str] = None
):
    """
    Stream conversation events (SSE endpoint).
    
    Args:
        session_id: Conversation session ID
        action: Action to perform ('start' for initial greeting, 'process' for audio)
        audio_file: Path to audio file (for testing)
        
    Returns:
        Server-Sent Events stream
    """
    try:
        # Validate session
        conversation_manager.get_session(session_id)
        
        async def event_generator():
            try:
                if action == "start":
                    # Start conversation with greeting
                    events = conversation_manager.start_conversation(session_id)
                else:
                    # This endpoint doesn't handle audio processing directly
                    # Audio should be uploaded via POST /api/conversation/audio first
                    raise ValueError("Use POST /api/conversation/audio to upload audio")
                
                # Stream events
                async for event_str in StreamProcessor.event_stream(events):
                    yield event_str
                    
            except Exception as e:
                logger.error(f"Error in event stream: {e}")
                # Send error event
                yield f"event: error\ndata: {{\"message\": \"{str(e)}\"}}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in stream endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/conversation/process")
async def process_audio_stream(
    session_id: str = Query(..., description="Session ID"),
    file: UploadFile = File(..., description="Audio file")
):
    """
    Process audio and stream results (combined endpoint).
    
    Args:
        session_id: Conversation session ID
        file: Audio file (webm format)
        
    Returns:
        Server-Sent Events stream with processing results
    """
    try:
        # Validate session
        conversation_manager.get_session(session_id)
        
        # Read audio data
        audio_data = await file.read()
        
        logger.info(f"Processing audio for session {session_id}: {len(audio_data)} bytes")
        
        async def event_generator():
            try:
                # Process audio through pipeline
                events = conversation_manager.process_audio(session_id, audio_data)
                
                # Stream events
                async for event_str in StreamProcessor.event_stream(events):
                    yield event_str
                    
            except Exception as e:
                logger.error(f"Error processing audio: {e}")
                yield f"event: error\ndata: {{\"message\": \"{str(e)}\"}}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in process endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/conversation/history")
async def get_history(
    session_id: str = Query(..., description="Session ID")
):
    """
    Get conversation history.
    
    Args:
        session_id: Conversation session ID
        
    Returns:
        List of messages
    """
    try:
        history = conversation_manager.get_conversation_history(session_id)
        return {"session_id": session_id, "messages": history}
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
