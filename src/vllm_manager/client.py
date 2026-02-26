"""
OpenAI-compatible client for vLLM instances.

This module provides a client for making requests to vLLM's OpenAI-compatible API.
"""

from typing import Optional, Dict, Any, List, Union, Iterator
import requests
import json


class VLLMClient:
    """
    Client for vLLM's OpenAI-compatible HTTP API.

    This is a lightweight wrapper around vLLM's native API.
    It does NOT start or manage vLLM processes - it only communicates
    with already-running vLLM instances.

    Example:
        >>> client = VLLMClient(base_url="http://localhost:8000")
        >>>
        >>> # Health check
        >>> if client.health_check():
        ...     print("Server is healthy")
        >>>
        >>> # Chat completion
        >>> response = client.chat_completion(
        ...     model="facebook/opt-125m",
        ...     messages=[{"role": "user", "content": "Hello!"}]
        ... )
        >>> print(response["choices"][0]["message"]["content"])
        >>>
        >>> # Text completion
        >>> response = client.completion(
        ...     model="facebook/opt-125m",
        ...     prompt="Once upon a time"
        ... )
    """

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """
        Initialize VLLM client.

        Args:
            base_url: Base URL of the vLLM server (e.g., "http://localhost:8000")
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

        self._session = requests.Session()
        if api_key:
            self._session.headers["Authorization"] = f"Bearer {api_key}"

    def health_check(self) -> bool:
        """
        Check if the vLLM server is healthy.

        Returns:
            True if server is healthy, False otherwise
        """
        try:
            response = self._session.get(
                f"{self.base_url}/health",
                timeout=5.0,
            )
            return response.status_code == 200
        except Exception:
            return False

    def get_models(self) -> List[Dict[str, Any]]:
        """
        Get list of available models.

        Returns:
            List of model information dictionaries
        """
        response = self._session.get(
            f"{self.base_url}/v1/models",
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json().get("data", [])

    def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: float = 1.0,
        n: int = 1,
        stream: bool = False,
        stop: Optional[Union[str, List[str]]] = None,
        **kwargs,
    ) -> Union[Dict[str, Any], Iterator[Dict[str, Any]]]:
        """
        Create a chat completion.

        Args:
            model: Model name
            messages: List of message dictionaries with "role" and "content"
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            n: Number of completions to generate
            stream: Whether to stream the response
            stop: Stop sequences
            **kwargs: Additional parameters

        Returns:
            Completion response (or iterator if streaming)
        """
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "n": n,
            "stream": stream,
        }

        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if stop is not None:
            payload["stop"] = stop

        payload.update(kwargs)

        if stream:
            return self._stream_chat_completion(payload)

        response = self._session.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def _stream_chat_completion(
        self,
        payload: Dict[str, Any],
    ) -> Iterator[Dict[str, Any]]:
        """Stream chat completion responses."""
        response = self._session.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload,
            stream=True,
            timeout=self.timeout,
        )
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                line = line.decode("utf-8")
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        yield json.loads(data)
                    except json.JSONDecodeError:
                        continue

    def completion(
        self,
        model: str,
        prompt: Union[str, List[str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: float = 1.0,
        n: int = 1,
        stream: bool = False,
        stop: Optional[Union[str, List[str]]] = None,
        **kwargs,
    ) -> Union[Dict[str, Any], Iterator[Dict[str, Any]]]:
        """
        Create a text completion.

        Args:
            model: Model name
            prompt: Prompt string or list of prompt strings
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            n: Number of completions to generate
            stream: Whether to stream the response
            stop: Stop sequences
            **kwargs: Additional parameters

        Returns:
            Completion response (or iterator if streaming)
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "top_p": top_p,
            "n": n,
            "stream": stream,
        }

        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if stop is not None:
            payload["stop"] = stop

        payload.update(kwargs)

        if stream:
            return self._stream_completion(payload)

        response = self._session.post(
            f"{self.base_url}/v1/completions",
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def _stream_completion(
        self,
        payload: Dict[str, Any],
    ) -> Iterator[Dict[str, Any]]:
        """Stream completion responses."""
        response = self._session.post(
            f"{self.base_url}/v1/completions",
            json=payload,
            stream=True,
            timeout=self.timeout,
        )
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                line = line.decode("utf-8")
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        yield json.loads(data)
                    except json.JSONDecodeError:
                        continue

    def embedding(
        self,
        model: str,
        input: Union[str, List[str]],
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create embeddings.

        Args:
            model: Model name
            input: Text or list of texts to embed
            **kwargs: Additional parameters

        Returns:
            Embedding response
        """
        payload = {
            "model": model,
            "input": input,
        }
        payload.update(kwargs)

        response = self._session.post(
            f"{self.base_url}/v1/embeddings",
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def close(self):
        """Close the HTTP session."""
        self._session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
