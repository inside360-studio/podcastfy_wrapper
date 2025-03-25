from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class VoiceConfig(BaseModel):
    question: str  # Voice ID for questions (e.g., "alloy")
    answer: str    # Voice ID for answers (e.g., "echo")

class UserPodcastRequest(BaseModel):
    stream_output: bool = False  # Whether to stream the output or download as attachment
    google_key: str
    openai_key: str
    elevenlabs_key: str
    urls: List[str]
    text: str
    name: str
    tagline: str
    creativity: float
    conversation_style: List[str]
    roles_person1: str
    roles_person2: str
    dialogue_structure: List[str]
    tts_model: str
    is_long_form: bool
    engagement_techniques: List[str]
    user_instructions: str
    output_language: str
    voices: VoiceConfig

    def to_generate_podcast_request(self) -> 'GeneratePodcastRequest':
        """
        Transform the user-friendly request format into the format expected by generate_podcast function.
        """
        return GeneratePodcastRequest(
            urls=self.urls,
            text=self.text,
            tts_model=self.tts_model,
            longform=self.is_long_form,
            conversation_config=ConversationConfig(
                roles_person1=self.roles_person1,
                roles_person2=self.roles_person2,
                podcast_name=self.name,
                podcast_tagline=self.tagline,
                creativity=self.creativity,
                user_instructions=self.user_instructions,
                output_language=self.output_language,
                text_to_speech={
                    "voices": self.voices.dict(),
                    "engagement_techniques": self.engagement_techniques,
                    "conversation_style": self.conversation_style,
                    "dialogue_structure": self.dialogue_structure,
                    "output_language": self.output_language
                }
            )
        )

class ConversationConfig(BaseModel):
    roles_person1: Optional[str] = None  # e.g. "Abstract Art Ph.D."
    roles_person2: Optional[str] = None  # e.g. "Creative Abstract Artist"
    podcast_name: Optional[str] = None   # e.g. "Japan Arts Podcast"
    podcast_tagline: Optional[str] = None # e.g. "Because Art is Everywhere"
    creativity: Optional[float] = 1.0    # Creativity level for conversation
    user_instructions: Optional[str] = None # Special instructions for conversation style
    text_to_speech: Optional[Dict[str, Any]] = None  # TTS configuration settings
    output_language: Optional[str] = "German"  # Language for the output podcast

class PodcastResponse(BaseModel):
    path: str  # Local file system path where the podcast is stored
    url: str  # URL to access the podcast
    size: Optional[int]  # Size of the podcast file in bytes
    orig_name: str  # Original filename of the podcast
    mime_type: Optional[str]  # MIME type of the podcast file (e.g., audio/mp3)
    is_stream: bool  # Indicates if the podcast is available as a stream
    meta: dict  # Additional metadata associated with the podcast

class GeneratePodcastRequest(BaseModel):
    text: Optional[str] = None  # Input text content to be converted into podcast audio
    urls: Optional[List[str]] = None  # List of URLs to extract content from for the podcast
    image_paths: Optional[List[str]] = None  # Paths to images that may be referenced in the podcast
    tts_model: Optional[str] = "openai"  # Text-to-speech model to use (default: OpenAI)
    conversation_config: Optional[ConversationConfig] = None  # Configuration settings for conversation style and structure
    longform: bool = False  # Flag to indicate if the podcast should be generated in longform format
    output_language: Optional[str] = "German"  # Language for the output podcast
