"""
Local LLM implementation using Hugging Face transformers
Supports Qwen, Gemma, Llama, Phi, and other instruction-tuned models
"""
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from typing import Optional, Dict
from .base_llm import BaseLLM, LLMResponse
import warnings

warnings.filterwarnings('ignore', category=UserWarning)


class LocalLLM(BaseLLM):
    """Local LLM implementation using Hugging Face transformers"""

    def __init__(
        self,
        model_name: str = "Qwen/Qwen2.5-3B-Instruct",
        device: str = "auto",
        load_in_4bit: bool = False,
        load_in_8bit: bool = False,
        max_memory: Optional[Dict[int, str]] = None,
        torch_dtype: str = "auto"
    ):
        """
        Initialize local LLM

        Args:
            model_name: Hugging Face model identifier
            device: Device to run on ("cpu", "cuda", "mps", "auto")
            load_in_4bit: Use 4-bit quantization (saves 75% memory)
            load_in_8bit: Use 8-bit quantization (saves 50% memory)
            max_memory: Memory constraints per device
            torch_dtype: Data type ("auto", "float16", "bfloat16", "float32")
        """
        self._model_name = model_name
        self._context_window = self._infer_context_window(model_name)
        self._device = device

        print(f"\n{'='*70}")
        print(f"Loading Local LLM: {model_name}")
        print(f"{'='*70}")

        # Load tokenizer
        print("📥 Loading tokenizer...")
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True
        )

        # Set padding token if not present
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Configure quantization if requested
        quantization_config = None
        if load_in_4bit:
            print("🔧 Configuring 4-bit quantization...")
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4"
            )
        elif load_in_8bit:
            print("🔧 Configuring 8-bit quantization...")
            quantization_config = BitsAndBytesConfig(load_in_8bit=True)

        # Determine torch dtype
        if torch_dtype == "auto":
            if device == "cpu":
                dtype = torch.float32
            else:
                dtype = torch.float16
        else:
            dtype = getattr(torch, torch_dtype)

        # Load model
        print("📥 Loading model...")
        try:
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                quantization_config=quantization_config,
                torch_dtype=dtype if quantization_config is None else None,
                device_map=device,
                max_memory=max_memory,
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )
            self.model.eval()

            # Get actual device
            if hasattr(self.model, 'device'):
                actual_device = str(self.model.device)
            elif hasattr(self.model, 'hf_device_map'):
                actual_device = str(self.model.hf_device_map)
            else:
                actual_device = device

            print(f"✅ Model loaded successfully!")
            print(f"   Device: {actual_device}")
            print(f"   Dtype: {dtype}")
            print(f"   Context window: {self._context_window} tokens")
            if quantization_config:
                quant_type = "4-bit" if load_in_4bit else "8-bit"
                print(f"   Quantization: {quant_type}")
            print(f"{'='*70}\n")

        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            raise

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        max_new_tokens: int = 512,
        temperature: float = 0.1,
        top_p: float = 0.9,
        do_sample: Optional[bool] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate response using local model

        Args:
            prompt: User prompt
            system_prompt: System instruction
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0 = greedy, higher = more random)
            top_p: Nucleus sampling parameter
            do_sample: Whether to use sampling (auto-determined if None)
            **kwargs: Additional generation parameters

        Returns:
            LLMResponse object
        """
        # Auto-determine sampling based on temperature
        if do_sample is None:
            do_sample = temperature > 0

        # Format prompt based on model's chat template
        formatted_prompt = self._format_prompt(system_prompt, prompt)

        # Tokenize with truncation
        inputs = self.tokenizer(
            formatted_prompt,
            return_tensors="pt",
            truncation=True,
            max_length=self._context_window - max_new_tokens
        ).to(self.model.device)

        input_length = inputs['input_ids'].shape[1]

        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=do_sample,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                **kwargs
            )

        # Decode only the new tokens
        generated_tokens = outputs[0][input_length:]
        response_text = self.tokenizer.decode(
            generated_tokens,
            skip_special_tokens=True
        ).strip()

        return LLMResponse(
            content=response_text,
            tokens_used=len(generated_tokens),
            prompt_tokens=input_length,
            completion_tokens=len(generated_tokens),
            model_name=self._model_name
        )

    def _format_prompt(self, system_prompt: str, user_prompt: str) -> str:
        """Format prompt based on model's chat template"""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": user_prompt})

        # Use model's native chat template if available
        if hasattr(self.tokenizer, 'apply_chat_template'):
            try:
                return self.tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True
                )
            except Exception:
                # Fallback if chat template fails
                pass

        # Fallback formatting
        formatted = ""
        if system_prompt:
            formatted += f"System: {system_prompt}\n\n"
        formatted += f"User: {user_prompt}\n\nAssistant:"
        return formatted

    def _infer_context_window(self, model_name: str) -> int:
        """Infer context window from model name"""
        context_map = {
            "qwen2.5": 32768,
            "qwen2": 32768,
            "qwen": 8192,
            "gemma-2": 8192,
            "gemma": 8192,
            "phi-3": 4096,
            "phi-2": 2048,
            "llama-3.2": 131072,
            "llama-3.1": 131072,
            "llama-3": 8192,
            "llama-2": 4096,
        }

        model_lower = model_name.lower()
        for key, value in context_map.items():
            if key in model_lower:
                return value

        return 2048  # Conservative default

    def supports_json_mode(self) -> bool:
        """Local models typically need prompt engineering for JSON"""
        return False

    @property
    def context_window(self) -> int:
        return self._context_window

    @property
    def is_local(self) -> bool:
        return True

    @property
    def model_name(self) -> str:
        return self._model_name

    def get_model_info(self) -> Dict[str, any]:
        """Get detailed model information"""
        param_count = sum(p.numel() for p in self.model.parameters())
        param_count_b = param_count / 1e9

        return {
            "name": self._model_name,
            "parameters": f"{param_count_b:.1f}B",
            "context_window": self._context_window,
            "device": str(self._device),
            "dtype": str(next(self.model.parameters()).dtype),
        }
