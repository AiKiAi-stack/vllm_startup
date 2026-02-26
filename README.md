<div align="center">

<!-- Logo Placeholder -->
<!-- <img src="assets/logo.jpg" alt="vLLM Manager" width="512"> -->

# vLLM Manager: vLLM Server Management Tool

### Write Once, Use Forever. No More vLLM Worries!

  <p>
    <img src="https://img.shields.io/badge/Python-3.8+-3776AB?style=flat&logo=python&logoColor=white" alt="Python">
    <img src="https://img.shields.io/badge/vLLM-Ready-brightgreen?style=flat&logo=cpu&logoColor=white" alt="vLLM Ready">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
    <br>
    <a href="https://pypi.org/project/vllm-manager/"><img src="https://img.shields.io/pypi/v/vllm-manager?color=blue&logo=pypi&logoColor=white" alt="PyPI"></a>
    <a href="https://github.com/AiKiAi-stack/vllm_startup"><img src="https://img.shields.io/github/stars/AiKiAi-stack/vllm_startup?style=flat&logo=github" alt="GitHub Stars"></a>
    <a href="https://github.com/AiKiAi-stack/vllm_startup/issues"><img src="https://img.shields.io/github/issues/AiKiAi-stack/vllm_startup" alt="Issues"></a>
  </p>

**English** | [中文](README.zh.md)

</div>

---

## 🚀 Features

- **🎯 Two Startup Modes**: Parameterized configuration or full command execution
- **📝 Comprehensive Logging**: Automatic log files with model name, date, and server identifier
- **🛑 Graceful Shutdown**: Proper process termination with timeout and force kill fallback
- **❤️ Health Monitoring**: Built-in health check and readiness detection
- **🖥️ Multi-Server Management**: Cluster support for running multiple instances
- **🔄 Auto-Restart**: Automatic server restart on failure (optional)
- **🎮 CUDA Management**: GPU device selection and resource management
- **🔧 Context Manager Support**: Clean resource management with `with` statement

## 📦 Installation

```bash
# Ensure vLLM is installed
pip install vllm

# Install vLLM Manager
pip install vllm-manager

# Import and use
from vllm_manager import VLLMManager
```

## 🎬 Quick Start

### Basic Usage

```python
from vllm_manager import VLLMManager

# Create manager and start server
manager = VLLMManager(model="facebook/opt-125m")
manager.start(host="0.0.0.0", port=8000)

# Check status
print(manager.get_status())
# {'running': True, 'pid': 12345, 'model': 'facebook/opt-125m', ...}

# Wait for server to be ready
manager.wait_for_ready(timeout=60)

# Stop when done
manager.stop()
```

### Parameterized Startup

```python
manager = VLLMManager(model="meta-llama/Llama-2-7b-hf")

manager.start(
    host="0.0.0.0",
    port=8000,
    tensor_parallel_size=2,      # Multi-GPU
    gpu_memory_utilization=0.9,
    max_model_len=4096,
    dtype="float16",
    quantization="awq",          # Optional: AWQ quantization
    api_key="your-api-key",      # Optional: API authentication
)
```

### Full Command Startup

```python
manager = VLLMManager()

# Start with complete command
manager.start_command(
    "vllm serve facebook/opt-125m --port 8000 --tensor-parallel-size 2"
)

# Or as list
manager.start_command([
    "vllm", "serve", "facebook/opt-125m",
    "--port", "8000",
    "--host", "0.0.0.0"
])
```

### Context Manager

```python
from vllm_manager import VLLMManager

with VLLMManager(model="facebook/opt-125m") as manager:
    manager.start(port=8000)
    # Server runs here
    # Automatically stopped when exiting context
```

### Convenience Function

```python
from vllm_manager import serve

# Quick one-liner
manager = serve("facebook/opt-125m", port=8001)
# ... use the server ...
manager.stop()
```

## 🖥️ Advanced Features

### Multi-Server Cluster

```python
from vllm_manager import VLLMCluster

# Create cluster
cluster = VLLMCluster()

# Add multiple servers
cluster.add_server("small", model="facebook/opt-125m", port=8001)
cluster.add_server("medium", model="facebook/opt-350m", port=8002, auto_restart=True)

# Start all
results = cluster.start_all()

# Health check
health = cluster.health_check()

# Get status
status = cluster.get_status()

# Stop all
cluster.stop_all()
```

### Configuration Persistence

```python
from vllm_manager import VLLMCluster

# Save configuration
cluster = VLLMCluster()
cluster.add_server("model1", model="facebook/opt-125m", port=8001)
cluster.save_config("config.json")

# Load configuration
cluster = VLLMCluster.load_config("config.json")
```

### GPU Selection

```python
from vllm_manager import VLLMManager

# Select specific GPUs
manager = VLLMManager(model="facebook/opt-125m")
manager.start(
    port=8000,
    cuda_devices=[0, 1],  # Use GPUs 0 and 1
    tensor_parallel_size=2,
)
```

### Health Monitoring

```python
from vllm_manager import VLLMManager, health_monitor
import threading

manager = VLLMManager(model="facebook/opt-125m")
manager.start(port=8000)

# Start health monitoring in background thread
monitor_thread = threading.Thread(
    target=health_monitor,
    args=(manager,),
    kwargs={"interval": 30, "max_failures": 3},
    daemon=True
)
monitor_thread.start()
```

## 📖 API Reference

### VLLMManager

#### Initialization

```python
VLLMManager(
    model: Optional[str] = None,       # Model name/path
    log_dir: Optional[Path] = None,    # Log directory
    server_id: Optional[str] = None,   # Custom server ID
)
```

#### Methods

| Method | Description |
|--------|-------------|
| `start(**kwargs)` | Start server with parameters |
| `start_command(cmd)` | Start server with full command |
| `stop(timeout=30, force=False)` | Stop server gracefully |
| `is_running()` | Check if server is running |
| `get_pid()` | Get server process ID |
| `get_uptime()` | Get server uptime string |
| `wait_for_ready(timeout=60)` | Wait for server readiness |
| `get_log_file()` | Get log file path |
| `get_status()` | Get comprehensive status dict |

#### Start Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | str | - | Model name or path |
| `host` | str | "0.0.0.0" | Bind address |
| `port` | int | 8000 | Port number |
| `tensor_parallel_size` | int | 1 | GPU count for parallelism |
| `dtype` | str | "auto" | Data type (auto, float16, etc.) |
| `max_model_len` | int | None | Maximum context length |
| `gpu_memory_utilization` | float | 0.9 | GPU memory ratio |
| `swap_space` | int | 4 | CPU swap space (GB) |
| `quantization` | str | None | Quantization method (awq, gptq, etc.) |
| `api_key` | str | None | API authentication key |
| `cuda_devices` | List[int] | None | GPU device IDs |
| `additional_args` | List[str] | [] | Extra command-line arguments |

### VLLMCluster

#### Methods

| Method | Description |
|--------|-------------|
| `add_server(name, model, port, **kwargs)` | Add server instance |
| `start_server(name)` | Start specific server |
| `stop_server(name)` | Stop specific server |
| `start_all()` | Start all servers |
| `stop_all()` | Stop all servers |
| `health_check(timeout=5)` | Check all servers' health |
| `get_status()` | Get all servers' status |
| `save_config(path)` | Save configuration to JSON |
| `load_config(path)` | Load configuration from JSON |

## 📁 Log Files

Logs are stored in `./vllm_logs/` by default with naming format:

```
vllm_{model_name}_{YYYYMMDD}_{server_id}.log
```

Example:
```
vllm_facebook_opt-125m_20260226_srv_20260226105451.log
```

Log format:
```
2026-02-26 10:54:51 [INFO] [vllm.srv_20260226105451] VLLMManager initialized
2026-02-26 10:54:52 [INFO] [vllm.srv_20260226105451] Starting vLLM server: vllm serve ...
2026-02-26 10:54:53 [INFO] [vllm.srv_20260226105451] vLLM server started with PID: 12345
```

## ⚠️ Error Handling

```python
from vllm_manager import VLLMManager

manager = VLLMManager(model="facebook/opt-125m")

try:
    manager.start(port=8000)
except RuntimeError as e:
    # Server already running
    print(f"Error: {e}")
except ValueError as e:
    # Model not specified
    print(f"Error: {e}")
except Exception as e:
    # Other errors
    print(f"Error: {e}")
finally:
    manager.stop()
```

## 💡 Examples

### Example 1: Simple Server

```python
from vllm_manager import VLLMManager

# Start server
manager = VLLMManager(model="facebook/opt-125m")
manager.start(port=8000)

# Keep running
import time
while manager.is_running():
    time.sleep(1)
```

### Example 2: Production Deployment

```python
from vllm_manager import VLLMManager
import logging

# Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Start with production config
manager = VLLMManager(
    model="meta-llama/Llama-2-70b-hf",
    log_dir="/var/log/vllm",
)

try:
    manager.start(
        host="0.0.0.0",
        port=8000,
        tensor_parallel_size=4,
        gpu_memory_utilization=0.95,
        api_key="secret-key",
        disable_log_requests=False,
    )
    
    # Wait for ready
    if not manager.wait_for_ready(timeout=120):
        raise RuntimeError("Server failed to start")
    
    logger.info("Server is ready!")
    
    # Keep running
    while True:
        time.sleep(1)
        
except KeyboardInterrupt:
    logger.info("Shutting down...")
    manager.stop(timeout=60)
except Exception as e:
    logger.error(f"Error: {e}")
    manager.stop(force=True)
    raise
```

### Example 3: Multiple Models

```python
from vllm_manager import VLLMCluster

# Create cluster for multiple models
cluster = VLLMCluster(log_dir="/var/log/vllm")

# Add models
cluster.add_server(
    "llama-7b",
    model="meta-llama/Llama-2-7b-hf",
    port=8001,
    auto_restart=True,
)
cluster.add_server(
    "llama-70b",
    model="meta-llama/Llama-2-70b-hf",
    port=8002,
    tensor_parallel_size=4,
)

# Start all
cluster.start_all()

# Monitor
import time
while True:
    status = cluster.get_status()
    print(f"Status: {status}")
    time.sleep(10)
```

## 📄 License

MIT License

## 🤝 Contributing

Contributions welcome! Please feel free to submit issues and pull requests.

---

<div align="center">

**🎉 If you find this useful, please give us a Star!**

</div>
