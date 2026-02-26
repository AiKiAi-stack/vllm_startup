"""
vLLM Server Manager - Enhanced Features

This module provides additional features for vLLMManager:
- Health check endpoint monitoring
- Auto-restart capability
- Multiple server instance management
- Configuration file support
"""

import json
import time
import requests
from typing import Optional, List, Dict, Any, Callable
from pathlib import Path
from dataclasses import dataclass, asdict

# Import from main module (support both package and standalone)
try:
    from .vllm_manager import VLLMManager
except ImportError:
    from vllm_manager import VLLMManager


@dataclass
class ServerInstance:
    """Represents a managed server instance."""

    name: str
    manager: VLLMManager
    model: str
    port: int
    auto_restart: bool = False
    max_restarts: int = 3
    restart_count: int = 0


class VLLMCluster:
    """
    Manage multiple vLLM server instances.

    Features:
    - Start/stop multiple servers
    - Health monitoring
    - Auto-restart on failure
    - Resource management

    Example:
        cluster = VLLMCluster()
        cluster.add_server("model1", port=8001, model="facebook/opt-125m")
        cluster.add_server("model2", port=8002, model="facebook/opt-350m")
        cluster.start_all()
        cluster.health_check()
        cluster.stop_all()
    """

    def __init__(self, log_dir: Optional[Path] = None):
        """
        Initialize VLLMCluster.

        Args:
            log_dir: Directory for log files. Defaults to ./vllm_logs.
        """
        self.servers: Dict[str, ServerInstance] = {}
        self.log_dir = log_dir or Path.cwd() / "vllm_logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def add_server(
        self,
        name: str,
        model: str,
        port: int = 8000,
        auto_restart: bool = False,
        max_restarts: int = 3,
        **kwargs,
    ) -> VLLMManager:
        """
        Add a server instance to the cluster.

        Args:
            name: Unique name for this server
            model: Model name or path
            port: Port to bind to
            auto_restart: Enable auto-restart on failure
            max_restarts: Maximum restart attempts
            **kwargs: Additional arguments passed to VLLMManager.start()

        Returns:
            VLLMManager instance for the server

        Raises:
            ValueError: If server name already exists
        """
        if name in self.servers:
            raise ValueError(f"Server '{name}' already exists")

        manager = VLLMManager(model=model, log_dir=self.log_dir, server_id=name)

        self.servers[name] = ServerInstance(
            name=name,
            manager=manager,
            model=model,
            port=port,
            auto_restart=auto_restart,
            max_restarts=max_restarts,
        )

        return manager

    def start_server(self, name: str, **kwargs) -> bool:
        """
        Start a specific server.

        Args:
            name: Server name
            **kwargs: Override arguments for manager.start()

        Returns:
            True if started successfully
        """
        if name not in self.servers:
            raise ValueError(f"Server '{name}' not found")

        instance = self.servers[name]
        return instance.manager.start(port=instance.port, **kwargs)

    def stop_server(self, name: str, **kwargs) -> bool:
        """
        Stop a specific server.

        Args:
            name: Server name
            **kwargs: Arguments for manager.stop()

        Returns:
            True if stopped successfully
        """
        if name not in self.servers:
            raise ValueError(f"Server '{name}' not found")

        instance = self.servers[name]
        instance.restart_count = 0  # Reset restart count on manual stop
        return instance.manager.stop(**kwargs)

    def start_all(self, **kwargs) -> Dict[str, bool]:
        """
        Start all servers in the cluster.

        Args:
            **kwargs: Arguments for manager.start()

        Returns:
            Dictionary mapping server names to start success
        """
        results = {}
        for name, instance in self.servers.items():
            try:
                results[name] = self.start_server(name, **kwargs)
            except Exception as e:
                results[name] = False
                instance.manager._logger.error(f"Failed to start {name}: {e}")
        return results

    def stop_all(self, **kwargs) -> Dict[str, bool]:
        """
        Stop all servers in the cluster.

        Args:
            **kwargs: Arguments for manager.stop()

        Returns:
            Dictionary mapping server names to stop success
        """
        results = {}
        for name, instance in self.servers.items():
            try:
                results[name] = self.stop_server(name, **kwargs)
            except Exception as e:
                results[name] = False
                instance.manager._logger.error(f"Failed to stop {name}: {e}")
        return results

    def health_check(self, timeout: int = 5) -> Dict[str, bool]:
        """
        Check health of all running servers.

        Args:
            timeout: Request timeout in seconds

        Returns:
            Dictionary mapping server names to health status
        """
        results = {}
        for name, instance in self.servers.items():
            if not instance.manager.is_running():
                results[name] = False
                continue

            try:
                response = requests.get(
                    f"http://localhost:{instance.port}/health",
                    timeout=timeout,
                )
                results[name] = response.status_code == 200
            except Exception:
                results[name] = False

            # Handle auto-restart
            if not results[name] and instance.auto_restart:
                if instance.restart_count < instance.max_restarts:
                    instance.manager._logger.warning(
                        f"Server {name} unhealthy, attempting restart "
                        f"({instance.restart_count + 1}/{instance.max_restarts})"
                    )
                    instance.restart_count += 1

                    # Stop and restart
                    instance.manager.stop(force=True)
                    time.sleep(2)
                    self.start_server(name)
                else:
                    instance.manager._logger.error(
                        f"Server {name} exceeded max restart attempts"
                    )

        return results

    def get_status(self) -> Dict[str, Any]:
        """
        Get status of all servers in the cluster.

        Returns:
            Dictionary with status information for all servers
        """
        return {
            name: {
                "running": instance.manager.is_running(),
                "model": instance.model,
                "port": instance.port,
                "pid": instance.manager.get_pid(),
                "uptime": instance.manager.get_uptime(),
                "auto_restart": instance.auto_restart,
                "restart_count": instance.restart_count,
            }
            for name, instance in self.servers.items()
        }

    def save_config(self, path: Path) -> None:
        """
        Save cluster configuration to a JSON file.

        Args:
            path: Path to save configuration
        """
        config = {
            "servers": {
                name: {
                    "model": instance.model,
                    "port": instance.port,
                    "auto_restart": instance.auto_restart,
                    "max_restarts": instance.max_restarts,
                }
                for name, instance in self.servers.items()
            }
        }

        path = Path(path)
        with path.open("w") as f:
            json.dump(config, f, indent=2)

    @classmethod
    def load_config(cls, path: Path, log_dir: Optional[Path] = None) -> "VLLMCluster":
        """
        Load cluster configuration from a JSON file.

        Args:
            path: Path to configuration file
            log_dir: Directory for log files

        Returns:
            VLLMCluster instance with configured servers
        """
        path = Path(path)
        with path.open("r") as f:
            config = json.load(f)

        cluster = cls(log_dir=log_dir)

        for name, server_config in config["servers"].items():
            cluster.add_server(
                name=name,
                model=server_config["model"],
                port=server_config["port"],
                auto_restart=server_config.get("auto_restart", False),
                max_restarts=server_config.get("max_restarts", 3),
            )

        return cluster

    def __len__(self) -> int:
        """Get number of servers in cluster."""
        return len(self.servers)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - stop all servers."""
        self.stop_all()
        return False


def health_monitor(
    manager: VLLMManager,
    interval: int = 30,
    max_failures: int = 3,
    callback: Optional[callable] = None,
) -> None:
    """
    Monitor server health and restart on failure.

    Args:
        manager: VLLMManager instance to monitor
        interval: Check interval in seconds
        max_failures: Maximum consecutive failures before restart
        callback: Optional callback function on restart

    This function blocks until the manager is stopped.
    """
    failures = 0

    while manager.is_running():
        time.sleep(interval)

        try:
            response = requests.get(
                f"http://localhost:{manager.get_status().get('port', 8000)}/health",
                timeout=5,
            )
            if response.status_code == 200:
                failures = 0
                continue
        except Exception:
            pass

        failures += 1
        manager._logger.warning(f"Health check failed ({failures}/{max_failures})")

        if failures >= max_failures:
            manager._logger.error("Max failures reached, restarting server...")

            pid = manager.get_pid()
            manager.stop(force=True)

            if callback:
                callback(manager)

            # Restart with same config
            time.sleep(2)
            manager.start()

            failures = 0


if __name__ == "__main__":
    # Example usage
    cluster = VLLMCluster()

    # Add servers
    cluster.add_server("small", model="facebook/opt-125m", port=8001)
    cluster.add_server(
        "medium",
        model="facebook/opt-350m",
        port=8002,
        auto_restart=True,
    )

    # Save config
    cluster.save_config("cluster_config.json")

    # Start all
    results = cluster.start_all()
    print(f"Start results: {results}")

    # Monitor
    try:
        while True:
            status = cluster.get_status()
            print(f"Status: {status}")
            time.sleep(10)
    except KeyboardInterrupt:
        cluster.stop_all()
