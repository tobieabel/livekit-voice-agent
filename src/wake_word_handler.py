# wake_word_handler.py
import re
import logging
from typing import AsyncIterable, Optional
from livekit import rtc
from livekit.agents import stt
from wav_player import WavPlayer

logger = logging.getLogger("wake-word-handler")

class WakeWordHandler:
    def __init__(self, wake_word: str = "computer", room: rtc.Room = None):
        self.wake_word = wake_word.lower()
        self.wake_word_detected = False
        self.room = room
        self.wav_player = WavPlayer()
        logger.info(f"Wake word handler initialized with wake word: '{wake_word}'")

    async def _play_wake_word_sound(self):
        """Play the wake word sound when state changes to false"""
        if self.room:
            try:
                await self.wav_player.play_once("assets/notification.wav", self.room)
            except Exception as e:
                logger.error(f"Error playing wake word sound: {e}")

    async def process_speech_events(
        self, 
        parent_stream: AsyncIterable[stt.SpeechEvent]
    ) -> AsyncIterable[stt.SpeechEvent]:
        """
        Process speech events and implement wake word detection.
        Only yields events if wake word is detected or was previously detected.
        """
        async for event in parent_stream:
            if hasattr(event, 'type') and str(event.type) == "SpeechEventType.FINAL_TRANSCRIPT" and event.alternatives:
                transcript = event.alternatives[0].text.lower()
                
                # Clean the transcript
                cleaned_transcript = re.sub(r'[^\w\s]', '', transcript)
                cleaned_transcript = ' '.join(cleaned_transcript.split())
                
                if not self.wake_word_detected:
                    # Check for wake word
                    if self.wake_word in cleaned_transcript:
                        logger.info(f"Wake word detected: '{self.wake_word}'")
                        self.wake_word_detected = True
                        logger.info(f"Wake word detected state changed to: {self.wake_word_detected}")
                        
                        # Extract content after wake word
                        content_after_wake_word = cleaned_transcript.split(self.wake_word, 1)[-1].strip()
                        if content_after_wake_word:
                            event.alternatives[0].text = content_after_wake_word
                            yield event
                else:
                    # Wake word already detected, process this utterance
                    yield event
                    
                    # Reset after end of speech
            elif hasattr(event, 'type') and str(event.type) == "SpeechEventType.END_OF_SPEECH" and self.wake_word_detected:
                logger.info("End of utterance detected, waiting for wake word again")
                self.wake_word_detected = False
                logger.info(f"Wake word detected state changed to: {self.wake_word_detected}")
                await self._play_wake_word_sound()
                yield event

            elif self.wake_word_detected:
                # Pass through other event types when wake word is active
                yield event

    def should_process_turn(self) -> bool:
        """Check if the current turn should be processed based on wake word detection."""
        return self.wake_word_detected

    def reset(self):
        """Reset the wake word detection state."""
        if self.wake_word_detected:  # Only log if there's an actual change
            self.wake_word_detected = False
            logger.info(f"Wake word detected state changed to: {self.wake_word_detected}")