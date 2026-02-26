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

**vLLM Manager is NOT a replacement for vLLM. It enhances vLLM with multi-instance orchestration capabilities.**

Think of it as:
- **Kubernetes for vLLM** - Manage multiple vLLM instances as a cluster
- **Load Balancer for LLMs** - Intelligent request routing across instances
- **High Availability Layer** - Automatic failover and health monitoring

### Why vLLM Manager?

While vLLM provides excellent single-instance serving capabilities, production deployments often need:

| Requirement | vLLM Alone | With vLLM Manager |
|-------------|-----------|-------------------|
| Multiple models on different GPUs | ❌ Manual setup | ✅ Automatic orchestration |
| Load balancing across instances | ❌ Not supported | ✅ Built-in routing strategies |
| Automatic failover | ❌ Not supported | ✅ Health checks & auto-restart |
| Unified API endpoint | ❌ Multiple ports | ✅ Single entry point |
| Request queueing | ❌ Not supported | ✅ Built-in queue management |

## 🚀 Features

- **🎯 Multi-Instance Cluster Management**: Manage multiple vLLM instances as a unified cluster
- **⚖️ Intelligent Load Balancing**: Route requests using round-robin, random, or health-priority strategies
- **🔄 Automatic Failover**: Detect unhealthy instances and route to healthy ones automatically
- **❤️ Health Monitoring**: Continuous health checks with automatic recovery
- **📊 Request Metrics**: Track latency, error rates, and throughput per instance
- **🔧 Pythonic API**: Simple, intuitive interface for cluster operations
- **🌐 OpenAI-Compatible**: Works with vLLM's native OpenAI-compatible API

## 📦 Installation

```bash
# Install vLLM first
pip install vllm

# Install vLLM Manager
pip install vllm-manager
```

## 🎬 Quick Start

### 1. Start vLLM Instances

First, start your vLLM servers using the official vLLM CLI:

```bash
# Terminal 1 - Server 1
vllm serve facebook/opt-125m --port 8000

# Terminal 2 - Server 2
vllm serve facebook/opt-350m --port 8001
```

### 2. Create a Cluster

```python
from vllm_manager import VLLMCluster, VLLMInstance

# Create cluster
cluster = VLLMCluster()

# Add instances (assumes vLLM is already running)
cluster.add_instance(VLLMInstance(
    name="server1",
    base_url="http://localhost:8000",
    model="facebook/opt-125m"
))

cluster.add_instance(VLLMInstance(
    name="server2", 
    base_url="http://localhost:8001",
    model="facebook/opt-350m"
))

# Check health
health = cluster.health_check()
print(f"Health status: {health}")
```

### 3. Route Requests with Load Balancing

```python
from vllm_manager import VLLMRouter, RoutingStrategy

# Create router with round-robin strategy
router = VLLMRouter(cluster, strategy=RoutingStrategy.ROUND_ROBIN)

# Make requests (automatically load balanced)
response = router.chat_completion(
    model="facebook/opt-125m",
    messages=[{"role": "user", "content": "Hello, how are you?"}]
)

print(response["choices"][0]["message"]["content"])
```

### 4. Use the Cluster Directly

```python
# Chat completion (auto-routed to appropriate instance)
response = cluster.chat_completion(
    model="facebook/opt-125m",
    messages=[{"role": "user", "content": "Tell me a joke"}]
)

# Text completion
response = cluster.completion(
    model="facebook/opt-350m",
    prompt="Once upon a time",
    max_tokens=100
)

# Get metrics
metrics = cluster.get_metrics()
print(f"Cluster metrics: {metrics}")
```

## 🖥️ Advanced Usage

### Configuration Persistence

```python
# Save cluster configuration
cluster.save_config("cluster.json")

# Load configuration later
cluster = VLLMCluster.load_config("cluster.json")
```

### Custom Routing Strategy

```python
from vllm_manager import RoutingStrategy

# Health-priority: route to healthiest instance
router = VLLMRouter(cluster, strategy=RoutingStrategy.HEALTH_PRIORITY)

# Least-connections: route to least busy instance
router = VLLMRouter(cluster, strategy=RoutingStrategy.LEAST_CONNECTIONS)
```

### Direct Client Access

```python
from vllm_manager import VLLMClient

# Connect directly to a vLLM instance
client = VLLMClient(base_url="http://localhost:8000")

# Health check
if client.health_check():
    response = client.chat_completion(
        model="facebook/opt-125m",
        messages=[{"role": "user", "content": "Hi!"}]
    )
```

### Auto-Restart on Failure

```python
# Enable auto-restart for critical instances
cluster.add_instance(VLLMInstance(
    name="critical-server",
    base_url="http://localhost:8000",
    auto_restart=True,
    max_restarts=3
))

# Health check will automatically restart failed instances
cluster.health_check()
```

## 📖 API Reference

### VLLMInstance

Represents a single vLLM instance.

```python
VLLMInstance(
    name: str,                    # Unique instance name
    base_url: str,                 # vLLM server URL
    model: Optional[str] = None,   # Model name (optional)
    api_key: Optional[str] = None, # API key (optional)
    auto_restart: bool = False,    # Enable auto-restart
    max_restarts: int = 3,         # Max restart attempts
)
```

Methods:
- `health_check()` - Check if instance is healthy
- `chat_completion(**kwargs)` - Send chat completion request
- `completion(**kwargs)` - Send text completion request
- `embedding(**kwargs)` - Send embedding request
- `get_metrics()` - Get instance metrics

### VLLMCluster

Manages multiple VLLMInstance objects.

```python
VLLMCluster()
```

Methods:
- `add_instance(instance)` - Add instance to cluster
- `remove_instance(name)` - Remove instance from cluster
- `health_check()` - Check health of all instances
- `get_healthy_instances()` - Get list of healthy instances
- `chat_completion(**kwargs)` - Route chat completion request
- `completion(**kwargs)` - Route completion request
- `get_metrics()` - Get metrics for all instances
- `save_config(path)` - Save configuration to JSON
- `load_config(path)` - Load configuration from JSON

### VLLMRouter

Intelligent request router with multiple strategies.

```python
VLLMRouter(
    cluster: VLLMCluster,
    strategy: RoutingStrategy = RoutingStrategy.ROUND_ROBIN,
    health_check_interval: float = 30.0,
)
```

Routing Strategies:
- `ROUND_ROBIN` - Distribute requests evenly
- `RANDOM` - Random instance selection
- `LEAST_CONNECTIONS` - Route to least recently used
- `HEALTH_PRIORITY` - Prioritize healthiest instances

### VLLMClient

Direct client for vLLM's OpenAI-compatible API.

```python
VLLMClient(
    base_url: str,                  # vLLM server URL
    api_key: Optional[str] = None,  # API key (optional)
    timeout: float = 30.0,          # Request timeout
)
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Application                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  VLLMRouter / VLLMCluster                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Load Balancing │ Health Checks │ Failover │ Metrics  │  │
│  └───────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         ▼           ▼           ▼
    ┌────────┐  ┌────────┐  ┌────────┐
    │vLLM #1 │  │vLLM #2 │  │vLLM #3 │
    │:8000   │  │:8001   │  │:8002   │
    └────────┘  └────────┘  └────────┘
```

## ⚠️ Migration from v0.1.x

**Breaking Changes in v0.2.0:**

vLLM Manager v0.2.0 is a complete rewrite focused on cluster management rather than process management.

### Old API (v0.1.x) - REMOVED
```python
# ❌ No longer supported
from vllm_manager import VLLMManager

manager = VLLMManager(model="facebook/opt-125m")
manager.start(port=8000)  # This managed subprocess - REMOVED
```

### New API (v0.2.0+)
```python
# ✅ New approach - vLLM Manager manages clusters, not processes
from vllm_manager import VLLMCluster, VLLMInstance

# Start vLLM using official CLI
# vllm serve facebook/opt-125m --port 8000

# Then manage with vLLM Manager
cluster = VLLMCluster()
cluster.add_instance(VLLMInstance("server1", "http://localhost:8000"))
```

**Why the change?**
vLLM already provides excellent process management. vLLM Manager now focuses on what vLLM doesn't provide: multi-instance orchestration.

## 📄 License

MIT License

## 🤝 Contributing

Contributions welcome! Please feel free to submit issues and pull requests.

See [ROADMAP.md](ROADMAP.md) for planned features.

---

<div align="center">

**🎉 If you find this useful, please give us a Star!**

</div>
