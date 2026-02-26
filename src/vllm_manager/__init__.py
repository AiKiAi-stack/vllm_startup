"""
vLLM Manager - A cluster management and orchestration tool for vLLM.

This package provides tools for managing multiple vLLM instances with:
- Load balancing and request routing
- Health monitoring and auto-restart
- Unified configuration management
- Multi-instance orchestration

Quick Start:
    >>> from vllm_manager import VLLMCluster, VLLMInstance
    >>>
    >>> # Create cluster with vLLM instances (assumes vLLM is already running)
    >>> cluster = VLLMCluster()
    >>> cluster.add_instance(VLLMInstance("server1", "http://localhost:8000"))
    >>> cluster.add_instance(VLLMInstance("server2", "http://localhost:8001"))
    >>>
    >>> # Use cluster (automatic load balancing)
    >>> response = cluster.chat_completion(
    ...     model="facebook/opt-125m",
    ...     messages=[{"role": "user", "content": "Hello!"}]
    ... )

For more information, see: https://github.com/AiKiAi-stack/vllm_startup
"""

from .instance import VLLMInstance
from .cluster import VLLMCluster
from .router import VLLMRouter
from .client import VLLMClient

__version__ = "0.2.0"
__author__ = "AiKiAi-stack"
__author_email__ = "aikeai.stack@gmail.com"
__license__ = "MIT"
__description__ = "Cluster management and orchestration for vLLM"
__url__ = "https://github.com/AiKiAi-stack/vllm_startup"

__all__ = [
    # Core classes
    "VLLMInstance",
    "VLLMCluster",
    "VLLMRouter",
    "VLLMClient",
    # Metadata
    "__version__",
    "__author__",
    "__license__",
]
