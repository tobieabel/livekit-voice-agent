# Livekit Voice Agent

A voice agent implementation using Livekit for real-time voice interactions. This project demonstrates how to create a voice-enabled agent that can respond to wake words and engage in conversations.

## Features

- Wake word detection
- Real-time voice interactions
- Livekit integration
- OpenAI integration for LLM and TTS
- Deepgram integration for STT
- Silero VAD for voice activity detection

## Prerequisites

- Python 3.8+
- Livekit account and API credentials
- OpenAI API key
- Deepgram API key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/tobieabel/livekit-voice-agent.git
cd livekit-voice-agent
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy `.env.example` to `.env` and fill in your API keys:
```bash
cp .env.example .env
```

## Usage

Run the simple voice agent:
```bash
python src/simple_voice_agent.py
```

## Project Structure

- `src/`: Main source code
  - `simple_voice_agent.py`: Main agent implementation
  - `wake_word_handler.py`: Wake word detection
  - `prompts.py`: System prompts and messages
  - `wav_player.py`: Audio utilities
- `assets/`: Static assets
  - `logo.png`: Agent logo
  - `notification.wav`: Audio notifications
- `examples/`: Example implementations

## License

MIT License 