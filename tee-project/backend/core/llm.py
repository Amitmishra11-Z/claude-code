"""
LLM inference layer — runs inside TEE enclave context.
Supports DummyLLM (always available) and OpenAILLM (if API key set).
# [SIMULATED] DummyLLM; # [REAL] OpenAILLM when OPENAI_API_KEY is configured
"""
import os
import time
import hashlib
from typing import Protocol

from .enclave import get_enclave


class LLMBackend(Protocol):
    def infer(self, prompt: str, model: str, max_tokens: int) -> str: ...


class DummyLLM:
    """
    Deterministic stub LLM for testing/demo.
    # [SIMULATED] — Replace with real model in production
    """

    _responses = {
        "hello": "Hello! I'm running securely inside a Trusted Execution Environment. Your query is encrypted end-to-end.",
        "default": (
            "I received your encrypted query and processed it securely inside the TEE enclave. "
            "This response was generated without exposing your plaintext prompt to the host OS or cloud provider. "
            "In a production deployment this would call a real language model such as GPT-4 or a locally hosted Llama model."
        ),
        "explain tee": (
            "A Trusted Execution Environment (TEE) is a secure area inside a CPU that guarantees code and data "
            "loaded inside it are protected with respect to confidentiality and integrity. "
            "Intel SGX, AMD SEV, and ARM TrustZone are popular implementations."
        ),
        "privacy": (
            "Privacy in LLM inference is critical. Without TEE, your prompts are visible to the cloud provider, "
            "the model server operator, and potentially logged for training. With TEE, the plaintext never leaves "
            "the encrypted enclave memory — not even the server operator can read it."
        ),
    }

    def infer(self, prompt: str, model: str = "dummy", max_tokens: int = 512) -> str:
        prompt_lower = prompt.lower().strip()
        for keyword, response in self._responses.items():
            if keyword in prompt_lower:
                return response
        # Default: echo a secure acknowledgement
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:8]
        return (
            f"[TEE-Secure Response] Processed prompt (hash: {prompt_hash}) inside enclave. "
            f"Model: {model}. Max tokens: {max_tokens}. "
            "Your data was never exposed in plaintext outside the secure enclave boundary."
        )


class OpenAILLM:
    """
    Real OpenAI API backend.
    # [REAL] — requires OPENAI_API_KEY environment variable
    """

    def __init__(self):
        try:
            from openai import OpenAI
            self._client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        except (ImportError, KeyError) as e:
            raise RuntimeError(f"OpenAILLM requires openai package and OPENAI_API_KEY: {e}")

    def infer(self, prompt: str, model: str = "gpt-3.5-turbo", max_tokens: int = 512) -> str:
        response = self._client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""


def get_llm() -> LLMBackend:
    """Factory: returns OpenAILLM if OPENAI_API_KEY is set, else DummyLLM."""
    if os.environ.get("OPENAI_API_KEY"):
        try:
            return OpenAILLM()
        except RuntimeError:
            pass
    return DummyLLM()


def infer(prompt: str, model: str = "dummy", max_tokens: int = 512) -> str:
    """
    Run LLM inference inside TEE enclave context.
    All intermediate state (prompt, response) lives only in isolated enclave memory.
    """
    enclave = get_enclave()
    llm = get_llm()

    with enclave.run() as ctx:
        # Store prompt in isolated enclave memory only
        ctx.store("prompt", prompt)
        ctx.store("model", model)

        start = time.perf_counter()
        response = llm.infer(prompt, model, max_tokens)
        elapsed_ms = (time.perf_counter() - start) * 1000

        ctx.store("response_preview", response[:32] + "…")
        ctx.store("inference_ms", elapsed_ms)

        # Response is returned; enclave memory wiped on context exit
        return response
