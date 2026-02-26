"""
VLLMInstance - A proxy for a single vLLM instance.

This module provides a client for interacting with a running vLLM server
using its native HTTP API. It does NOT start or manage the vLLM process -
that should be done using vLLM's official tools.
"""

import time
import requests
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, field
from urllib.parse import urljoin
import logging


@dataclass
class InstanceMetrics:
    """Metrics for a vLLM instance."""

    is_healthy: bool = False
    response_time_ms: float = 0.0
    last_check: Optional[float] = None
    request_count: int = 0
    error_count: int = 0
    gpu_utilization: Optional[float] = None

    @property
    def error_rate(self) -> float:
        """Calculate error rate."""
        if self.request_count == 0:
            return 0.0
        return self.error_count / self.request_count


class VLLMInstance:
    """
    A client for interacting with a running vLLM instance.

    This class provides a Pythonic interface to vLLM's HTTP API.
    It assumes vLLM is already running and accessible at the given base_url.

    Args:
        name: Unique identifier for this instance
        base_url: Base URL of the vLLM server (e.g., "http://localhost:8000")
        api_key: Optional API key for authentication
        timeout: Default timeout for requests in seconds

    Example:
        >>> instance = VLLMInstance("server1", "http://localhost:8000")
        >>>
        >>> # Check health
        >>> if instance.health_check():
        ...     print("Server is healthy")
        >>>
        >>> # Make a completion request
        >>> response = instance.completion(
        ...     model="facebook/opt-125m",
        ...     prompt="Hello, world!"
        ... )
    """

    def __init__(
        self,
        name: str,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.metrics = InstanceMetrics()

        # Setup logging
        self._logger = logging.getLogger(f"vllm_manager.instance.{name}")

        # Prepare default headers
        self._headers = {
            "Content-Type": "application/json",
        }
        if api_key:
            self._headers["Authorization"] = f"Bearer {api_key}"

    def _make_url(self, endpoint: str) -> str:
        """Construct full URL from endpoint."""
        return urljoin(self.base_url + "/", endpoint.lstrip("/"))

    def health_check(self, timeout: Optional[float] = None) -> bool:
        """
        Check if the vLLM instance is healthy.

        Args:
            timeout: Request timeout in seconds

        Returns:
            True if healthy, False otherwise
        """
        timeout = timeout or 5.0
        start_time = time.time()

        try:
            response = requests.get(
                self._make_url("/health"),
                timeout=timeout,
            )
            is_healthy = response.status_code == 200

            # Update metrics
            self.metrics.is_healthy = is_healthy
            self.metrics.last_check = time.time()
            self.metrics.response_time_ms = (time.time() - start_time) * 1000

            return is_healthy

        except requests.RequestException as e:
            self._logger.debug(f"Health check failed: {e}")
            self.metrics.is_healthy = False
            self.metrics.last_check = time.time()
            return False

    def completion(
        self,
        model: str,
        prompt: Union[str, List[str]],
        max_tokens: int = 16,
        temperature: float = 1.0,
        top_p: float = 1.0,
        n: int = 1,
        stream: bool = False,
        stop: Optional[Union[str, List[str]]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a completion request (OpenAI-compatible).

        Args:
            model: Model name
            prompt: Text prompt(s)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            n: Number of completions to generate
            stream: Whether to stream the response
            stop: Stop sequences
            **kwargs: Additional parameters

        Returns:
            API response as dictionary
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "n": n,
            "stream": stream,
        }

        if stop:
            payload["stop"] = stop

        payload.update(kwargs)

        start_time = time.time()
        self.metrics.request_count += 1

        try:
            response = requests.post(
                self._make_url("/v1/completions"),
                json=payload,
                headers=self._headers,
                timeout=self.timeout,
                stream=stream,
            )
            response.raise_for_status()

            self.metrics.response_time_ms = (time.time() - start_time) * 1000
            return response.json()

        except requests.RequestException as e:
            self.metrics.error_count += 1
            self._logger.error(f"Completion request failed: {e}")
            raise

    def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 16,
        temperature: float = 1.0,
        top_p: float = 1.0,
        n: int = 1,
        stream: bool = False,
        stop: Optional[Union[str, List[str]]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a chat completion request (OpenAI-compatible).

        Args:
            model: Model name
            messages: List of message dictionaries with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            n: Number of completions to generate
            stream: Whether to stream the response
            stop: Stop sequences
            **kwargs: Additional parameters

        Returns:
            API response as dictionary
        """
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "n": n,
            "stream": stream,
        }

        if stop:
            payload["stop"] = stop

        payload.update(kwargs)

        start_time = time.time()
        self.metrics.request_count += 1

        try:
            response = requests.post(
                self._make_url("/v1/chat/completions"),
                json=payload,
                headers=self._headers,
                timeout=self.timeout,
                stream=stream,
            )
            response.raise_for_status()

            self.metrics.response_time_ms = (time.time() - start_time) * 1000
            return response.json()

        except requests.RequestException as e:
            self.metrics.error_count += 1
            self._logger.error(f"Chat completion request failed: {e}")
            raise

    def get_models(self) -> List[Dict[str, Any]]:
        """
        List available models.

        Returns:
            List of model information dictionaries
        """
        try:
            response = requests.get(
                self._make_url("/v1/models"),
                headers=self._headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json().get("data", [])

        except requests.RequestException as e:
            self._logger.error(f"Get models request failed: {e}")
            raise

    def get_metrics(self) -> InstanceMetrics:
        """
        Get current metrics for this instance.

        Returns:
            InstanceMetrics object with current statistics
        """
        return self.metrics

    def __repr__(self) -> str:
        return f"VLLMInstance(name='{self.name}', base_url='{self.base_url}')"

    def __eq__(self, other) -> bool:
        if not isinstance(other, VLLMInstance):
            return False
        return self.name == other.name and self.base_url == other.base_url

    def __hash__(self) -> int:
        return hash((self.name, self.base_url))
