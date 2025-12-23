"""
Base LLM interface for both local and cloud models
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
import json


@dataclass
class LLMResponse:
    """Standardized LLM response"""
    content: str
    reasoning: Optional[str] = None
    confidence: Optional[float] = None
    tokens_used: Optional[int] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    model_name: Optional[str] = None

    def to_json(self) -> Dict[str, Any]:
        """Parse content as JSON"""
        try:
            return json.loads(self.content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse response as JSON: {e}\nContent: {self.content}")


class BaseLLM(ABC):
    """Abstract base class for all LLM implementations"""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        **kwargs
    ) -> LLMResponse:
        """
        Generate response from prompt

        Args:
            prompt: User prompt
            system_prompt: System prompt (instruction)
            **kwargs: Model-specific parameters

        Returns:
            LLMResponse object
        """
        pass

    @abstractmethod
    def supports_json_mode(self) -> bool:
        """Check if model supports structured JSON output"""
        pass

    @property
    @abstractmethod
    def context_window(self) -> int:
        """Maximum context length in tokens"""
        pass

    @property
    @abstractmethod
    def is_local(self) -> bool:
        """Whether model runs locally"""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model identifier"""
        pass

    def __str__(self) -> str:
        """String representation"""
        location = "Local" if self.is_local else "Cloud"
        return f"{location} LLM: {self.model_name} (context: {self.context_window} tokens)"
