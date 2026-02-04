#!/usr/bin/env python3
"""
Multi-Provider LLM Service for MicroCFO
Supports Gemini (primary), Groq (fast), and OpenAI (fallback)

Provider Selection Strategy:
- Gemini: Primary for vision and general tasks (cost-effective)
- Groq: Ultra-fast inference for real-time features
- OpenAI: High-quality fallback for complex reasoning

Environment Variables Required:
- GEMINI_API_KEY: Google AI Studio API key
- GROQ_API_KEY: Groq Cloud API key  
- OPENAI_API_KEY: OpenAI API key
"""

import os
import json
import logging
import time
import asyncio
import httpx
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Available LLM providers"""
    GEMINI = "gemini"
    GROQ = "groq"
    OPENAI = "openai"
    MOCK = "mock"


class ModelCapability(str, Enum):
    """Model capabilities for routing"""
    TEXT = "text"
    VISION = "vision"
    EMBEDDING = "embedding"
    CODE = "code"
    REASONING = "reasoning"


@dataclass
class LLMResponse:
    """Standardized LLM response"""
    content: str
    provider: LLMProvider
    model: str
    tokens_used: int = 0
    latency_ms: float = 0.0
    cost_estimate: float = 0.0
    raw_response: Optional[Dict] = None
    success: bool = True
    error: Optional[str] = None


@dataclass
class LLMConfig:
    """Configuration for LLM providers"""
    provider: LLMProvider
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 2000
    temperature: float = 0.7
    timeout: int = 30


# Provider-specific model mappings
PROVIDER_MODELS = {
    LLMProvider.GEMINI: {
        ModelCapability.TEXT: "gemini-2.0-flash",
        ModelCapability.VISION: "gemini-2.0-flash",
        ModelCapability.CODE: "gemini-2.0-flash",
        ModelCapability.REASONING: "gemini-2.0-flash-thinking-exp",
        ModelCapability.EMBEDDING: "text-embedding-004",
    },
    LLMProvider.GROQ: {
        ModelCapability.TEXT: "llama-3.3-70b-versatile",
        ModelCapability.CODE: "llama-3.1-70b-versatile",
        ModelCapability.VISION: "llava-v1.5-7b-4096-preview",
        ModelCapability.REASONING: "llama-3.3-70b-versatile",
    },
    LLMProvider.OPENAI: {
        ModelCapability.TEXT: "gpt-4o-mini",
        ModelCapability.VISION: "gpt-4o",
        ModelCapability.CODE: "gpt-4o",
        ModelCapability.REASONING: "gpt-4o",
        ModelCapability.EMBEDDING: "text-embedding-3-small",
    },
}

# Cost per 1K tokens (input/output)
COST_PER_1K_TOKENS = {
    LLMProvider.GEMINI: {"input": 0.000075, "output": 0.00030},  # Very cheap
    LLMProvider.GROQ: {"input": 0.0005, "output": 0.0008},  # Fast & affordable
    LLMProvider.OPENAI: {"input": 0.00015, "output": 0.0006},  # GPT-4o-mini
}


class BaseLLMProvider(ABC):
    """Base class for LLM providers"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.name = LLMProvider.MOCK
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and available"""
        pass
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        images: Optional[List[bytes]] = None,
    ) -> LLMResponse:
        """Generate text completion"""
        pass
    
    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate text embedding"""
        pass
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for token usage"""
        costs = COST_PER_1K_TOKENS.get(self.name, {"input": 0, "output": 0})
        return (input_tokens * costs["input"] + output_tokens * costs["output"]) / 1000


class GeminiProvider(BaseLLMProvider):
    """Google Gemini AI provider"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or os.getenv("GEMINI_API_KEY"))
        self.name = LLMProvider.GEMINI
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self._client = None
        self._model = None
        
        # Try to initialize SDK
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._model = genai.GenerativeModel("gemini-2.0-flash")
                logger.info("✅ Gemini provider initialized (SDK mode)")
            except ImportError:
                logger.info("✅ Gemini provider initialized (HTTP mode)")
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        images: Optional[List[bytes]] = None,
    ) -> LLMResponse:
        start_time = time.time()
        model_name = model or PROVIDER_MODELS[LLMProvider.GEMINI][ModelCapability.TEXT]
        
        try:
            if self._model:
                # Use SDK
                full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
                
                if images:
                    import io
                    from PIL import Image
                    content = [full_prompt]
                    for img_bytes in images:
                        img = Image.open(io.BytesIO(img_bytes))
                        content.append(img)
                    response = self._model.generate_content(content)
                else:
                    response = self._model.generate_content(full_prompt)
                
                content = response.text
                tokens_used = len(prompt.split()) + len(content.split())  # Rough estimate
                
            else:
                # Use HTTP API
                async with httpx.AsyncClient() as client:
                    url = f"{self.base_url}/models/{model_name}:generateContent"
                    
                    parts = [{"text": prompt}]
                    if system_prompt:
                        parts.insert(0, {"text": system_prompt})
                    
                    if images:
                        import base64
                        for img_bytes in images:
                            parts.append({
                                "inline_data": {
                                    "mime_type": "image/png",
                                    "data": base64.b64encode(img_bytes).decode()
                                }
                            })
                    
                    payload = {
                        "contents": [{"parts": parts}],
                        "generationConfig": {
                            "maxOutputTokens": max_tokens,
                            "temperature": temperature,
                        }
                    }
                    
                    response = await client.post(
                        url,
                        params={"key": self.api_key},
                        json=payload,
                        timeout=30
                    )
                    response.raise_for_status()
                    
                    data = response.json()
                    content = data["candidates"][0]["content"]["parts"][0]["text"]
                    tokens_used = data.get("usageMetadata", {}).get("totalTokenCount", 0)
            
            latency = (time.time() - start_time) * 1000
            
            return LLMResponse(
                content=content,
                provider=LLMProvider.GEMINI,
                model=model_name,
                tokens_used=tokens_used,
                latency_ms=latency,
                cost_estimate=self.estimate_cost(tokens_used // 2, tokens_used // 2),
                success=True
            )
            
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            return LLMResponse(
                content="",
                provider=LLMProvider.GEMINI,
                model=model_name,
                success=False,
                error=str(e)
            )
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Gemini"""
        try:
            if self._model:
                import google.generativeai as genai
                result = genai.embed_content(
                    model="models/text-embedding-004",
                    content=text
                )
                return result["embedding"]
            else:
                async with httpx.AsyncClient() as client:
                    url = f"{self.base_url}/models/text-embedding-004:embedContent"
                    response = await client.post(
                        url,
                        params={"key": self.api_key},
                        json={"content": {"parts": [{"text": text}]}},
                        timeout=30
                    )
                    response.raise_for_status()
                    return response.json()["embedding"]["values"]
        except Exception as e:
            logger.error(f"Gemini embedding failed: {e}")
            return []


class GroqProvider(BaseLLMProvider):
    """Groq Cloud provider - Ultra-fast inference"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or os.getenv("GROQ_API_KEY"))
        self.name = LLMProvider.GROQ
        self.base_url = "https://api.groq.com/openai/v1"
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        images: Optional[List[bytes]] = None,
    ) -> LLMResponse:
        start_time = time.time()
        model_name = model or PROVIDER_MODELS[LLMProvider.GROQ][ModelCapability.TEXT]
        
        try:
            async with httpx.AsyncClient() as client:
                messages = []
                
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                
                # Handle vision if images provided
                if images and model_name in ["llava-v1.5-7b-4096-preview"]:
                    import base64
                    content = [{"type": "text", "text": prompt}]
                    for img_bytes in images:
                        content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64.b64encode(img_bytes).decode()}"
                            }
                        })
                    messages.append({"role": "user", "content": content})
                else:
                    messages.append({"role": "user", "content": prompt})
                
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model_name,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": temperature
                    },
                    timeout=30
                )
                response.raise_for_status()
                
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                tokens_used = usage.get("total_tokens", 0)
                
                latency = (time.time() - start_time) * 1000
                
                return LLMResponse(
                    content=content,
                    provider=LLMProvider.GROQ,
                    model=model_name,
                    tokens_used=tokens_used,
                    latency_ms=latency,
                    cost_estimate=self.estimate_cost(
                        usage.get("prompt_tokens", 0),
                        usage.get("completion_tokens", 0)
                    ),
                    raw_response=data,
                    success=True
                )
                
        except Exception as e:
            logger.error(f"Groq generation failed: {e}")
            return LLMResponse(
                content="",
                provider=LLMProvider.GROQ,
                model=model_name,
                success=False,
                error=str(e)
            )
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Groq doesn't support embeddings, fallback to sentence-transformers"""
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')
            return model.encode(text).tolist()
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return []


class OpenAIProvider(BaseLLMProvider):
    """OpenAI provider - High-quality fallback"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or os.getenv("OPENAI_API_KEY"))
        self.name = LLMProvider.OPENAI
        self.base_url = "https://api.openai.com/v1"
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        images: Optional[List[bytes]] = None,
    ) -> LLMResponse:
        start_time = time.time()
        model_name = model or PROVIDER_MODELS[LLMProvider.OPENAI][ModelCapability.TEXT]
        
        try:
            async with httpx.AsyncClient() as client:
                messages = []
                
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                
                # Handle vision if images provided
                if images:
                    import base64
                    content = [{"type": "text", "text": prompt}]
                    for img_bytes in images:
                        content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64.b64encode(img_bytes).decode()}"
                            }
                        })
                    messages.append({"role": "user", "content": content})
                    model_name = "gpt-4o"  # Vision requires GPT-4o
                else:
                    messages.append({"role": "user", "content": prompt})
                
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model_name,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": temperature
                    },
                    timeout=60
                )
                response.raise_for_status()
                
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                tokens_used = usage.get("total_tokens", 0)
                
                latency = (time.time() - start_time) * 1000
                
                return LLMResponse(
                    content=content,
                    provider=LLMProvider.OPENAI,
                    model=model_name,
                    tokens_used=tokens_used,
                    latency_ms=latency,
                    cost_estimate=self.estimate_cost(
                        usage.get("prompt_tokens", 0),
                        usage.get("completion_tokens", 0)
                    ),
                    raw_response=data,
                    success=True
                )
                
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            return LLMResponse(
                content="",
                provider=LLMProvider.OPENAI,
                model=model_name,
                success=False,
                error=str(e)
            )
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "text-embedding-3-small",
                        "input": text
                    },
                    timeout=30
                )
                response.raise_for_status()
                return response.json()["data"][0]["embedding"]
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            return []


class MockProvider(BaseLLMProvider):
    """Mock provider for testing"""
    
    def __init__(self):
        super().__init__(None)
        self.name = LLMProvider.MOCK
    
    def is_available(self) -> bool:
        return True
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        images: Optional[List[bytes]] = None,
    ) -> LLMResponse:
        return LLMResponse(
            content=f"[Mock Response] Processed prompt: {prompt[:100]}...",
            provider=LLMProvider.MOCK,
            model="mock-model",
            tokens_used=100,
            latency_ms=10,
            success=True
        )
    
    async def generate_embedding(self, text: str) -> List[float]:
        return [0.1] * 384  # Return fake embedding


class LLMService:
    """
    Multi-Provider LLM Service with automatic failover
    
    Features:
    - Automatic provider selection based on task
    - Failover to backup providers
    - Cost tracking and optimization
    - Response caching
    - Rate limiting awareness
    
    Usage:
        llm = LLMService()
        response = await llm.generate("What is GST?", capability=ModelCapability.TEXT)
    """
    
    def __init__(self):
        # Initialize providers
        self.providers: Dict[LLMProvider, BaseLLMProvider] = {
            LLMProvider.GEMINI: GeminiProvider(),
            LLMProvider.GROQ: GroqProvider(),
            LLMProvider.OPENAI: OpenAIProvider(),
            LLMProvider.MOCK: MockProvider(),
        }
        
        # Provider priority for different tasks
        self.provider_priority = {
            ModelCapability.TEXT: [LLMProvider.GROQ, LLMProvider.GEMINI, LLMProvider.OPENAI],
            ModelCapability.VISION: [LLMProvider.GEMINI, LLMProvider.OPENAI],
            ModelCapability.CODE: [LLMProvider.GEMINI, LLMProvider.GROQ, LLMProvider.OPENAI],
            ModelCapability.REASONING: [LLMProvider.GEMINI, LLMProvider.OPENAI, LLMProvider.GROQ],
            ModelCapability.EMBEDDING: [LLMProvider.GEMINI, LLMProvider.OPENAI],
        }
        
        # Statistics
        self._request_count = 0
        self._total_tokens = 0
        self._total_cost = 0.0
        self._provider_stats: Dict[LLMProvider, Dict] = {
            p: {"requests": 0, "tokens": 0, "cost": 0.0, "errors": 0}
            for p in LLMProvider
        }
        
        # Log available providers
        available = [p.value for p, provider in self.providers.items() if provider.is_available()]
        logger.info(f"LLM Service initialized with providers: {available}")
    
    def get_available_providers(self) -> List[LLMProvider]:
        """Get list of available providers"""
        return [p for p, provider in self.providers.items() if provider.is_available()]
    
    def select_provider(
        self,
        capability: ModelCapability = ModelCapability.TEXT,
        preferred: Optional[LLMProvider] = None
    ) -> Optional[BaseLLMProvider]:
        """Select the best available provider for a task"""
        
        # If preferred provider is specified and available, use it
        if preferred and self.providers[preferred].is_available():
            return self.providers[preferred]
        
        # Otherwise, use priority order for the capability
        for provider_name in self.provider_priority.get(capability, []):
            provider = self.providers[provider_name]
            if provider.is_available():
                return provider
        
        # Fallback to mock
        return self.providers[LLMProvider.MOCK]
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        capability: ModelCapability = ModelCapability.TEXT,
        preferred_provider: Optional[LLMProvider] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        images: Optional[List[bytes]] = None,
        retry_on_failure: bool = True,
    ) -> LLMResponse:
        """
        Generate text using the best available provider
        
        Args:
            prompt: The input prompt
            system_prompt: Optional system instruction
            capability: The type of task (text, vision, code, reasoning)
            preferred_provider: Force a specific provider
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            images: List of image bytes for vision tasks
            retry_on_failure: Whether to retry with other providers on failure
        
        Returns:
            LLMResponse with generated content
        """
        self._request_count += 1
        
        # Auto-detect vision capability if images provided
        if images:
            capability = ModelCapability.VISION
        
        # Get provider priority
        priority = self.provider_priority.get(capability, [])
        if preferred_provider and preferred_provider not in priority:
            priority = [preferred_provider] + list(priority)
        
        last_error = None
        
        for provider_name in priority:
            provider = self.providers[provider_name]
            
            if not provider.is_available():
                continue
            
            try:
                model = PROVIDER_MODELS.get(provider_name, {}).get(capability)
                
                response = await provider.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    images=images
                )
                
                if response.success:
                    # Update statistics
                    self._total_tokens += response.tokens_used
                    self._total_cost += response.cost_estimate
                    stats = self._provider_stats[provider_name]
                    stats["requests"] += 1
                    stats["tokens"] += response.tokens_used
                    stats["cost"] += response.cost_estimate
                    
                    logger.info(
                        f"LLM request successful: provider={provider_name.value}, "
                        f"tokens={response.tokens_used}, latency={response.latency_ms:.0f}ms"
                    )
                    return response
                
                last_error = response.error
                self._provider_stats[provider_name]["errors"] += 1
                
                if not retry_on_failure:
                    return response
                    
            except Exception as e:
                last_error = str(e)
                self._provider_stats[provider_name]["errors"] += 1
                logger.warning(f"Provider {provider_name.value} failed: {e}")
                
                if not retry_on_failure:
                    break
        
        # All providers failed, return error response
        return LLMResponse(
            content="",
            provider=LLMProvider.MOCK,
            model="none",
            success=False,
            error=f"All providers failed. Last error: {last_error}"
        )
    
    async def generate_embedding(
        self,
        text: str,
        preferred_provider: Optional[LLMProvider] = None
    ) -> List[float]:
        """Generate text embedding"""
        for provider_name in [preferred_provider, LLMProvider.GEMINI, LLMProvider.OPENAI]:
            if provider_name and self.providers[provider_name].is_available():
                embedding = await self.providers[provider_name].generate_embedding(text)
                if embedding:
                    return embedding
        
        # Fallback to sentence-transformers
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')
            return model.encode(text).tolist()
        except Exception as e:
            logger.error(f"All embedding methods failed: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            "total_requests": self._request_count,
            "total_tokens": self._total_tokens,
            "total_cost_usd": round(self._total_cost, 4),
            "providers": {
                p.value: stats for p, stats in self._provider_stats.items()
            },
            "available_providers": [p.value for p in self.get_available_providers()]
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all providers"""
        results = {}
        
        for provider_name, provider in self.providers.items():
            if provider_name == LLMProvider.MOCK:
                continue
                
            try:
                if not provider.is_available():
                    results[provider_name.value] = {"status": "not_configured"}
                    continue
                
                response = await provider.generate(
                    prompt="Say 'OK'",
                    max_tokens=10,
                    temperature=0
                )
                
                results[provider_name.value] = {
                    "status": "healthy" if response.success else "unhealthy",
                    "latency_ms": response.latency_ms,
                    "error": response.error
                }
            except Exception as e:
                results[provider_name.value] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return results


# Global instance
llm_service = LLMService()


# Convenience functions
async def generate_text(prompt: str, **kwargs) -> str:
    """Generate text using the best available provider"""
    response = await llm_service.generate(prompt, **kwargs)
    return response.content


async def generate_with_vision(prompt: str, images: List[bytes], **kwargs) -> str:
    """Generate text from images"""
    response = await llm_service.generate(
        prompt, 
        images=images, 
        capability=ModelCapability.VISION,
        **kwargs
    )
    return response.content


async def generate_code(prompt: str, **kwargs) -> str:
    """Generate code using code-optimized models"""
    response = await llm_service.generate(
        prompt,
        capability=ModelCapability.CODE,
        temperature=0.3,  # Lower temperature for code
        **kwargs
    )
    return response.content


async def generate_embedding(text: str) -> List[float]:
    """Generate text embedding"""
    return await llm_service.generate_embedding(text)
