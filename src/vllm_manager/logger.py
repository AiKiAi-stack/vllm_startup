"""
Logging utilities for vLLM Manager.

Provides centralized log management and aggregation for vLLM instances.
"""

import logging
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict


class VLLMLogger:
    """
    Centralized logger for vLLM Manager.

    Configures logging for all vLLM Manager components with:
    - File output to log directory
    - Console output for debugging
    - Log rotation
    """

    def __init__(
        self,
        log_dir: Optional[Path] = None,
        level: int = logging.INFO,
        name: str = "vllm_manager",
    ):
        self.log_dir = Path(log_dir) if log_dir else Path.cwd() / "vllm_logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.level = level
        self.name = name

        # Setup root logger
        self._setup_logger()

    def _setup_logger(self):
        """Configure logging handlers."""
        root_logger = logging.getLogger(self.name)
        root_logger.setLevel(self.level)

        # Clear existing handlers
        root_logger.handlers.clear()

        # File handler with rotation
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"vllm_manager_{timestamp}.log"

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(self.level)

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

        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

        root_logger.info(f"VLLMLogger initialized - Log file: {log_file}")

    def get_logger(self, name: str) -> logging.Logger:
        """Get a child logger."""
        return logging.getLogger(f"{self.name}.{name}")


@dataclass
class LogEntry:
    """A single log entry."""

    timestamp: str
    level: str
    instance: str
    message: str


class LogAggregator:
    """
    Aggregate logs from multiple vLLM instances.

    Provides unified view of logs across the cluster.
    """

    def __init__(self, log_dir: Optional[Path] = None):
        self.log_dir = Path(log_dir) if log_dir else Path.cwd() / "vllm_logs"
        self.entries: List[LogEntry] = []

    def read_instance_logs(self, instance_name: str) -> List[LogEntry]:
        """
        Read logs for a specific instance.

        Args:
            instance_name: Name of the instance

        Returns:
            List of log entries
        """
        entries = []

        # Find log files for this instance
        log_files = sorted(self.log_dir.glob(f"vllm_{instance_name}_*.log"))

        for log_file in log_files:
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    entry = self._parse_line(line, instance_name)
                    if entry:
                        entries.append(entry)

        return entries

    def _parse_line(self, line: str, instance: str) -> Optional[LogEntry]:
        """Parse a log line into a LogEntry."""
        try:
            # Format: "2026-02-26 10:54:51 [INFO] [vllm.server1] Message"
            parts = line.strip().split(" ", 3)
            if len(parts) >= 4:
                timestamp = f"{parts[0]} {parts[1]}"
                level = parts[2].strip("[]")
                return LogEntry(
                    timestamp=timestamp,
                    level=level,
                    instance=instance,
                    message=parts[3] if len(parts) > 3 else "",
                )
        except Exception:
            pass
        return None

    def get_all_logs(self, limit: int = 100) -> List[LogEntry]:
        """Get all logs across instances."""
        all_entries = []

        for log_file in sorted(self.log_dir.glob("vllm_*.log")):
            instance_name = log_file.stem.split("_")[1]
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    entry = self._parse_line(line, instance_name)
                    if entry:
                        all_entries.append(entry)

        # Sort by timestamp and limit
        all_entries.sort(key=lambda e: e.timestamp, reverse=True)
        return all_entries[:limit]

    def export_json(self, output_path: Path) -> None:
        """Export logs to JSON format."""
        logs = [asdict(entry) for entry in self.get_all_logs(limit=10000)]

        output_path = Path(output_path)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
