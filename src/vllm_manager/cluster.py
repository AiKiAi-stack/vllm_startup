"""
VLLMCluster - Multi-instance cluster management for vLLM.

This module provides cluster-level management for multiple vLLM instances,
including load balancing, health monitoring, and auto-restart capabilities.
"""

import json
import time
import random
import logging
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from .instance import VLLMInstance


@dataclass
class ClusterConfig:
    """Configuration for VLLMCluster."""

    health_check_interval: float = 30.0
    health_check_timeout: float = 5.0
    auto_restart: bool = False
    max_restarts: int = 3
    restart_delay: float = 2.0
    load_balancing_strategy: str = "round_robin"  # round_robin, least_busy, random


class VLLMCluster:
    """
    Manage a cluster of vLLM instances with load balancing and health monitoring.

    This class provides:
    - Multi-instance management
    - Request routing and load balancing
    - Health monitoring and auto-restart
    - Unified configuration management

    Args:
        config: Cluster configuration
        name: Optional cluster name

    Example:
        >>> cluster = VLLMCluster()
        >>>
        >>> # Add instances (assumes vLLM servers are already running)
        >>> cluster.add_instance(VLLMInstance("server1", "http://localhost:8000"))
        >>> cluster.add_instance(VLLMInstance("server2", "http://localhost:8001"))
        >>>
        >>> # Make requests (automatically load balanced)
        >>> response = cluster.chat_completion(
        ...     model="facebook/opt-125m",
        ...     messages=[{"role": "user", "content": "Hello!"}]
        ... )
        >>>
        >>> # Health check all instances
        >>> health = cluster.health_check()
        >>> print(health)  # {'server1': True, 'server2': True}
    """

    def __init__(
        self,
        config: Optional[ClusterConfig] = None,
        name: str = "default",
    ):
        self.name = name
        self.config = config or ClusterConfig()
        self.instances: Dict[str, VLLMInstance] = {}
        self._instance_order: List[str] = []  # For round-robin
        self._current_index: int = 0
        self._restart_counts: Dict[str, int] = {}
        self._shutdown_event = False

        # Setup logging
        self._logger = logging.getLogger(f"vllm_manager.cluster.{name}")

        # Health monitoring thread
        self._monitor_thread: Optional[Any] = None

    def add_instance(self, instance: VLLMInstance) -> None:
        """
        Add a vLLM instance to the cluster.

        Args:
            instance: VLLMInstance to add

        Raises:
            ValueError: If instance with same name already exists
        """
        if instance.name in self.instances:
            raise ValueError(f"Instance '{instance.name}' already exists in cluster")

        self.instances[instance.name] = instance
        self._instance_order.append(instance.name)
        self._restart_counts[instance.name] = 0

        self._logger.info(f"Added instance '{instance.name}' at {instance.base_url}")

    def remove_instance(self, name: str) -> None:
        """
        Remove a vLLM instance from the cluster.

        Args:
            name: Name of the instance to remove
        """
        if name not in self.instances:
            self._logger.warning(f"Instance '{name}' not found in cluster")
            return

        del self.instances[name]
        self._instance_order.remove(name)
        del self._restart_counts[name]

        self._logger.info(f"Removed instance '{name}' from cluster")

    def get_instance(self, name: str) -> Optional[VLLMInstance]:
        """
        Get a specific instance by name.

        Args:
            name: Instance name

        Returns:
            VLLMInstance or None if not found
        """
        return self.instances.get(name)

    def get_healthy_instances(self) -> List[VLLMInstance]:
        """
        Get all healthy instances.

        Returns:
            List of healthy VLLMInstance objects
        """
        healthy = []
        for instance in self.instances.values():
            if instance.health_check(timeout=self.config.health_check_timeout):
                healthy.append(instance)
        return healthy

    def _select_instance(self) -> Optional[VLLMInstance]:
        """
        Select an instance using the configured load balancing strategy.

        Returns:
            Selected VLLMInstance or None if no healthy instances
        """
        healthy = self.get_healthy_instances()

        if not healthy:
            self._logger.error("No healthy instances available")
            return None

        if self.config.load_balancing_strategy == "round_robin":
            # Round-robin selection
            for _ in range(len(healthy)):
                idx = self._current_index % len(healthy)
                self._current_index += 1
                return healthy[idx]

        elif self.config.load_balancing_strategy == "least_busy":
            # Select instance with lowest request count
            return min(healthy, key=lambda i: i.metrics.request_count)

        elif self.config.load_balancing_strategy == "random":
            # Random selection
            return random.choice(healthy)

        else:
            # Default to first healthy instance
            return healthy[0]

    def completion(
        self,
        model: str,
        prompt: Any,
        max_retries: int = 3,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Make a completion request with automatic load balancing.

        Args:
            model: Model name
            prompt: Text prompt
            max_retries: Maximum retry attempts on failure
            **kwargs: Additional parameters for completion

        Returns:
            API response

        Raises:
            RuntimeError: If no healthy instances available
        """
        last_error = None

        for attempt in range(max_retries):
            instance = self._select_instance()

            if instance is None:
                raise RuntimeError("No healthy instances available")

            try:
                return instance.completion(model=model, prompt=prompt, **kwargs)
            except Exception as e:
                last_error = e
                self._logger.warning(
                    f"Request failed on instance '{instance.name}' (attempt {attempt + 1}/{max_retries}): {e}"
                )
                # Mark instance as potentially unhealthy
                instance.metrics.is_healthy = False
                time.sleep(0.5)  # Brief delay before retry

        raise RuntimeError(f"All retries failed: {last_error}")

    def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_retries: int = 3,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Make a chat completion request with automatic load balancing.

        Args:
            model: Model name
            messages: List of message dictionaries
            max_retries: Maximum retry attempts on failure
            **kwargs: Additional parameters for chat completion

        Returns:
            API response

        Raises:
            RuntimeError: If no healthy instances available
        """
        last_error = None

        for attempt in range(max_retries):
            instance = self._select_instance()

            if instance is None:
                raise RuntimeError("No healthy instances available")

            try:
                return instance.chat_completion(model=model, messages=messages, **kwargs)
            except Exception as e:
                last_error = e
                self._logger.warning(
                    f"Request failed on instance '{instance.name}' (attempt {attempt + 1}/{max_retries}): {e}"
                )
                instance.metrics.is_healthy = False
                time.sleep(0.5)

        raise RuntimeError(f"All retries failed: {last_error}")

    def health_check(self, parallel: bool = True) -> Dict[str, bool]:
        """
        Check health of all instances.

        Args:
            parallel: Whether to check instances in parallel

        Returns:
            Dictionary mapping instance names to health status
        """
        results = {}

        if parallel and len(self.instances) > 1:
            with ThreadPoolExecutor(max_workers=len(self.instances)) as executor:
                future_to_name = {
                    executor.submit(instance.health_check): name
                    for name, instance in self.instances.items()
                }

                for future in as_completed(future_to_name):
                    name = future_to_name[future]
                    try:
                        results[name] = future.result()
                    except Exception as e:
                        self._logger.error(f"Health check error for '{name}': {e}")
                        results[name] = False
        else:
            for name, instance in self.instances.items():
                results[name] = instance.health_check()

        return results

    def get_status(self) -> Dict[str, Any]:
        """
        Get detailed status of all instances.

        Returns:
            Dictionary with status information for all instances
        """
        return {
            "cluster_name": self.name,
            "total_instances": len(self.instances),
            "instances": {
                name: {
                    "base_url": instance.base_url,
                    "is_healthy": instance.metrics.is_healthy,
                    "request_count": instance.metrics.request_count,
                    "error_count": instance.metrics.error_count,
                    "error_rate": instance.metrics.error_rate,
                    "response_time_ms": instance.metrics.response_time_ms,
                    "last_check": instance.metrics.last_check,
                    "restart_count": self._restart_counts[name],
                }
                for name, instance in self.instances.items()
            },
        }

    def save_config(self, path: Path) -> None:
        """
        Save cluster configuration to a JSON file.

        Args:
            path: Path to save configuration
        """
        config = {
            "name": self.name,
            "config": asdict(self.config),
            "instances": [
                {
                    "name": instance.name,
                    "base_url": instance.base_url,
                    "api_key": instance.api_key,
                }
                for instance in self.instances.values()
            ],
        }

        path = Path(path)
        with path.open("w") as f:
            json.dump(config, f, indent=2)

        self._logger.info(f"Saved cluster configuration to {path}")

    @classmethod
    def load_config(cls, path: Path) -> "VLLMCluster":
        """
        Load cluster configuration from a JSON file.

        Args:
            path: Path to configuration file

        Returns:
            VLLMCluster instance with configured instances
        """
        path = Path(path)
        with path.open("r") as f:
            data = json.load(f)

        config = ClusterConfig(**data.get("config", {}))
        cluster = cls(config=config, name=data.get("name", "default"))

        for inst_data in data.get("instances", []):
            instance = VLLMInstance(
                name=inst_data["name"],
                base_url=inst_data["base_url"],
                api_key=inst_data.get("api_key"),
            )
            cluster.add_instance(instance)

        return cluster

    def __len__(self) -> int:
        """Get number of instances in cluster."""
        return len(self.instances)

    def __contains__(self, name: str) -> bool:
        """Check if instance exists in cluster."""
        return name in self.instances

    def __iter__(self):
        """Iterate over instances."""
        return iter(self.instances.values())

    def __repr__(self) -> str:
        return f"VLLMCluster(name='{self.name}', instances={len(self)})"
