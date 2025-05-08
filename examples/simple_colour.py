import asyncio
import logging
from PIL import Image
import numpy as np

from dotenv import load_dotenv

from livekit import rtc
from livekit.agents import JobContext, WorkerOptions, cli

# Load environment variables
load_dotenv()

WIDTH = 640
HEIGHT = 480


async def entrypoint(job: JobContext):
    await job.connect()

    room = job.room
    source = rtc.VideoSource(WIDTH, HEIGHT)
    track = rtc.LocalVideoTrack.create_video_track("logo-display", source)
    options = rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_CAMERA)
    publication = await room.local_participant.publish_track(track, options)
    logging.info("published track", extra={"track_sid": publication.sid})

    async def _display_logo():
        # Load the image
        img = Image.open('assets/logo.png')
        # Resize image to match our dimensions
        img = img.resize((WIDTH, HEIGHT))
        # Convert to RGBA if it isn't already
        img = img.convert('RGBA')
        # Convert to bytes
        img_bytes = np.array(img).tobytes()
        
        # Create the frame once outside the loop
        frame = rtc.VideoFrame(WIDTH, HEIGHT, rtc.VideoBufferType.RGBA, img_bytes)
        
        try:
            while True:
                source.capture_frame(frame)
                await asyncio.sleep(0.1)  # 10 FPS is sufficient for a static image
        except asyncio.CancelledError:
            logging.info("Logo display task cancelled")
        except Exception as e:
            logging.error(f"Error in logo display: {e}")
            raise

    await _display_logo()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))