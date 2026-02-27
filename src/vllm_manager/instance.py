"""
VLLMInstance - Manages a single vLLM instance using official CLI.

This module:
1. Inherits from official AsyncEngineArgs (parameter alignment)
2. Starts vLLM using official CLI
3. Captures and stores logs automatically
4. Provides health check and OpenAI client
"""

import subprocess
import logging
import signal
import os
import time
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path
from argparse import Namespace
from openai import OpenAI

try:
    from vllm.engine.arg_utils import AsyncEngineArgs
except ImportError:
    raise ImportError("vllm package is required. Install with: pip install vllm")


class VLLMInstance(AsyncEngineArgs):
    """
    Manages a single vLLM instance with automatic log capture.

    This class inherits from AsyncEngineArgs, so ALL vLLM parameters
    are automatically supported without manual maintenance.

    What we add:
    - Process management (start/stop)
    - Log capture and storage
    - Health check
    - OpenAI client wrapper

    Args:
        name: Unique instance name
        port: Port for API server (default: 8000)
        host: Host to bind (default: 0.0.0.0)
        log_dir: Directory for log files
        model: Model name/path (required)
        **kwargs: ALL AsyncEngineArgs parameters (auto-completed)

    Example:
        >>> instance = VLLMInstance(
        ...     name="server1",
        ...     model="facebook/opt-125m",
        ...     port=8000,
        ...     gpu_memory_utilization=0.5,
        ...     max_num_seqs=2,
        ...     pipeline_parallel_size=2,  # Any AsyncEngineArgs param works
        ... )
        >>> instance.start()
        >>>
        >>> # Get OpenAI client
        >>> client = instance.get_client()
        >>> response = client.completions.create(
        ...     model="facebook/opt-125m",
        ...     prompt="Hello!"
        ... )
        >>>
        >>> # Check logs
        >>> print(instance.log_file)
        >>> instance.stop()
    """

    def __init__(
        self,
        name: str,
        port: int = 8000,
        host: str = "0.0.0.0",
        log_dir: Optional[Path] = None,
        model: str = "",
        **kwargs,
    ):
        # Store vLLM Manager specific attributes
        self.name = name
        self.host = host
        self.port = port
        self.log_dir = Path(log_dir) if log_dir else Path.cwd() / "vllm_logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Initialize parent AsyncEngineArgs with all vLLM parameters
        # This ensures we support ALL vLLM parameters automatically
        kwargs["model"] = model
        super().__init__(**kwargs)

        # Process management
        self.process: Optional[subprocess.Popen] = None
        self._log_file: Optional[Path] = None
        self._start_time: Optional[datetime] = None
        self._healthy = False

        # Setup logging
        self._logger = logging.getLogger(f"vllm_manager.{name}")
        self._setup_logging()

    @property
    def base_url(self) -> str:
        """Get the base URL for this instance."""
        return f"http://{self.host}:{self.port}"

    @property
    def api_url(self) -> str:
        """Get the OpenAI-compatible API URL."""
        return f"{self.base_url}/v1"

    @property
    def log_file(self) -> Optional[Path]:
        """Get the log file path."""
        return self._log_file

    def _setup_logging(self):
        """Setup log file for this instance."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._log_file = self.log_dir / f"vllm_{self.name}_{timestamp}.log"

        # File handler for instance logs
        file_handler = logging.FileHandler(self._log_file, encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)
        self._logger.setLevel(logging.INFO)

        self._logger.info(f"VLLMInstance '{self.name}' initialized")
        self._logger.info(f"Model: {self.model}")
        self._logger.info(f"Log file: {self._log_file}")

    def _to_cli_args(self) -> list[str]:
        """
        Convert AsyncEngineArgs to CLI arguments.

        Uses official AsyncEngineArgs.to_cli_args() method,
        then adds host/port which are server-specific.
        """
        # Get all vLLM engine args using official method
        args = self.to_cli_args()

        # Add server-specific args (host/port)
        # These are not part of AsyncEngineArgs but needed for API server
        server_args = [
            "--host",
            self.host,
            "--port",
            str(self.port),
        ]

        return args + server_args

    def start(self) -> bool:
        """
        Start vLLM instance using official CLI.

        Returns:
            True if started successfully

        Raises:
            RuntimeError: If already running
        """
        if self.process is not None and self.process.poll() is None:
            raise RuntimeError(f"Instance '{self.name}' is already running")

        cmd = self._to_cli_args()
        self._logger.info(
            f"Starting vLLM: python -m vllm.entrypoints.openai.api_server {' '.join(cmd)}"
        )

        try:
            # Start vLLM process
            self.process = subprocess.Popen(
                ["python", "-m", "vllm.entrypoints.openai.api_server"] + cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                preexec_fn=os.setsid if os.name != "nt" else None,
            )
            self._start_time = datetime.now()

            self._logger.info(f"vLLM started with PID: {self.process.pid}")
            self._logger.info(f"API will be available at {self.api_url}")

            # Start log reader thread
            self._start_log_reader()

            # Wait for health check
            self._wait_for_healthy()

            return True

        except Exception as e:
            self._logger.error(f"Failed to start vLLM: {e}")
            self.process = None
            raise

    def _start_log_reader(self):
        """Start thread to read and log vLLM output."""
        import threading

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

    def _wait_for_healthy(self, timeout: int = 120):
        """Wait for vLLM to become healthy."""
        import requests

        self._logger.info(f"Waiting for vLLM to be healthy (timeout: {timeout}s)...")
        start = time.time()

        while time.time() - start < timeout:
            if self.process.poll() is not None:
                raise RuntimeError("vLLM process terminated during startup")

            try:
                response = requests.get(f"{self.base_url}/health", timeout=5)
                if response.status_code == 200:
                    self._healthy = True
                    self._logger.info("vLLM is healthy and ready")
                    return
            except Exception:
                pass

            time.sleep(2)

        raise RuntimeError(f"vLLM failed to become healthy within {timeout}s")

    def stop(self, timeout: int = 30, force: bool = False) -> bool:
        """
        Stop vLLM instance gracefully.

        Args:
            timeout: Seconds to wait for graceful shutdown
            force: If True, forcefully kill immediately

        Returns:
            True if stopped successfully
        """
        if self.process is None:
            return False

        pid = self.process.pid
        self._logger.info(f"Stopping vLLM (PID: {pid})...")

        try:
            if force:
                if os.name != "nt":
                    os.killpg(os.getpgid(pid), signal.SIGKILL)
                else:
                    self.process.kill()
                self._logger.info(f"vLLM forcefully killed (PID: {pid})")
            else:
                if os.name != "nt":
                    os.killpg(os.getpgid(pid), signal.SIGTERM)
                else:
                    self.process.terminate()

                try:
                    self.process.wait(timeout=timeout)
                    self._logger.info(f"vLLM gracefully stopped (PID: {pid})")
                except subprocess.TimeoutExpired:
                    self._logger.warning("Graceful shutdown timed out, force killing...")
                    if os.name != "nt":
                        os.killpg(os.getpgid(pid), signal.SIGKILL)
                    else:
                        self.process.kill()
                    self.process.wait()

        except Exception as e:
            self._logger.error(f"Error stopping vLLM: {e}")
            return False
        finally:
            self.process = None
            self._healthy = False
            self._start_time = None

        return True

    def is_running(self) -> bool:
        """Check if instance is running."""
        return self.process is not None and self.process.poll() is None

    def is_healthy(self) -> bool:
        """Check if instance is healthy."""
        if not self.is_running():
            return False

        import requests

        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            self._healthy = response.status_code == 200
            return self._healthy
        except Exception:
            return False

    def get_client(self, api_key: str = "EMPTY") -> OpenAI:
        """
        Get OpenAI client for this instance.

        Args:
            api_key: API key (default: "EMPTY" for local vLLM)

        Returns:
            OpenAI client configured for this instance
        """
        if not self.is_running():
            raise RuntimeError(f"Instance '{self.name}' is not running")

        return OpenAI(
            api_key=api_key,
            base_url=self.api_url,
        )

    def get_uptime(self) -> Optional[str]:
        """Get instance uptime as human-readable string."""
        if self._start_time is None:
            return None

        delta = datetime.now() - self._start_time
        total_seconds = int(delta.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def get_status(self) -> Dict[str, Any]:
        """Get instance status."""
        return {
            "name": self.name,
            "model": self.model,
            "port": self.port,
            "running": self.is_running(),
            "healthy": self.is_healthy(),
            "pid": self.process.pid if self.process else None,
            "uptime": self.get_uptime(),
            "log_file": str(self._log_file) if self._log_file else None,
            "base_url": self.base_url,
            "api_url": self.api_url,
        }

    def __repr__(self) -> str:
        return f"VLLMInstance(name='{self.name}', model='{self.model}', port={self.port})"

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False
