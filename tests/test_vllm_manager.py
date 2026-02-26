"""
Test suite for vLLM Manager package.

Run tests with: pytest tests/ -v
"""

import pytest
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

# Test imports from package
from vllm_manager import (
    VLLMManager,
    VLLMConfig,
    VLLMCluster,
    serve,
    __version__,
)


class TestVLLMConfig:
    """Test VLLMConfig dataclass."""

    def test_config_default_values(self):
        """Test default configuration values."""
        config = VLLMConfig(model="test-model")
        assert config.model == "test-model"
        assert config.host == "0.0.0.0"
        assert config.port == 8000
        assert config.tensor_parallel_size == 1
        assert config.dtype == "auto"
        assert config.gpu_memory_utilization == 0.9

    def test_config_custom_values(self):
        """Test custom configuration values."""
        config = VLLMConfig(
            model="facebook/opt-125m",
            host="127.0.0.1",
            port=8001,
            tensor_parallel_size=2,
            quantization="awq",
        )
        assert config.model == "facebook/opt-125m"
        assert config.host == "127.0.0.1"
        assert config.port == 8001
        assert config.tensor_parallel_size == 2
        assert config.quantization == "awq"


class TestVLLMManager:
    """Test VLLMManager class."""

    def test_manager_initialization(self):
        """Test manager initialization."""
        manager = VLLMManager(model="test-model")
        assert manager.model_name == "test-model"
        assert manager.server_id is not None
        assert manager.log_dir.exists()
        assert not manager.is_running()

    def test_manager_custom_log_dir(self, tmp_path):
        """Test custom log directory."""
        log_dir = tmp_path / "custom_logs"
        manager = VLLMManager(model="test-model", log_dir=log_dir)
        assert manager.log_dir == log_dir
        assert log_dir.exists()

    def test_manager_custom_server_id(self):
        """Test custom server ID."""
        manager = VLLMManager(model="test-model", server_id="custom_srv")
        assert manager.server_id == "custom_srv"

    def test_log_file_naming(self):
        """Test log file naming convention."""
        manager = VLLMManager(model="facebook/opt-125m", server_id="test_srv")
        log_file = manager.get_log_file()
        log_name = log_file.name
        assert "vllm" in log_name
        assert "facebook_opt-125m" in log_name or "facebook/opt-125m" in log_name

    def test_command_building_basic(self):
        """Test basic command building."""
        manager = VLLMManager(model="test")
        config = VLLMConfig(model="facebook/opt-125m", port=8000)
        cmd = manager._build_command(config)
        assert cmd[0:3] == ["vllm", "serve", "facebook/opt-125m"]
        assert "--port" in cmd
        assert "8000" in cmd

    def test_command_building_advanced(self):
        """Test advanced command building."""
        manager = VLLMManager(model="test")
        config = VLLMConfig(
            model="meta-llama/Llama-2-7b",
            quantization="awq",
            api_key="test-key",
            tensor_parallel_size=4,
        )
        cmd = manager._build_command(config)
        assert "--quantization" in cmd
        assert "awq" in cmd
        assert "--api-key" in cmd
        assert "test-key" in cmd
        assert "--tensor-parallel-size" in cmd
        assert "4" in cmd

    def test_status_reporting(self):
        """Test status reporting."""
        manager = VLLMManager(model="test-model")
        status = manager.get_status()
        assert "running" in status
        assert "pid" in status
        assert "model" in status
        assert "server_id" in status
        assert "log_file" in status
        assert status["model"] == "test-model"
        assert status["running"] is False

    def test_not_running_initially(self):
        """Test that manager is not running initially."""
        manager = VLLMManager(model="test-model")
        assert not manager.is_running()
        assert manager.get_pid() is None

    def test_error_no_model(self):
        """Test error when no model specified."""
        manager = VLLMManager()
        with pytest.raises(ValueError, match="Model must be specified"):
            manager.start()

    def test_uptime_none_initially(self):
        """Test uptime is None when not running."""
        manager = VLLMManager(model="test-model")
        assert manager.get_uptime() is None


class TestVLLMCluster:
    """Test VLLMCluster class."""

    def test_cluster_initialization(self):
        """Test cluster initialization."""
        cluster = VLLMCluster()
        assert len(cluster) == 0
        assert cluster.servers == {}

    def test_add_server(self):
        """Test adding servers to cluster."""
        cluster = VLLMCluster()
        cluster.add_server("server1", model="model1", port=8001)
        assert len(cluster) == 1
        assert "server1" in cluster.servers
        assert cluster.servers["server1"].model == "model1"
        assert cluster.servers["server1"].port == 8001

    def test_add_multiple_servers(self):
        """Test adding multiple servers."""
        cluster = VLLMCluster()
        cluster.add_server("server1", model="model1", port=8001)
        cluster.add_server("server2", model="model2", port=8002, auto_restart=True)
        assert len(cluster) == 2
        assert cluster.servers["server2"].auto_restart is True

    def test_duplicate_server_name(self):
        """Test error on duplicate server name."""
        cluster = VLLMCluster()
        cluster.add_server("server1", model="model1", port=8001)
        with pytest.raises(ValueError, match="already exists"):
            cluster.add_server("server1", model="model2", port=8002)

    def test_cluster_status(self):
        """Test cluster status reporting."""
        cluster = VLLMCluster()
        cluster.add_server("server1", model="model1", port=8001)
        status = cluster.get_status()
        assert "server1" in status
        assert "running" in status["server1"]
        assert "model" in status["server1"]


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_serve_function(self):
        """Test serve convenience function."""
        # Note: We can't actually start a server in tests
        # This just verifies the function exists and has correct signature
        assert callable(serve)


class TestVersion:
    """Test package version."""

    def test_version_format(self):
        """Test version format is valid."""
        assert isinstance(__version__, str)
        # Version should match semver-like pattern
        assert len(__version__.split(".")) >= 2


class TestContextManager:
    """Test context manager support."""

    def test_context_manager_enter(self):
        """Test context manager entry."""
        with VLLMManager(model="test-model") as manager:
            assert manager is not None
            assert manager.model_name == "test-model"

    def test_context_manager_exit(self):
        """Test context manager exit cleans up."""
        with VLLMManager(model="test-model") as manager:
            pass
        # After exiting, manager should be cleaned up
        # (server stopped if it was running)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
