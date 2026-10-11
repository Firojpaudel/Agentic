"""
Configuration and Provider Management for Agentic Systems.
Provides unified zero-cost LLM settings (Groq, Gemini, OpenRouter, Ollama)
used across all modules.
"""
from __future__ import annotations

import os
from enum import Enum
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from openai import OpenAI

# Automatically load .env if present
load_dotenv()


class ProviderType(str, Enum):
    GROQ = "groq"
    GEMINI = "gemini"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    MOCK = "mock"


class LLMConfig(BaseModel):
    """Configuration contract for model providers."""
    provider: ProviderType
    model: str
    base_url: str
    api_key: str = "EMPTY"
    temperature: float = 0.0
    max_tokens: Optional[int] = 2048


class Settings(BaseModel):
    """Unified application settings loading environment variables."""
    # Groq (Free tier)
    groq_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("GROQ_API_KEY"))
    groq_base_url: str = Field(default_factory=lambda: os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"))
    groq_model: str = Field(default_factory=lambda: os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b"))

    # Gemini (Google AI Studio Free tier)
    gemini_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY"))
    gemini_base_url: str = Field(default_factory=lambda: os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/"))
    gemini_model: str = Field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-2.0-flash"))

    # OpenRouter Free tier
    openrouter_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("OPENROUTER_API_KEY"))
    openrouter_base_url: str = Field(default_factory=lambda: os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"))
    openrouter_model: str = Field(default_factory=lambda: os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free"))

    # Ollama (Local zero-cost)
    ollama_base_url: str = Field(default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"))
    ollama_model: str = Field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b"))

    def get_llm_config(self, preferred_provider: Optional[str] = None) -> LLMConfig:
        """
        Resolve the best available zero-cost provider according to availability.
        Priority: Explicit -> Groq -> Gemini -> OpenRouter -> Ollama.
        """
        prov = (preferred_provider or "").lower()

        if prov == ProviderType.GROQ or (not preferred_provider and self.groq_api_key):
            return LLMConfig(
                provider=ProviderType.GROQ,
                model=self.groq_model,
                base_url=self.groq_base_url,
                api_key=self.groq_api_key or "EMPTY",
            )
        elif prov == ProviderType.GEMINI or (not preferred_provider and self.gemini_api_key):
            return LLMConfig(
                provider=ProviderType.GEMINI,
                model=self.gemini_model,
                base_url=self.gemini_base_url,
                api_key=self.gemini_api_key or "EMPTY",
            )
        elif prov == ProviderType.OPENROUTER or (not preferred_provider and self.openrouter_api_key):
            return LLMConfig(
                provider=ProviderType.OPENROUTER,
                model=self.openrouter_model,
                base_url=self.openrouter_base_url,
                api_key=self.openrouter_api_key or "EMPTY",
            )
        elif prov == ProviderType.OLLAMA or (not preferred_provider):
            return LLMConfig(
                provider=ProviderType.OLLAMA,
                model=self.ollama_model,
                base_url=self.ollama_base_url,
                api_key="ollama",
            )

        raise ValueError(f"Unknown or unconfigured provider: {preferred_provider}")

    def get_client(self, preferred_provider: Optional[str] = None) -> tuple[OpenAI, LLMConfig]:
        """Return an instantiated OpenAI client and its associated configuration."""
        config = self.get_llm_config(preferred_provider)
        client = OpenAI(
            base_url=config.base_url,
            api_key=config.api_key,
        )
        return client, config


# Global settings singleton
settings = Settings()
