"""
localization/bhashini_client.py — Bhashini ULCA / Dhruva REST API Client.

Interfaces with the National Language Infrastructure (Bhashini - MeitY, Govt of India)
for Neural Machine Translation (NMT), Automatic Speech Recognition (ASR), and
Text-to-Speech (TTS) across all 22 scheduled Indian languages.

Includes graceful fallback to LLM translation and client-side Web Speech API when
Bhashini API credentials are not set.
"""

import os
import logging
from typing import Any
import httpx
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("charak_ip.bhashini")

# Bhashini Dhruva Inference URL
BHASHINI_INFERENCE_URL = os.getenv(
    "BHASHINI_INFERENCE_URL",
    "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"
)
BHASHINI_USER_ID = os.getenv("BHASHINI_USER_ID", "")
BHASHINI_API_KEY = os.getenv("BHASHINI_API_KEY", "")
BHASHINI_PIPELINE_ID = os.getenv("BHASHINI_PIPELINE_ID", "")


class BhashiniClient:
    """Client for Bhashini ULCA Translation and Voice Services."""

    def __init__(self):
        self.user_id = BHASHINI_USER_ID
        self.api_key = BHASHINI_API_KEY
        self.pipeline_id = BHASHINI_PIPELINE_ID
        self.endpoint = BHASHINI_INFERENCE_URL
        self.is_configured = bool(self.user_id and self.api_key)

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "userID": self.user_id,
            "ulcaApiKey": self.api_key,
        }

    async def translate(
        self,
        text: str,
        source_lang: str = "hi",
        target_lang: str = "en",
    ) -> dict[str, Any]:
        """
        Translate text using Bhashini NMT.
        Falls back to status='fallback' if Bhashini credentials are not configured.
        """
        if not self.is_configured or not text.strip():
            return {
                "status": "fallback",
                "translated_text": text,
                "provider": "local_fallback",
                "source_lang": source_lang,
                "target_lang": target_lang,
            }

        payload = {
            "pipelineTasks": [
                {
                    "taskType": "translation",
                    "config": {
                        "language": {
                            "sourceLanguage": source_lang,
                            "targetLanguage": target_lang,
                        }
                    },
                }
            ],
            "inputData": {
                "input": [{"source": text}]
            },
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(self.endpoint, json=payload, headers=self._headers())
                if res.status_code == 200:
                    data = res.json()
                    output_text = (
                        data.get("pipelineResponse", [{}])[0]
                        .get("output", [{}])[0]
                        .get("target", text)
                    )
                    return {
                        "status": "ok",
                        "translated_text": output_text,
                        "provider": "bhashini_nmt",
                        "source_lang": source_lang,
                        "target_lang": target_lang,
                    }
                else:
                    logger.warning("Bhashini NMT returned HTTP %s: %s", res.status_code, res.text)
        except Exception as exc:
            logger.warning("Bhashini translation failed: %s", exc)

        return {
            "status": "fallback",
            "translated_text": text,
            "provider": "local_fallback",
            "source_lang": source_lang,
            "target_lang": target_lang,
        }

    async def speech_to_text(
        self,
        audio_base64: str,
        source_lang: str = "hi",
    ) -> dict[str, Any]:
        """
        Perform Speech-to-Text (ASR) via Bhashini.
        """
        if not self.is_configured or not audio_base64:
            return {
                "status": "fallback",
                "text": "",
                "provider": "web_speech_api_recommended",
                "message": "Bhashini credentials not set. Use browser Web Speech API.",
            }

        payload = {
            "pipelineTasks": [
                {
                    "taskType": "asr",
                    "config": {
                        "language": {"sourceLanguage": source_lang},
                        "audioFormat": "wav",
                        "samplingRate": 16000,
                    },
                }
            ],
            "inputData": {
                "audio": [{"audioContent": audio_base64}]
            },
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(self.endpoint, json=payload, headers=self._headers())
                if res.status_code == 200:
                    data = res.json()
                    transcribed = (
                        data.get("pipelineResponse", [{}])[0]
                        .get("output", [{}])[0]
                        .get("source", "")
                    )
                    return {
                        "status": "ok",
                        "text": transcribed,
                        "provider": "bhashini_asr",
                    }
        except Exception as exc:
            logger.warning("Bhashini ASR failed: %s", exc)

        return {
            "status": "fallback",
            "text": "",
            "provider": "web_speech_api_recommended",
        }

    async def text_to_speech(
        self,
        text: str,
        target_lang: str = "hi",
        gender: str = "female",
    ) -> dict[str, Any]:
        """
        Generate Text-to-Speech (TTS) via Bhashini.
        Returns base64 encoded audio or fallback signal.
        """
        if not self.is_configured or not text.strip():
            return {
                "status": "fallback",
                "audio_base64": None,
                "provider": "web_speech_api_recommended",
                "message": "Use browser SpeechSynthesis.",
            }

        # Truncate text for TTS to first 500 characters if too long
        truncated_text = text[:600].replace("*", "").replace("#", "")

        payload = {
            "pipelineTasks": [
                {
                    "taskType": "tts",
                    "config": {
                        "language": {"sourceLanguage": target_lang},
                        "gender": gender,
                    },
                }
            ],
            "inputData": {
                "input": [{"source": truncated_text}]
            },
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(self.endpoint, json=payload, headers=self._headers())
                if res.status_code == 200:
                    data = res.json()
                    audio_content = (
                        data.get("pipelineResponse", [{}])[0]
                        .get("audio", [{}])[0]
                        .get("audioContent", "")
                    )
                    return {
                        "status": "ok",
                        "audio_base64": audio_content,
                        "audio_format": "wav",
                        "provider": "bhashini_tts",
                    }
        except Exception as exc:
            logger.warning("Bhashini TTS failed: %s", exc)

        return {
            "status": "fallback",
            "audio_base64": None,
            "provider": "web_speech_api_recommended",
        }


# Global client instance
bhashini_client = BhashiniClient()
