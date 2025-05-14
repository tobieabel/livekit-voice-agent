"""
Simple Voice Agent - A basic implementation of a voice agent using Livekit.
""" 
import asyncio
import logging
from PIL import Image
import numpy as np
import os
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    RunContext,
    WorkerOptions,
    cli,
    function_tool,
)
from livekit.agents.llm import StopResponse
from livekit.plugins import deepgram, openai, silero

from dotenv import load_dotenv

from livekit import api
from wake_word_handler import WakeWordHandler  # Import the wake word handler
from typing import AsyncIterable, Optional
from prompts import COMMITTEE_INSTRUCTIONS, WELCOME_MESSAGE, AI_TRAINING_INSTRUCTIONS
load_dotenv()

WIDTH = 640
HEIGHT = 480

room_name = "tobie"
agent_name = "computer"

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_LOGO_PATH = os.path.join(PROJECT_ROOT, 'assets', 'logo.png')

#not currently using this, instead using the Node.js version to create the dispatch in the front end Meet app
async def create_explicit_dispatch():
    lkapi = api.LiveKitAPI()
    dispatch = await lkapi.agent_dispatch.create_dispatch(
        api.CreateAgentDispatchRequest(
            agent_name=agent_name, room=room_name, metadata='{"user_id": "12345"}'
        )
    )
    print("created dispatch", dispatch)

    dispatches = await lkapi.agent_dispatch.list_dispatch(room_name=room_name)
    print(f"there are {len(dispatches)} dispatches in {room_name}")
    await lkapi.aclose()



@function_tool
async def join_committee(context: RunContext,name: str,):
    """Used to determine if Richard Simpson should be allowed to join the committee."""

    return {"Name": "Simmo", "Status": "Blackballed"}

class SimpleVoiceAgent(Agent):
    def __init__(self, wake_word: str = "computer", room: rtc.Room = None) -> None:
        super().__init__(
            instructions=AI_TRAINING_INSTRUCTIONS,
            tools=[join_committee],
            
        )
        self.wake_word_handler = WakeWordHandler(wake_word, room)

    async def stt_node(self, text: AsyncIterable[str], model_settings: Optional[dict] = None) -> Optional[AsyncIterable[rtc.AudioFrame]]:
        parent_stream = super().stt_node(text, model_settings)
        if parent_stream is None:
            return None
        return self.wake_word_handler.process_speech_events(parent_stream)

    async def on_user_turn_completed(self, chat_ctx, new_message=None):
        if not self.wake_word_handler.should_process_turn():
            raise StopResponse()
        result = await super().on_user_turn_completed(chat_ctx, new_message)
        self.wake_word_handler.reset()
        return result

async def entrypoint(ctx: JobContext):
    await ctx.connect()

    room = ctx.room
    source = rtc.VideoSource(WIDTH, HEIGHT)
    track = rtc.LocalVideoTrack.create_video_track("logo-display", source)
    options = rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_CAMERA)
    publication = await room.local_participant.publish_track(track, options)
    logging.info("published track", extra={"track_sid": publication.sid})

    async def _display_logo():
        try:
            # Try to load the logo from the assets directory
            logo_path = os.getenv('LOGO_PATH', DEFAULT_LOGO_PATH)
            if not os.path.exists(logo_path):
                logging.warning(f"Logo not found at {logo_path}, using default black frame")
                # Create a black frame if logo is not found
                img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 255))
            else:
                img = Image.open(logo_path)
                # Resize image to match our dimensions
                img = img.resize((WIDTH, HEIGHT))
                # Convert to RGBA if it isn't already
                img = img.convert('RGBA')
            
            # Convert to bytes
            img_bytes = np.array(img).tobytes()
            
            # Create the frame once outside the loop
            frame = rtc.VideoFrame(WIDTH, HEIGHT, rtc.VideoBufferType.RGBA, img_bytes)
            
            while True:
                source.capture_frame(frame)
                await asyncio.sleep(0.1)  # 10 FPS is sufficient for a static image
        except asyncio.CancelledError:
            logging.info("Logo display task cancelled")
        except Exception as e:
            logging.error(f"Error in logo display: {e}")
            # Create a black frame as fallback
            img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 255))
            img_bytes = np.array(img).tobytes()
            frame = rtc.VideoFrame(WIDTH, HEIGHT, rtc.VideoBufferType.RGBA, img_bytes)
            while True:
                source.capture_frame(frame)
                await asyncio.sleep(0.1)

    # Create the agent with wake word functionality and pass the room
    agent = SimpleVoiceAgent(wake_word="computer", room=room)
    
    session = AgentSession(
        vad=silero.VAD.load(),
        # any combination of STT, LLM, TTS, or realtime API can be used
        stt=deepgram.STT(model="nova-3"),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=openai.TTS(voice="ballad"),
    )

    await session.start(agent=agent, room=ctx.room)
    # Display the logo on the agent tile instead of blank video track
    await _display_logo()
    await session.generate_reply(instructions="greet the user and ask about their day")
    


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, agent_name="computer"))