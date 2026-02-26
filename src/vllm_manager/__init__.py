"""
vLLM Manager - A comprehensive Python package for managing vLLM API server lifecycle.

This package provides convenient tools for starting, stopping, and managing vLLM API servers
programmatically with proper logging, process management, and multi-server support.

Quick Start:
    >>> from vllm_manager import VLLMManager
    >>> manager = VLLMManager(model="facebook/opt-125m")
    >>> manager.start(port=8000)
    >>> manager.wait_for_ready()
    >>> # ... use the server ...
    >>> manager.stop()

Multi-Server Management:
    >>> from vllm_manager import VLLMCluster
    >>> cluster = VLLMCluster()
    >>> cluster.add_server("model1", model="facebook/opt-125m", port=8001)
    >>> cluster.add_server("model2", model="facebook/opt-350m", port=8002)
    >>> cluster.start_all()
    >>> cluster.health_check()

For more information, see the documentation at: https://github.com/yourusername/vllm-manager
"""

from .core import VLLMManager, VLLMConfig, serve
from .enhanced import VLLMCluster, health_monitor, ServerInstance

__version__ = "0.1.0"
__author__ = "AiKiAi-stack"
__author_email__ = "aikeai.stack@gmail.com"
__license__ = "MIT"
__description__ = "Manage vLLM API server lifecycle with ease"
__url__ = "https://github.com/AiKiAi-stack/vllm_startup"

__all__ = [
    # Core classes
    "VLLMManager",
    "VLLMConfig",
    "serve",
    # Enhanced features
    "VLLMCluster",
    "health_monitor",
    "ServerInstance",
    # Metadata
    "__version__",
    "__author__",
    "__license__",
]
