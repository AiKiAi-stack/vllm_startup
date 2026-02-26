"""
Request router for vLLM clusters.

Provides intelligent request routing across multiple vLLM instances.
"""

import random
import time
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from .instance import VLLMInstance
from .cluster import VLLMCluster


class RoutingStrategy(Enum):
    """Available routing strategies."""

    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
    LEAST_CONNECTIONS = "least_connections"
    HEALTH_PRIORITY = "health_priority"


@dataclass
class RoutingMetrics:
    """Metrics for routing decisions."""

    request_count: int = 0
    error_count: int = 0
    total_latency: float = 0.0
    last_used: float = field(default_factory=time.time)

    @property
    def average_latency(self) -> float:
        """Calculate average latency."""
        if self.request_count == 0:
            return 0.0
        return self.total_latency / self.request_count

    @property
    def error_rate(self) -> float:
        """Calculate error rate."""
        if self.request_count == 0:
            return 0.0
        return self.error_count / self.request_count


class VLLMRouter:
    """
    Intelligent request router for vLLM clusters.

    Routes requests across multiple vLLM instances using various strategies
    like round-robin, random, least-connections, or health-priority.

    Example:
        >>> from vllm_manager import VLLMCluster, VLLMInstance, VLLMRouter
        >>>
        >>> cluster = VLLMCluster()
        >>> cluster.add_instance(VLLMInstance("server1", "http://localhost:8000"))
        >>> cluster.add_instance(VLLMInstance("server2", "http://localhost:8001"))
        >>>
        >>> router = VLLMRouter(cluster, strategy=RoutingStrategy.ROUND_ROBIN)
        >>>
        >>> # Route a chat completion request
        >>> response = router.chat_completion(
        ...     model="facebook/opt-125m",
        ...     messages=[{"role": "user", "content": "Hello!"}]
        ... )
    """

    def __init__(
        self,
        cluster: VLLMCluster,
        strategy: RoutingStrategy = RoutingStrategy.ROUND_ROBIN,
        health_check_interval: float = 30.0,
        on_instance_fail: Optional[Callable[[str], None]] = None,
    ):
        """
        Initialize VLLM Router.

        Args:
            cluster: VLLMCluster instance to route across
            strategy: Routing strategy to use
            health_check_interval: Seconds between health checks
            on_instance_fail: Callback when an instance fails
        """
        self.cluster = cluster
        self.strategy = strategy
        self.health_check_interval = health_check_interval
        self.on_instance_fail = on_instance_fail

        self._metrics: Dict[str, RoutingMetrics] = {}
        self._round_robin_index = 0
        self._last_health_check = 0.0

        # Initialize metrics for existing instances
        for name in cluster.instances:
            self._metrics[name] = RoutingMetrics()

    def _get_healthy_instances(self) -> List[VLLMInstance]:
        """Get list of healthy instances."""
        return [instance for instance in self.cluster.instances.values() if instance.is_healthy()]

    def _update_health_check(self):
        """Run health check if interval has passed."""
        current_time = time.time()
        if current_time - self._last_health_check >= self.health_check_interval:
            self.cluster.health_check()
            self._last_health_check = current_time

    def _select_instance(self, model: Optional[str] = None) -> VLLMInstance:
        """
        Select an instance based on routing strategy.

        Args:
            model: Optional model name to filter instances

        Returns:
            Selected VLLMInstance

        Raises:
            RuntimeError: No healthy instances available
        """
        self._update_health_check()

        healthy_instances = self._get_healthy_instances()

        # Filter by model if specified
        if model:
            healthy_instances = [
                inst for inst in healthy_instances if inst.model == model or inst.model is None
            ]

        if not healthy_instances:
            raise RuntimeError("No healthy instances available")

        if self.strategy == RoutingStrategy.RANDOM:
            return random.choice(healthy_instances)

        elif self.strategy == RoutingStrategy.ROUND_ROBIN:
            # Simple round-robin
            if self._round_robin_index >= len(healthy_instances):
                self._round_robin_index = 0
            instance = healthy_instances[self._round_robin_index]
            self._round_robin_index = (self._round_robin_index + 1) % len(healthy_instances)
            return instance

        elif self.strategy == RoutingStrategy.LEAST_CONNECTIONS:
            # Select instance with least recent activity
            return min(
                healthy_instances,
                key=lambda inst: self._metrics.get(inst.name, RoutingMetrics()).last_used,
            )

        elif self.strategy == RoutingStrategy.HEALTH_PRIORITY:
            # Prioritize instances with lowest error rate
            def health_score(inst):
                metrics = self._metrics.get(inst.name, RoutingMetrics())
                return metrics.error_rate

            return min(healthy_instances, key=health_score)

        else:
            # Default to random
            return random.choice(healthy_instances)

    def _update_metrics(self, instance_name: str, latency: float, success: bool):
        """Update routing metrics for an instance."""
        if instance_name not in self._metrics:
            self._metrics[instance_name] = RoutingMetrics()

        metrics = self._metrics[instance_name]
        metrics.request_count += 1
        metrics.total_latency += latency
        metrics.last_used = time.time()

        if not success:
            metrics.error_count += 1

    def chat_completion(self, **kwargs) -> Dict[str, Any]:
        """
        Route a chat completion request.

        Args:
            **kwargs: Arguments passed to the instance's chat_completion method

        Returns:
            Completion response

        Raises:
            RuntimeError: If no healthy instances available
        """
        model = kwargs.get("model")
        instance = self._select_instance(model)

        start_time = time.time()
        try:
            response = instance.chat_completion(**kwargs)
            latency = time.time() - start_time
            self._update_metrics(instance.name, latency, success=True)
            return response
        except Exception as e:
            latency = time.time() - start_time
            self._update_metrics(instance.name, latency, success=False)

            # Mark instance as unhealthy
            instance.mark_unhealthy(str(e))

            if self.on_instance_fail:
                self.on_instance_fail(instance.name)

            # Retry with another instance
            return self.chat_completion(**kwargs)

    def completion(self, **kwargs) -> Dict[str, Any]:
        """
        Route a text completion request.

        Args:
            **kwargs: Arguments passed to the instance's completion method

        Returns:
            Completion response
        """
        model = kwargs.get("model")
        instance = self._select_instance(model)

        start_time = time.time()
        try:
            response = instance.completion(**kwargs)
            latency = time.time() - start_time
            self._update_metrics(instance.name, latency, success=True)
            return response
        except Exception as e:
            latency = time.time() - start_time
            self._update_metrics(instance.name, latency, success=False)

            instance.mark_unhealthy(str(e))

            if self.on_instance_fail:
                self.on_instance_fail(instance.name)

            return self.completion(**kwargs)

    def embedding(self, **kwargs) -> Dict[str, Any]:
        """
        Route an embedding request.

        Args:
            **kwargs: Arguments passed to the instance's embedding method

        Returns:
            Embedding response
        """
        instance = self._select_instance()

        start_time = time.time()
        try:
            response = instance.embedding(**kwargs)
            latency = time.time() - start_time
            self._update_metrics(instance.name, latency, success=True)
            return response
        except Exception as e:
            latency = time.time() - start_time
            self._update_metrics(instance.name, latency, success=False)

            instance.mark_unhealthy(str(e))

            if self.on_instance_fail:
                self.on_instance_fail(instance.name)

            return self.embedding(**kwargs)

    def get_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get routing metrics for all instances.

        Returns:
            Dictionary mapping instance names to their metrics
        """
        return {
            name: {
                "request_count": metrics.request_count,
                "error_count": metrics.error_count,
                "error_rate": metrics.error_rate,
                "average_latency": metrics.average_latency,
                "last_used": metrics.last_used,
            }
            for name, metrics in self._metrics.items()
        }

    def reset_metrics(self):
        """Reset all routing metrics."""
        self._metrics.clear()
        for name in self.cluster.instances:
            self._metrics[name] = RoutingMetrics()
