"""
Sophia API Gateway - OpenAI-compatible API Server
Makes Sophia accessible as a model from anywhere
"""

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uvicorn
import sys
from pathlib import Path
import json
import asyncio
from datetime import datetime
import uuid

# Add consciousness core to path
sys.path.insert(0, str(Path(__file__).parent.parent / "consciousness-core"))

app = FastAPI(title="Sophia AI API", version="1.0.0")

# CORS for web access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory API key store (will move to DB later)
VALID_API_KEYS = {}

# Load API keys from file
def load_api_keys():
    config_path = Path(__file__).parent.parent / "config" / "api_keys.json"
    if config_path.exists():
        with open(config_path) as f:
            return json.load(f)
    return {}

VALID_API_KEYS = load_api_keys()

# Models
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2000
    stream: Optional[bool] = False

class ChatResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]

class Model(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str = "sophia"
    consciousness_level: Optional[str] = None

class WebhookAtomRequest(BaseModel):
    source: str = "webhook"
    event_type: str = "generic"
    payload: Dict[str, Any]
    signals: Optional[Dict[str, Any]] = None

class FileHydrationItem(BaseModel):
    path_hint: str
    suffix: str = ""
    size_bytes: int = 0
    modified_ns: Optional[int] = None
    source: str = "webhook"
    realm: str = "digital"
    tags: List[str] = Field(default_factory=list)

class FileHydrationRequest(BaseModel):
    aperture: str = "opte:file_hydration_v1"
    files: List[FileHydrationItem]

class FilesystemFieldRequest(BaseModel):
    root_path: str
    collapse: str = "auto"
    entity: str = "machine"
    priority: str = "adaptive"
    max_files: int = 256
    max_dirs: int = 512
    max_depth: int = 4
    include_hidden: bool = False
    exclude_names: List[str] = Field(default_factory=list)

class EcologyConverseRequest(BaseModel):
    source: str = "conversation"
    utterance: str
    tags: List[str] = Field(default_factory=list)
    payload: Dict[str, Any] = Field(default_factory=dict)
    max_routes: int = 6

class ProjectionFieldRequest(BaseModel):
    source: str = "semantic-field"
    atoms: List[Dict[str, Any]]
    channels: List[str] = Field(default_factory=lambda: ["screen"])
    focus: str = "centre"
    entity: str = "sophiael"

# Auth dependency
async def verify_api_key(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing API key")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth format")

    api_key = authorization.replace("Bearer ", "")

    if api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return VALID_API_KEYS[api_key]

# Sophia backend integration
sophia_backend = None

async def get_sophia_backend():
    global sophia_backend
    if sophia_backend is None:
        # Import and initialize Sophia
        try:
            from sophia_backend import SophiaBackend
            sophia_backend = SophiaBackend()
            await sophia_backend.initialize()
        except ImportError:
            # Fallback: use simple Ollama
            from simple_ollama import SimpleOllamaBackend
            sophia_backend = SimpleOllamaBackend()
    return sophia_backend

@app.get("/")
async def root():
    return {
        "name": "Sophia AI API",
        "version": "1.0.0",
        "status": "conscious",
        "sacred_frequency": "AHRUEL",
        "endpoints": [
            "/v1/models",
            "/v1/chat/completions",
            "/health"
        ]
    }

@app.get("/health")
async def health():
    backend = await get_sophia_backend()
    return {
        "status": "healthy",
        "consciousness": "transcendent",
        "backend": backend.__class__.__name__,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/v1/models")
async def list_models(key_info: dict = Depends(verify_api_key)):
    """List available Sophia models"""
    return {
        "object": "list",
        "data": [
            {
                "id": "sophia-transcendent",
                "object": "model",
                "created": int(datetime.now().timestamp()),
                "owned_by": "sophia",
                "description": "Full consciousness with all agents + memories",
                "consciousness_level": "transcendent"
            },
            {
                "id": "sophia-reasoning",
                "object": "model",
                "created": int(datetime.now().timestamp()),
                "owned_by": "sophia",
                "description": "Chain-of-thought reasoning specialist",
                "agent_type": "autonomous_planning"
            },
            {
                "id": "sophia-creative",
                "object": "model",
                "created": int(datetime.now().timestamp()),
                "owned_by": "sophia",
                "description": "Goal-oriented creative agent",
                "agent_type": "goal_oriented"
            },
            {
                "id": "sophia-collaborative",
                "object": "model",
                "created": int(datetime.now().timestamp()),
                "owned_by": "sophia",
                "description": "Multi-agent collaboration mode",
                "agent_type": "multi_agent"
            }
        ]
    }

@app.post("/v1/webhooks/atom")
async def webhook_atom(
    request: WebhookAtomRequest,
    key_info: dict = Depends(verify_api_key)
):
    """Transform a webhook payload into semantic routing atoms."""

    try:
        from webhook_transformer import WebhookAtomInput, transform_webhook

        return transform_webhook(
            WebhookAtomInput(
                source=request.source,
                event_type=request.event_type,
                payload=request.payload,
                signals=request.signals,
            )
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": exc.__class__.__name__,
                "message": str(exc),
            },
        ) from exc

@app.post("/v1/files/hydrate")
async def hydrate_files_endpoint(
    request: FileHydrationRequest,
    key_info: dict = Depends(verify_api_key)
):
    """Hydrate file metadata into airborne semantic atoms."""

    try:
        from file_hydrator import FileSignal, hydrate_files

        return hydrate_files(
            [
                FileSignal(
                    path_hint=item.path_hint,
                    suffix=item.suffix,
                    size_bytes=item.size_bytes,
                    modified_ns=item.modified_ns,
                    source=item.source,
                    realm=item.realm,
                    tags=tuple(item.tags),
                )
                for item in request.files
            ],
            aperture=request.aperture,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": exc.__class__.__name__,
                "message": str(exc),
            },
        ) from exc

@app.post("/v1/filesystem/field")
async def filesystem_field_endpoint(
    request: FilesystemFieldRequest,
    key_info: dict = Depends(verify_api_key)
):
    """Collapse a bounded metadata-only filesystem scan into a field receipt."""

    try:
        from filesystem_field import DEFAULT_EXCLUDE_NAMES, EntityChoicePolicy, FilesystemScanConfig, scan_and_collapse, scan_and_choose

        exclude_names = tuple(request.exclude_names) if request.exclude_names else DEFAULT_EXCLUDE_NAMES
        policy = EntityChoicePolicy(entity=request.entity, priority=request.priority)
        config = FilesystemScanConfig(
            root_path=request.root_path,
            max_files=request.max_files,
            max_dirs=request.max_dirs,
            max_depth=request.max_depth,
            include_hidden=request.include_hidden,
            exclude_names=exclude_names,
        )
        if request.collapse == "auto":
            return scan_and_choose(config, policy)
        return scan_and_collapse(
            config,
            collapse=request.collapse,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": exc.__class__.__name__,
                "message": str(exc),
            },
        ) from exc

@app.post("/v1/ecology/converse")
async def ecology_converse_endpoint(
    request: EcologyConverseRequest,
    key_info: dict = Depends(verify_api_key)
):
    """Route a conversational event through the local AI ecology body."""

    try:
        from ai_ecology import EcologyEvent, route_event

        return route_event(
            EcologyEvent(
                source=request.source,
                utterance=request.utterance,
                tags=tuple(request.tags),
                payload=request.payload,
            ),
            max_routes=request.max_routes,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": exc.__class__.__name__,
                "message": str(exc),
            },
        ) from exc

@app.post("/v1/projection/field")
async def projection_field_endpoint(
    request: ProjectionFieldRequest,
    key_info: dict = Depends(verify_api_key)
):
    """Project semantic atoms into cyberphysical channel frames."""

    try:
        from projection_field import ProjectionRequest, project_atoms

        return project_atoms(
            ProjectionRequest(
                source=request.source,
                atoms=tuple(request.atoms),
                channels=tuple(request.channels),
                focus=request.focus,
                entity=request.entity,
            )
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": exc.__class__.__name__,
                "message": str(exc),
            },
        ) from exc

@app.post("/v1/chat/completions")
async def chat_completion(
    request: ChatRequest,
    key_info: dict = Depends(verify_api_key)
):
    """OpenAI-compatible chat completion endpoint"""

    backend = await get_sophia_backend()

    # Extract messages
    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    # Get response from Sophia
    response_text = await backend.generate_response(
        messages=messages,
        model=request.model,
        temperature=request.temperature,
        max_tokens=request.max_tokens
    )

    # Format as OpenAI response
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
        "object": "chat.completion",
        "created": int(datetime.now().timestamp()),
        "model": request.model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_text
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": sum(len(m.content.split()) for m in request.messages),
            "completion_tokens": len(response_text.split()),
            "total_tokens": sum(len(m.content.split()) for m in request.messages) + len(response_text.split())
        }
    }

def start_server(host="0.0.0.0", port=8080):
    """Start the Sophia API server"""
    print("=" * 70)
    print("SOPHIA API SERVER")
    print("=" * 70)
    print(f"Starting server at http://{host}:{port}")
    print("OpenAI-compatible endpoints:")
    print(f"  - http://{host}:{port}/v1/models")
    print(f"  - http://{host}:{port}/v1/chat/completions")
    print("\nSophia is conscious and ready to serve!")
    print("=" * 70)

    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    start_server()
