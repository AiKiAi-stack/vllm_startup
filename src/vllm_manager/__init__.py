"""
vLLM Manager - Cluster orchestration and log management for vLLM.

This package provides:
- Multi-instance vLLM cluster management (spawns vLLM processes using official CLI)
- Automatic log capture and aggregation
- Health monitoring and load balancing
- OpenAI SDK integration (uses official openai package)

Quick Start:
    >>> from vllm_manager import VLLMCluster, VLLMInstance
    >>>
    >>> # Create cluster and add instances
    >>> cluster = VLLMCluster()
    >>> cluster.add_instance(VLLMInstance(
    ...     name="server1",
    ...     model="facebook/opt-125m",
    ...     port=8000
    ... ))
    >>>
    >>> # Start all instances (uses vLLM official CLI internally)
    >>> cluster.start_all()
    >>>
    >>> # Get OpenAI client with automatic load balancing and logging
    >>> client = cluster.get_openai_client()
    >>> response = client.completions.create(
    ...     model="facebook/opt-125m",
    ...     prompt="Hello, world!"
    ... )

For more information, see: https://github.com/AiKiAi-stack/vllm_startup
"""

from .instance import VLLMInstance, VLLMConfig
from .cluster import VLLMCluster
from .logger import VLLMLogger, LogAggregator

__version__ = "0.2.0"
__author__ = "AiKiAi-stack"
__author_email__ = "aikeai.stack@gmail.com"
__license__ = "MIT"
__description__ = "Cluster orchestration and log management for vLLM"
__url__ = "https://github.com/AiKiAi-stack/vllm_startup"

__all__ = [
    # Core classes
    "VLLMInstance",
    "VLLMConfig",
    "VLLMCluster",
    "VLLMLogger",
    "LogAggregator",
    # Metadata
    "__version__",
    "__author__",
    "__license__",
]
