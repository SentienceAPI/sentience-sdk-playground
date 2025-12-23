"""
Cloud LLM implementation (OpenAI, for comparison)
"""
from openai import OpenAI
from typing import Optional, Dict, Any
from .base_llm import BaseLLM, LLMResponse


class CloudLLM(BaseLLM):
    """Cloud LLM implementation using OpenAI API"""

    def __init__(
        self,
        model: str = "gpt-4-turbo-preview",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """
        Initialize cloud LLM

        Args:
            model: Model identifier (e.g., "gpt-4-turbo-preview", "gpt-3.5-turbo")
            api_key: OpenAI API key (or set OPENAI_API_KEY env var)
            base_url: Custom API base URL (for compatible APIs)
        """
        self._model_name = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)

        # Infer context window
        self._context_window = self._infer_context_window(model)

        print(f"\n✅ Initialized Cloud LLM: {model}")
        print(f"   Context window: {self._context_window} tokens\n")

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate using cloud API

        Args:
            prompt: User prompt
            system_prompt: System instruction
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            response_format: Response format (e.g., {"type": "json_object"})
            **kwargs: Additional API parameters

        Returns:
            LLMResponse object
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Build API call parameters
        api_params = {
            "model": self._model_name,
            "messages": messages,
            "temperature": temperature,
        }

        if max_tokens:
            api_params["max_tokens"] = max_tokens

        if response_format:
            api_params["response_format"] = response_format

        api_params.update(kwargs)

        # Call API
        response = self.client.chat.completions.create(**api_params)

        return LLMResponse(
            content=response.choices[0].message.content,
            tokens_used=response.usage.total_tokens,
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            model_name=self._model_name
        )

    def _infer_context_window(self, model: str) -> int:
        """Infer context window from model name"""
        context_map = {
            "gpt-4-turbo": 128000,
            "gpt-4": 8192,
            "gpt-3.5-turbo": 16385,
            "gpt-3.5": 4096,
        }

        model_lower = model.lower()
        for key, value in context_map.items():
            if key in model_lower:
                return value

        return 4096  # Conservative default

    def supports_json_mode(self) -> bool:
        """OpenAI supports response_format for JSON"""
        return "gpt-4" in self._model_name.lower() or "gpt-3.5" in self._model_name.lower()

    @property
    def context_window(self) -> int:
        return self._context_window

    @property
    def is_local(self) -> bool:
        return False

    @property
    def model_name(self) -> str:
        return self._model_name
