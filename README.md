<div align="center">

<!-- Logo Placeholder -->
<!-- <img src="assets/logo.jpg" alt="vLLM Manager" width="512"> -->

# vLLM Manager: vLLM Cluster Orchestrator

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

## 🎯 What is vLLM Manager?

**vLLM Manager uses official vLLM CLI to start services and official OpenAI SDK to send requests, focusing on log management and multi-instance orchestration.**

Think of it as:
- **vLLM's Kubernetes** - Manage multiple vLLM instances as a cluster
- **Log Collector** - Automatically capture and aggregate all instance logs
- **High Availability Layer** - Automatic failover and health monitoring

### Core Design Principles

1. **Start vLLM** → Use official command `python -m vllm.entrypoints.openai.api_server --model ...`
2. **Send Requests** → Use official OpenAI SDK `from openai import OpenAI`
3. **vLLM Manager Handles** → Log management + Multi-instance orchestration

## 🚀 Features

- **🎯 Multi-Instance Cluster Management**: Start/stop multiple vLLM instances
- **📝 Automatic Log Collection**: All instance logs automatically saved to files
- **🔄 Automatic Failover**: Auto-retry on other instances when request fails
- **❤️ Health Monitoring**: Continuous health checks
- **🔧 OpenAI SDK Integration**: Returns standard OpenAI client
- **🌐 Load Balancing**: Round-robin request distribution

## 📦 Installation

```bash
# Install vLLM first
pip install vllm

# Install dependencies
pip install openai requests

# Install vLLM Manager
pip install vllm-manager
```

## 🎬 Quick Start

### 1. Create Cluster and Add Instances

```python
from vllm_manager import VLLMCluster, VLLMInstance

# Create cluster
cluster = VLLMCluster(log_dir="./vllm_logs")

# Add instances (configure vLLM parameters)
cluster.add_instance(VLLMInstance(
    name="server1",
    model="facebook/opt-125m",
    port=8000,
    gpu_memory_utilization=0.5,
    max_num_seqs=2,
))

cluster.add_instance(VLLMInstance(
    name="server2",
    model="facebook/opt-350m",
    port=8001,
))
```

### 2. Start All Instances

```python
# Start all instances (uses vLLM official CLI)
results = cluster.start_all()
print(f"Start results: {results}")

# Check health
health = cluster.health_check()
print(f"Health: {health}")
```

### 3. Get OpenAI Client and Send Requests

```python
from openai import OpenAI

# Get load-balanced client
client = cluster.get_openai_client()

# Use standard OpenAI SDK API
completion = client.completions.create(
    model="facebook/opt-125m",
    prompt="San Francisco is a",
)
print("Completion result:", completion)

# Chat completions
chat_response = client.chat.completions.create(
    model="facebook/opt-125m",
    messages=[{"role": "user", "content": "Hello!"}]
)
print("Chat result:", chat_response.choices[0].message.content)
```

### 4. View Logs

```python
from vllm_manager import LogAggregator

# Aggregate all logs
aggregator = LogAggregator(log_dir="./vllm_logs")

# Get all logs
logs = aggregator.get_all_logs(limit=100)
for log in logs:
    print(f"[{log.timestamp}] {log.instance}: {log.message}")

# Export to JSON
aggregator.export_json("logs.json")
```

### 5. Stop Cluster

```python
# Stop all instances
cluster.stop_all()

# Or use context manager
with VLLMCluster() as cluster:
    cluster.add_instance(VLLMInstance("s1", model="facebook/opt-125m", port=8000))
    cluster.start_all()
    
    client = cluster.get_openai_client()
    response = client.completions.create(model="facebook/opt-125m", prompt="Hello!")
    print(response)
# Automatically stops all instances on exit
```

## 🖥️ Advanced Usage

### Configure vLLM Parameters

```python
VLLMInstance(
    name="gpu-server",
    model="Qwen/Qwen2.5-1.5B-Instruct",
    port=8000,
    # GPU configuration
    gpu_memory_utilization=0.5,
    tensor_parallel_size=2,
    max_num_seqs=2,
    max_model_len=128,
    # Quantization
    quantization="awq_marlin",
    dtype="float16",
    # Other settings
    trust_remote_code=True,
    enforce_eager=True,
    api_key="your-api-key",
)
```

### Custom Log Directory

```python
from pathlib import Path

cluster = VLLMCluster(log_dir=Path("/var/log/vllm"))
```

### Manual Instance Control

```python
instance = VLLMInstance(
    name="solo",
    model="facebook/opt-125m",
    port=8000
)

# Start
instance.start()

# Get client
client = instance.get_client()
response = client.completions.create(
    model="facebook/opt-125m",
    prompt="Test"
)

# View log file
print(f"Log file: {instance.log_file}")

# Stop
instance.stop()
```

## 📖 API Reference

### VLLMInstance

Manages a single vLLM instance.

```python
VLLMInstance(
    name: str,                    # Instance name
    model: str,                   # Model name/path
    port: int = 8000,             # Port
    log_dir: Optional[Path] = None,  # Log directory
    gpu_memory_utilization: float = 0.9,
    max_num_seqs: int = 256,
    tensor_parallel_size: int = 1,
    quantization: Optional[str] = None,
    trust_remote_code: bool = False,
    enforce_eager: bool = False,
    **kwargs
)
```

Methods:
- `start()` - Start vLLM instance
- `stop()` - Stop instance
- `is_running()` - Check if running
- `is_healthy()` - Check health status
- `get_client()` - Get OpenAI client
- `get_status()` - Get status information

### VLLMCluster

Manages multiple vLLM instances.

```python
VLLMCluster(
    log_dir: Optional[Path] = None,  # Log directory
    name: str = "default"           # Cluster name
)
```

Methods:
- `add_instance(instance)` - Add instance
- `start_all()` - Start all instances
- `stop_all()` - Stop all instances
- `health_check()` - Health check
- `get_openai_client()` - Get load-balanced client
- `get_status()` - Get all instances status

### VLLMLogger

Logging configuration.

```python
VLLMLogger(
    log_dir: Optional[Path] = None,
    level: int = logging.INFO,
)
```

### LogAggregator

Log aggregator.

```python
aggregator = LogAggregator(log_dir="./vllm_logs")
logs = aggregator.get_all_logs(limit=100)
aggregator.export_json("output.json")
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Application                          │
│                  from openai import OpenAI                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              VLLMCluster / LoadBalancedClient               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Load Balancing │ Auto-Retry │ Health Check │ Logs    │  │
│  └───────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         ▼           ▼           ▼
    ┌────────┐  ┌────────┐  ┌────────┐
    │vLLM #1 │  │vLLM #2 │  │vLLM #3 │
    │:8000   │  │:8001   │  │:8002   │
    └────────┘  └────────┘  └────────┘
         │           │           │
         └───────────┴───────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │   Auto Log Saving     │
         │  ./vllm_logs/         │
         └───────────────────────┘
```

## 📝 Log Example

After startup, all logs are automatically saved to `./vllm_logs/`:

```
./vllm_logs/
├── vllm_manager_20260227_101234.log  # Manager logs
├── vllm_server1_20260227_101235.log  # Server 1 logs
└── vllm_server2_20260227_101236.log  # Server 2 logs
```

Log format:
```
2026-02-27 10:12:35 [INFO] [vllm_manager.server1] VLLMInstance 'server1' initialized
2026-02-27 10:12:35 [INFO] [vllm_manager.server1] Starting vLLM: python -m vllm.entrypoints.openai.api_server ...
2026-02-27 10:12:40 [INFO] [vllm_manager.server1] vLLM started with PID: 12345
2026-02-27 10:12:45 [INFO] [vllm_manager.server1] vLLM is healthy and ready
```

## 📄 License

MIT License

## 🤝 Contributing

Contributions welcome! Please feel free to submit issues and pull requests.

See [ROADMAP.md](ROADMAP.md) for planned features.

---

<div align="center">

**🎉 If you find this useful, please give us a Star!**

</div>
