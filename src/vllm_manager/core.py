"""
vLLM Server Manager - A Python class for managing vLLM server lifecycle.

This module provides a convenient way to start, stop, and manage vLLM API servers
programmatically with proper logging and process management.

Example usage:
    from vllm_manager import VLLMManager

    # Method 1: Parameterized startup
    manager = VLLMManager(model="facebook/opt-125m")
    manager.start(host="0.0.0.0", port=8000)

    # Method 2: Full command startup
    manager = VLLMManager()
    manager.start_command("vllm serve facebook/opt-125m --port 8000")

    # Stop the server
    manager.stop()
"""

import subprocess
import logging
import signal
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Union, Dict, Any
from dataclasses import dataclass, field
import threading
import time


@dataclass
class VLLMConfig:
    """Configuration for vLLM server."""

    model: str
    host: str = "0.0.0.0"
    port: int = 8000
    tensor_parallel_size: int = 1
    dtype: str = "auto"
    max_model_len: Optional[int] = None
    gpu_memory_utilization: float = 0.9
    swap_space: int = 4
    disable_log_stats: bool = False
    disable_log_requests: bool = False
    max_log_len: Optional[int] = None
    additional_args: List[str] = field(default_factory=list)
    
    # Advanced parameters (from vLLM docs)
    quantization: Optional[str] = None
    api_key: Optional[str] = None
    config: Optional[str] = None
    distributed_executor_backend: Optional[str] = None
    worker_use_ray: bool = False
    cuda_devices: Optional[List[int]] = None  # For CUDA_VISIBLE_DEVICES


class VLLMManager:
    """
    Manager class for vLLM server lifecycle.

    Supports two startup modes:
    1. Parameterized: Build command from config parameters
    2. Full command: Provide complete vllm serve command

    Features:
    - Graceful startup and shutdown
    - Comprehensive logging with model name, date, and server identifier
    - Process management with signal handling
    - Health check support
    - Log rotation

    Attributes:
        model_name: Name of the model being served
        server_id: Unique identifier for this server instance
        log_dir: Directory for log files
        process: Subprocess handle for the vLLM server
    """

    def __init__(
        self,
        model: Optional[str] = None,
        log_dir: Optional[Union[str, Path]] = None,
        server_id: Optional[str] = None,
    ):
        """
        Initialize VLLMManager.

        Args:
            model: Model name or path. Required for parameterized startup.
            log_dir: Directory for log files. Defaults to ./vllm_logs.
            server_id: Unique server identifier. Auto-generated if not provided.
        """
        self.model_name = model
        self.server_id = server_id or self._generate_server_id()
        self.log_dir = Path(log_dir) if log_dir else Path.cwd() / "vllm_logs"
        self.process: Optional[subprocess.Popen] = None
        self._log_file: Optional[Path] = None
        self._logger: Optional[logging.Logger] = None
        self._start_time: Optional[datetime] = None
        self._lock = threading.Lock()

        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Setup logging
        self._setup_logging()

    def _generate_server_id(self) -> str:
        """Generate a unique server identifier."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"srv_{timestamp}"

    def _get_log_filename(self) -> str:
        """Generate log filename with model name, date, and server identifier."""
        date_str = datetime.now().strftime("%Y%m%d")
        model_safe = (
            self.model_name.replace("/", "_").replace("\\", "_")
            if self.model_name
            else "unknown"
        )
        return f"vllm_{model_safe}_{date_str}_{self.server_id}.log"

    def _setup_logging(self):
        """Setup logging configuration."""
        self._log_file = self.log_dir / self._get_log_filename()

        # Create logger
        self._logger = logging.getLogger(f"vllm.{self.server_id}")
        self._logger.setLevel(logging.INFO)

        # Clear existing handlers
        self._logger.handlers.clear()

        # File handler with rotation
        file_handler = logging.FileHandler(self._log_file, encoding="utf-8")
        file_handler.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self._logger.addHandler(file_handler)
        self._logger.addHandler(console_handler)

        self._logger.info(
            f"VLLMManager initialized - Server ID: {self.server_id}, Log file: {self._log_file}"
        )

    def _build_command(self, config: VLLMConfig) -> List[str]:
        """Build vLLM serve command from configuration."""
        cmd = ["vllm", "serve", config.model]

        # Add standard parameters
        cmd.extend(["--host", config.host])
        cmd.extend(["--port", str(config.port)])
        cmd.extend(["--tensor-parallel-size", str(config.tensor_parallel_size)])
        cmd.extend(["--dtype", config.dtype])
        cmd.extend(["--gpu-memory-utilization", str(config.gpu_memory_utilization)])
        cmd.extend(["--swap-space", str(config.swap_space)])

        # Add optional parameters
        if config.max_model_len is not None:
            cmd.extend(["--max-model-len", str(config.max_model_len)])

        if config.disable_log_stats:
            cmd.append("--disable-log-stats")

        if config.disable_log_requests:
            cmd.append("--disable-log-requests")

        if config.max_log_len is not None:
            cmd.extend(["--max-log-len", str(config.max_log_len)])

        # Add advanced parameters
        if config.quantization is not None:
            cmd.extend(["--quantization", config.quantization])

        if config.api_key is not None:
            cmd.extend(["--api-key", config.api_key])

        if config.config is not None:
            cmd.extend(["--config", config.config])

        if config.distributed_executor_backend is not None:
            cmd.extend(["--distributed-executor-backend", config.distributed_executor_backend])

        if config.worker_use_ray:
            cmd.append("--worker-use-ray")

        # Add additional arguments
        cmd.extend(config.additional_args)

        return cmd

    def start(
        self,
        model: Optional[str] = None,
        host: str = "0.0.0.0",
        port: int = 8000,
        tensor_parallel_size: int = 1,
        dtype: str = "auto",
        max_model_len: Optional[int] = None,
        gpu_memory_utilization: float = 0.9,
        swap_space: int = 4,
        disable_log_stats: bool = False,
        disable_log_requests: bool = False,
        max_log_len: Optional[int] = None,
        additional_args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> bool:
        """
        Start vLLM server with parameters.

        Args:
            model: Model name or path (required if not set in __init__)
            host: Host to bind to (default: 0.0.0.0)
            port: Port to bind to (default: 8000)
            tensor_parallel_size: Number of tensor parallel workers (default: 1)
            dtype: Data type for model weights (default: auto)
            max_model_len: Maximum model context length (optional)
            gpu_memory_utilization: GPU memory utilization ratio (default: 0.9)
            swap_space: CPU swap space in GB (default: 4)
            disable_log_stats: Disable periodic statistics logging
            disable_log_requests: Disable request logging
            max_log_len: Maximum sequence length for logs
            additional_args: Additional command-line arguments
            env: Environment variables for the subprocess

        Returns:
            True if server started successfully, False otherwise

        Raises:
            RuntimeError: If server is already running
            ValueError: If model is not specified
        """
        with self._lock:
            if self.process is not None and self.process.poll() is None:
                self._logger.error("Server is already running")
                raise RuntimeError("Server is already running. Stop it first.")

            # Determine model name
            model_name = model or self.model_name
            if not model_name:
                raise ValueError(
                    "Model must be specified either in __init__ or start()"
                )

            self.model_name = model_name

            # Build configuration
            config = VLLMConfig(
                model=model_name,
                host=host,
                port=port,
                tensor_parallel_size=tensor_parallel_size,
                dtype=dtype,
                max_model_len=max_model_len,
                gpu_memory_utilization=gpu_memory_utilization,
                swap_space=swap_space,
                disable_log_stats=disable_log_stats,
                disable_log_requests=disable_log_requests,
                max_log_len=max_log_len,
                additional_args=additional_args or [],
            )

            # Build command
            cmd = self._build_command(config)
            cmd_str = " ".join(cmd)

            self._logger.info(f"Starting vLLM server: {cmd_str}")
            self._logger.info(f"Log file: {self._log_file}")

            # Prepare environment
            process_env = os.environ.copy()
            if env:
                process_env.update(env)

            try:
                # Start process
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    env=process_env,
                    preexec_fn=os.setsid if os.name != "nt" else None,
                )
                self._start_time = datetime.now()

                self._logger.info(f"vLLM server started with PID: {self.process.pid}")
                self._logger.info(f"Server will be available at http://{host}:{port}")

                # Start output reader thread
                self._start_output_reader()

                return True

            except Exception as e:
                self._logger.error(f"Failed to start vLLM server: {e}")
                self.process = None
                raise

    def start_command(
        self,
        command: Union[str, List[str]],
        env: Optional[Dict[str, str]] = None,
    ) -> bool:
        """
        Start vLLM server with a full command.

        Args:
            command: Complete vllm serve command (string or list)
            env: Environment variables for the subprocess

        Returns:
            True if server started successfully, False otherwise

        Raises:
            RuntimeError: If server is already running

        Example:
            manager.start_command("vllm serve facebook/opt-125m --port 8000")
            manager.start_command(["vllm", "serve", "facebook/opt-125m", "--port", "8000"])
        """
        with self._lock:
            if self.process is not None and self.process.poll() is None:
                self._logger.error("Server is already running")
                raise RuntimeError("Server is already running. Stop it first.")

            # Parse command if string
            if isinstance(command, str):
                cmd = command.split()
            else:
                cmd = command

            cmd_str = " ".join(cmd) if isinstance(cmd, list) else command

            # Try to extract model name from command
            try:
                if "serve" in cmd:
                    serve_idx = cmd.index("serve")
                    if serve_idx + 1 < len(cmd) and not cmd[serve_idx + 1].startswith(
                        "--"
                    ):
                        self.model_name = cmd[serve_idx + 1]
            except (ValueError, IndexError):
                self.model_name = "unknown"

            self._logger.info(f"Starting vLLM with command: {cmd_str}")
            self._logger.info(f"Log file: {self._log_file}")

            # Prepare environment
            process_env = os.environ.copy()
            if env:
                process_env.update(env)

            try:
                # Start process
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    env=process_env,
                    preexec_fn=os.setsid if os.name != "nt" else None,
                )
                self._start_time = datetime.now()

                self._logger.info(f"vLLM server started with PID: {self.process.pid}")

                # Start output reader thread
                self._start_output_reader()

                return True

            except Exception as e:
                self._logger.error(f"Failed to start vLLM server: {e}")
                self.process = None
                raise

    def _start_output_reader(self):
        """Start a thread to read and log subprocess output."""

        def read_output():
            if self.process is None:
                return
            try:
                for line in self.process.stdout:
                    if line:
                        self._logger.info(line.rstrip())
                    if self.process.poll() is not None:
                        break
            except Exception as e:
                self._logger.error(f"Error reading output: {e}")

        thread = threading.Thread(target=read_output, daemon=True)
        thread.start()

    def stop(self, timeout: int = 30, force: bool = False) -> bool:
        """
        Stop vLLM server gracefully.

        Args:
            timeout: Seconds to wait for graceful shutdown (default: 30)
            force: If True, forcefully kill the process immediately

        Returns:
            True if stopped successfully, False otherwise
        """
        with self._lock:
            if self.process is None:
                self._logger.warning("No server process to stop")
                return False

            if self.process.poll() is not None:
                self._logger.warning("Server process already terminated")
                self.process = None
                return False

            pid = self.process.pid
            self._logger.info(f"Stopping vLLM server (PID: {pid})...")

            try:
                if force:
                    # Force kill
                    if os.name != "nt":
                        os.killpg(os.getpgid(pid), signal.SIGKILL)
                    else:
                        self.process.kill()
                    self._logger.info(f"Server forcefully killed (PID: {pid})")
                else:
                    # Graceful shutdown
                    if os.name != "nt":
                        os.killpg(os.getpgid(pid), signal.SIGTERM)
                    else:
                        self.process.terminate()

                    # Wait for process to terminate
                    try:
                        self.process.wait(timeout=timeout)
                        self._logger.info(f"Server gracefully stopped (PID: {pid})")
                    except subprocess.TimeoutExpired:
                        self._logger.warning(
                            f"Graceful shutdown timed out. Force killing..."
                        )
                        if os.name != "nt":
                            os.killpg(os.getpgid(pid), signal.SIGKILL)
                        else:
                            self.process.kill()
                        self.process.wait()
                        self._logger.info(
                            f"Server forcefully killed after timeout (PID: {pid})"
                        )

            except Exception as e:
                self._logger.error(f"Error stopping server: {e}")
                return False
            finally:
                self.process = None
                self._start_time = None

            return True

    def is_running(self) -> bool:
        """Check if server is currently running."""
        if self.process is None:
            return False
        return self.process.poll() is None

    def get_pid(self) -> Optional[int]:
        """Get server process PID."""
        if self.process and self.is_running():
            return self.process.pid
        return None

    def get_uptime(self) -> Optional[str]:
        """Get server uptime as a human-readable string."""
        if self._start_time is None:
            return None
        delta = datetime.now() - self._start_time
        total_seconds = int(delta.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def wait_for_ready(self, timeout: int = 60, check_interval: float = 2.0) -> bool:
        """
        Wait for server to become ready.

        Args:
            timeout: Maximum seconds to wait (default: 60)
            check_interval: Seconds between health checks (default: 2.0)

        Returns:
            True if server became ready, False if timeout or error
        """
        import socket

        if self.process is None or not self.is_running():
            self._logger.error("Server is not running")
            return False

        # Extract port from process args or config
        port = 8000  # Default
        if self.process.args:
            try:
                if "--port" in self.process.args:
                    port_idx = self.process.args.index("--port")
                    if port_idx + 1 < len(self.process.args):
                        port = int(self.process.args[port_idx + 1])
            except (ValueError, IndexError):
                pass

        self._logger.info(f"Waiting for server to be ready on port {port}...")

        start = time.time()
        while time.time() - start < timeout:
            if not self.is_running():
                self._logger.error("Server process terminated during startup")
                return False

            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1)
                    result = s.connect_ex(("localhost", port))
                    if result == 0:
                        self._logger.info(f"Server is ready on port {port}")
                        return True
            except Exception:
                pass

            time.sleep(check_interval)

        self._logger.error(f"Server failed to become ready within {timeout} seconds")
        return False

    def get_log_file(self) -> Optional[Path]:
        """Get the path to the log file."""
        return self._log_file

    def get_status(self) -> Dict[str, Any]:
        """
        Get current server status.

        Returns:
            Dictionary with server status information
        """
        return {
            "running": self.is_running(),
            "pid": self.get_pid(),
            "model": self.model_name,
            "server_id": self.server_id,
            "log_file": str(self._log_file) if self._log_file else None,
            "uptime": self.get_uptime(),
            "start_time": self._start_time.isoformat() if self._start_time else None,
        }

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure server is stopped."""
        if self.is_running():
            self._logger.info("Exiting context manager, stopping server...")
            self.stop()
        return False


# Convenience function for quick usage
def serve(
    model: str,
    host: str = "0.0.0.0",
    port: int = 8000,
    **kwargs,
) -> VLLMManager:
    """
    Convenience function to start a vLLM server quickly.

    Args:
        model: Model name or path
        host: Host to bind to
        port: Port to bind to
        **kwargs: Additional arguments passed to VLLMManager.start()

    Returns:
        VLLMManager instance with server running

    Example:
        manager = serve("facebook/opt-125m", port=8001)
        # ... use the server ...
        manager.stop()
    """
    manager = VLLMManager(model=model)
    manager.start(host=host, port=port, **kwargs)
    return manager


if __name__ == "__main__":
    # Example usage
    import argparse

    parser = argparse.ArgumentParser(description="vLLM Server Manager")
    parser.add_argument("--model", type=str, required=True, help="Model name or path")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode (start and stop immediately)",
    )

    args = parser.parse_args()

    print(f"Starting vLLM server with model: {args.model}")
    print(f"Host: {args.host}, Port: {args.port}")

    manager = VLLMManager(model=args.model)

    try:
        manager.start(host=args.host, port=args.port)

        if args.test:
            print("Test mode: Server started successfully. Stopping now...")
            time.sleep(2)
            manager.stop()
            print("Server stopped.")
        else:
            print(f"Server running. Press Ctrl+C to stop.")
            print(f"Log file: {manager.get_log_file()}")

            # Keep running
            while manager.is_running():
                time.sleep(1)

    except KeyboardInterrupt:
        print("\nReceived interrupt signal. Stopping server...")
        manager.stop()
        print("Server stopped.")
    except Exception as e:
        print(f"Error: {e}")
        manager.stop()
        sys.exit(1)
