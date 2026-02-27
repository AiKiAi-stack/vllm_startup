<div align="center">

# vLLM Manager

**Multi-Instance vLLM Cluster Management & Log Aggregation**

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![vLLM](https://img.shields.io/badge/vLLM-Latest-brightgreen?style=flat&logo=cpu&logoColor=white)](https://github.com/vllm-project/vllm)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/vllm-manager?color=blue&logo=pypi&logoColor=white)](https://pypi.org/project/vllm-manager/)

**[English](README.md)** | **[中文](README.zh.md)**

</div>

---

## 📖 About

vLLM Manager provides multi-instance vLLM cluster management, automatic log collection, and load balancing.

- **Start vLLM**: Uses official CLI (`python -m vllm.entrypoints.openai.api_server`)
- **Send Requests**: Uses official OpenAI SDK (`from openai import OpenAI`)
- **Cluster Management**: Auto start/stop, health checks, failover
- **Log Collection**: All instance logs automatically saved to files

## ✨ Features

- 🎯 **Multi-Instance Management**: Start/stop multiple vLLM instances with one command
- 📝 **Automatic Logging**: All logs saved to `./vllm_logs/` automatically
- 🔄 **Failover**: Auto-retry on other instances when request fails
- ❤️ **Health Monitoring**: Continuous instance health checks
- 🔧 **OpenAI SDK**: Returns standard OpenAI client, seamless integration
- ⚖️ **Load Balancing**: Round-robin request distribution

## 🛠️ Tech Stack

- **Python** 3.8+
- **vLLM** - LLM inference engine
- **OpenAI SDK** - API client
- **Requests** - HTTP client

## 📦 Installation

```bash
# 1. Install vLLM
pip install vllm

# 2. Install dependencies
pip install openai requests

# 3. Install vLLM Manager
pip install vllm-manager
```

## 🚀 Quick Start

### Basic Usage

```python
from vllm_manager import VLLMCluster, VLLMInstance

# 1. Create cluster
cluster = VLLMCluster(log_dir="./vllm_logs")

# 2. Add instances
cluster.add_instance(VLLMInstance(
    name="server1",
    model="facebook/opt-125m",
    port=8000,
    gpu_memory_utilization=0.5,
))

# 3. Start all instances
cluster.start_all()

# 4. Get OpenAI client
client = cluster.get_openai_client()

# 5. Send requests (auto load-balanced)
response = client.completions.create(
    model="facebook/opt-125m",
    prompt="San Francisco is a",
)
print(response)

# 6. Stop cluster
cluster.stop_all()
```

### Context Manager

```python
from vllm_manager import VLLMCluster, VLLMInstance

with VLLMCluster() as cluster:
    cluster.add_instance(VLLMInstance(
        name="server1",
        model="facebook/opt-125m",
        port=8000
    ))
    cluster.start_all()
    
    client = cluster.get_openai_client()
    response = client.chat.completions.create(
        model="facebook/opt-125m",
        messages=[{"role": "user", "content": "Hello!"}]
    )
    print(response.choices[0].message.content)
# Automatically stops all instances on exit
```

## 📖 API Reference

### VLLMInstance

```python
VLLMInstance(
    name: str,                    # Instance name
    model: str,                   # Model name/path
    port: int = 8000,             # Port
    host: str = "0.0.0.0",        # Host
    log_dir: Optional[Path] = None,
    
    # vLLM parameters (inherited from AsyncEngineArgs)
    gpu_memory_utilization: float = 0.9,
    tensor_parallel_size: int = 1,
    pipeline_parallel_size: int = 1,
    max_model_len: Optional[int] = None,
    quantization: Optional[str] = None,
    dtype: str = "auto",
    # ... supports all AsyncEngineArgs parameters
)
```

### VLLMCluster

```python
cluster = VLLMCluster(log_dir="./vllm_logs")
cluster.add_instance(instance: VLLMInstance)
cluster.start_all()
cluster.stop_all()
cluster.health_check()
client = cluster.get_openai_client()
```

## 📝 Log Management

### View Logs

```python
from vllm_manager import LogAggregator

aggregator = LogAggregator(log_dir="./vllm_logs")

# Get all logs
logs = aggregator.get_all_logs(limit=100)
for log in logs:
    print(f"[{log.timestamp}] {log.instance}: {log.message}")

# Export to JSON
aggregator.export_json("logs.json")
```

### Log File Structure

```
./vllm_logs/
├── vllm_manager_20260227_101234.log
├── vllm_server1_20260227_101235.log
└── vllm_server2_20260227_101236.log
```

## ❓ FAQ

### Q: Why use vLLM Manager?

**A**: When you need to run multiple vLLM instances (different models, different GPUs), vLLM Manager provides unified cluster management and log collection.

### Q: Which vLLM parameters are supported?

**A**: All `AsyncEngineArgs` parameters are supported, since `VLLMInstance` inherits from `AsyncEngineArgs`.

### Q: Can I customize the log directory?

**A**: Yes, specify via `log_dir` parameter:
```python
cluster = VLLMCluster(log_dir="/var/log/vllm")
```

## 🤝 Contributing

Issues and Pull Requests are welcome!

```bash
# 1. Fork the repo
# 2. Create your branch (git checkout -b feature/AmazingFeature)
# 3. Commit your changes (git commit -m 'Add some AmazingFeature')
# 4. Push to the branch (git push origin feature/AmazingFeature)
# 5. Open a Pull Request
```

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

## 📬 Contact

- **Project URL**: https://github.com/AiKiAi-stack/vllm_startup
- **Issues**: https://github.com/AiKiAi-stack/vllm_startup/issues
- **Author**: AiKiAi-stack

## 🙏 Acknowledgements

- [vLLM](https://github.com/vllm-project/vllm) - LLM inference engine
- [OpenAI Python SDK](https://github.com/openai/openai-python) - API client
