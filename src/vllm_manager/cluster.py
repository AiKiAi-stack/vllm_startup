"""
VLLMCluster - Multi-instance cluster management for vLLM.

Manages multiple vLLM instances with:
- Centralized startup/shutdown
- Load balancing across instances
- Health monitoring
- OpenAI client with automatic routing
"""

import logging
import random
from typing import Dict, List, Optional, Any
from pathlib import Path
from openai import OpenAI

from .instance import VLLMInstance


class VLLMCluster:
    """
    Manage a cluster of vLLM instances.

    This class provides:
    - Multi-instance startup/shutdown
    - Load balanced OpenAI client
    - Health monitoring
    - Unified log management

    Args:
        log_dir: Directory for log files
        name: Cluster name

    Example:
        >>> cluster = VLLMCluster()
        >>>
        >>> # Add instances
        >>> cluster.add_instance(VLLMInstance(
        ...     name="server1",
        ...     model="facebook/opt-125m",
        ...     port=8000
        ... ))
        >>> cluster.add_instance(VLLMInstance(
        ...     name="server2",
        ...     model="facebook/opt-350m",
        ...     port=8001
        ... ))
        >>>
        >>> # Start all instances
        >>> cluster.start_all()
        >>>
        >>> # Get OpenAI client with load balancing
        >>> client = cluster.get_openai_client()
        >>> response = client.completions.create(
        ...     model="facebook/opt-125m",
        ...     prompt="Hello!"
        ... )
        >>>
        >>> # Check health
        >>> health = cluster.health_check()
        >>> print(health)
    """

    def __init__(self, log_dir: Optional[Path] = None, name: str = "default"):
        self.name = name
        self.log_dir = Path(log_dir) if log_dir else Path.cwd() / "vllm_logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.instances: Dict[str, VLLMInstance] = {}
        self._current_index = 0
        self._logger = logging.getLogger(f"vllm_manager.cluster.{name}")

    def add_instance(self, instance: VLLMInstance) -> None:
        """Add a vLLM instance to the cluster."""
        if instance.name in self.instances:
            raise ValueError(f"Instance '{instance.name}' already exists")

        self.instances[instance.name] = instance
        self._logger.info(f"Added instance '{instance.name}'")

    def remove_instance(self, name: str) -> None:
        """Remove an instance from the cluster."""
        if name not in self.instances:
            return

        instance = self.instances[name]
        if instance.is_running():
            instance.stop()

        del self.instances[name]
        self._logger.info(f"Removed instance '{name}'")

    def start_all(self) -> Dict[str, bool]:
        """Start all instances in the cluster."""
        results = {}
        for name, instance in self.instances.items():
            try:
                instance.start()
                results[name] = True
                self._logger.info(f"Started instance '{name}'")
            except Exception as e:
                results[name] = False
                self._logger.error(f"Failed to start '{name}': {e}")
        return results

    def stop_all(self, force: bool = False) -> Dict[str, bool]:
        """Stop all instances in the cluster."""
        results = {}
        for name, instance in self.instances.items():
            try:
                instance.stop(force=force)
                results[name] = True
                self._logger.info(f"Stopped instance '{name}'")
            except Exception as e:
                results[name] = False
                self._logger.error(f"Failed to stop '{name}': {e}")
        return results

    def health_check(self) -> Dict[str, bool]:
        """Check health of all instances."""
        return {name: instance.is_healthy() for name, instance in self.instances.items()}

    def _get_healthy_instance(self) -> Optional[VLLMInstance]:
        """Get a healthy instance using round-robin."""
        healthy = [inst for inst in self.instances.values() if inst.is_healthy()]

        if not healthy:
            return None

        # Round-robin selection
        instance = healthy[self._current_index % len(healthy)]
        self._current_index += 1
        return instance

    def get_openai_client(self, api_key: str = "EMPTY") -> Optional["LoadBalancedClient"]:
        """
        Get a load-balanced OpenAI client.

        Args:
            api_key: API key for authentication

        Returns:
            LoadBalancedClient that routes requests across healthy instances
        """
        healthy = self._get_healthy_instance()
        if healthy is None:
            return None

        return LoadBalancedClient(self, api_key)

    def get_status(self) -> Dict[str, Any]:
        """Get status of all instances."""
        return {name: instance.get_status() for name, instance in self.instances.items()}

    def __len__(self) -> int:
        return len(self.instances)

    def __enter__(self):
        self.start_all()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_all()
        return False


class LoadBalancedClient:
    """
    Load-balanced OpenAI client wrapper.

    Routes requests across healthy instances in the cluster.
    Uses the official OpenAI SDK internally.
    """

    def __init__(self, cluster: VLLMCluster, api_key: str = "EMPTY"):
        self.cluster = cluster
        self.api_key = api_key
        self._logger = logging.getLogger("vllm_manager.client")

    def _get_client(self) -> OpenAI:
        """Get OpenAI client from a healthy instance."""
        instance = self.cluster._get_healthy_instance()
        if instance is None:
            raise RuntimeError("No healthy instances available")
        return instance.get_client(self.api_key)

    def completions(self):
        """Access completions API."""
        return _LoadBalancedCompletions(self)

    def chat(self):
        """Access chat completions API."""
        return _LoadBalancedChat(self)

    def models(self):
        """Access models API."""
        return self._get_client().models


class _LoadBalancedCompletions:
    """Load-balanced completions API."""

    def __init__(self, client: LoadBalancedClient):
        self.client = client
        self._max_retries = 3

    def create(self, **kwargs):
        """Create a completion with automatic retry on failure."""
        last_error = None

        for _ in range(self._max_retries):
            try:
                api_client = self.client._get_client()
                return api_client.completions.create(**kwargs)
            except Exception as e:
                last_error = e
                self.client._logger.warning(f"Request failed, retrying: {e}")

        raise RuntimeError(f"All retries failed: {last_error}")


class _LoadBalancedChat:
    """Load-balanced chat completions API."""

    def __init__(self, client: LoadBalancedClient):
        self.client = client
        self._max_retries = 3
        self.completions = _LoadBalancedChatCompletions(client)


class _LoadBalancedChatCompletions:
    """Load-balanced chat completions endpoint."""

    def __init__(self, client: LoadBalancedClient):
        self.client = client
        self._max_retries = 3

    def create(self, **kwargs):
        """Create a chat completion with automatic retry."""
        last_error = None

        for _ in range(self._max_retries):
            try:
                api_client = self.client._get_client()
                return api_client.chat.completions.create(**kwargs)
            except Exception as e:
                last_error = e
                self.client._logger.warning(f"Request failed, retrying: {e}")

        raise RuntimeError(f"All retries failed: {last_error}")
