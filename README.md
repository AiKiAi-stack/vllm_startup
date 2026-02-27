<div align="center">

<!-- Logo Placeholder -->
<!-- <img src="assets/logo.jpg" alt="vLLM Manager" width="512"> -->

# vLLM Manager: vLLM 集群编排器

### 一次编写，终生使用，妈妈再也不用担心我的 vLLM 了

  <p>
    <img src="https://img.shields.io/badge/Python-3.8+-3776AB?style=flat&logo=python&logoColor=white" alt="Python">
    <img src="https://img.shields.io/badge/vLLM-Ready-brightgreen?style=flat&logo=cpu&logoColor=white" alt="vLLM Ready">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
    <br>
    <a href="https://pypi.org/project/vllm-manager/"><img src="https://img.shields.io/pypi/v/vllm-manager?color=blue&logo=pypi&logoColor=white" alt="PyPI"></a>
    <a href="https://github.com/AiKiAi-stack/vllm_startup"><img src="https://img.shields.io/github/stars/AiKiAi-stack/vllm_startup?style=flat&logo=github" alt="GitHub Stars"></a>
    <a href="https://github.com/AiKiAi-stack/vllm_startup/issues"><img src="https://img.shields.io/github/issues/AiKiAi-stack/vllm_startup" alt="Issues"></a>
  </p>

**中文** | [English](README.md)

</div>

---

## 🎯 vLLM Manager 是什么？

**vLLM Manager 使用官方 vLLM CLI 启动服务，使用官方 OpenAI SDK 发送请求，专注于日志管理和多实例编排。**

可以把它想象成：
- **vLLM 的 Kubernetes** - 将多个 vLLM 实例作为集群管理
- **日志收集器** - 自动捕获和聚合所有实例的日志
- **高可用层** - 自动故障转移和健康监控

### 核心设计原则

1. **启动 vLLM** → 使用官方命令 `python -m vllm.entrypoints.openai.api_server --model ...`
2. **发送请求** → 使用官方 OpenAI SDK `from openai import OpenAI`
3. **vLLM Manager 负责** → 日志管理 + 多实例编排

## 🚀 功能特性

- **🎯 多实例集群管理**：启动/停止多个 vLLM 实例
- **📝 自动日志收集**：所有实例日志自动保存到文件
- **🔄 自动故障转移**：请求失败时自动重试其他实例
- **❤️ 健康监控**：持续健康检查
- **🔧 OpenAI SDK 集成**：返回标准 OpenAI 客户端
- **🌐 负载均衡**：轮询策略分发请求

## 📦 安装

```bash
# 先安装 vLLM
pip install vllm

# 安装依赖
pip install openai requests

# 安装 vLLM Manager
pip install vllm-manager
```

## 🎬 快速开始

### 1. 创建集群并添加实例

```python
from vllm_manager import VLLMCluster, VLLMInstance

# 创建集群
cluster = VLLMCluster(log_dir="./vllm_logs")

# 添加实例（配置 vLLM 参数）
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

### 2. 启动所有实例

```python
# 启动所有实例（使用 vLLM 官方 CLI）
results = cluster.start_all()
print(f"Start results: {results}")

# 检查健康状态
health = cluster.health_check()
print(f"Health: {health}")
```

### 3. 获取 OpenAI 客户端并发送请求

```python
from openai import OpenAI

# 获取负载均衡的客户端
client = cluster.get_openai_client()

# 使用标准 OpenAI SDK API
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

### 4. 查看日志

```python
from vllm_manager import LogAggregator

# 聚合所有日志
aggregator = LogAggregator(log_dir="./vllm_logs")

# 获取所有日志
logs = aggregator.get_all_logs(limit=100)
for log in logs:
    print(f"[{log.timestamp}] {log.instance}: {log.message}")

# 导出为 JSON
aggregator.export_json("logs.json")
```

### 5. 停止集群

```python
# 停止所有实例
cluster.stop_all()

# 或使用上下文管理器
with VLLMCluster() as cluster:
    cluster.add_instance(VLLMInstance("s1", model="facebook/opt-125m", port=8000))
    cluster.start_all()
    
    client = cluster.get_openai_client()
    response = client.completions.create(model="facebook/opt-125m", prompt="Hello!")
    print(response)
# 退出时自动停止所有实例
```

## 🖥️ 高级用法

### 配置 vLLM 参数

```python
VLLMInstance(
    name="gpu-server",
    model="Qwen/Qwen2.5-1.5B-Instruct",
    port=8000,
    # GPU 配置
    gpu_memory_utilization=0.5,
    tensor_parallel_size=2,
    max_num_seqs=2,
    max_model_len=128,
    # 量化配置
    quantization="awq_marlin",
    dtype="float16",
    # 其他配置
    trust_remote_code=True,
    enforce_eager=True,
    api_key="your-api-key",
)
```

### 自定义日志目录

```python
from pathlib import Path

cluster = VLLMCluster(log_dir=Path("/var/log/vllm"))
```

### 手动控制单个实例

```python
instance = VLLMInstance(
    name="solo",
    model="facebook/opt-125m",
    port=8000
)

# 启动
instance.start()

# 获取客户端
client = instance.get_client()
response = client.completions.create(
    model="facebook/opt-125m",
    prompt="Test"
)

# 查看日志文件
print(f"Log file: {instance.log_file}")

# 停止
instance.stop()
```

## 📖 API 参考

### VLLMInstance

管理单个 vLLM 实例。

```python
VLLMInstance(
    name: str,                    # 实例名称
    model: str,                   # 模型名称/路径
    port: int = 8000,             # 端口
    log_dir: Optional[Path] = None,  # 日志目录
    gpu_memory_utilization: float = 0.9,
    max_num_seqs: int = 256,
    tensor_parallel_size: int = 1,
    quantization: Optional[str] = None,
    trust_remote_code: bool = False,
    enforce_eager: bool = False,
    **kwargs
)
```

方法：
- `start()` - 启动 vLLM 实例
- `stop()` - 停止实例
- `is_running()` - 检查是否运行中
- `is_healthy()` - 检查健康状态
- `get_client()` - 获取 OpenAI 客户端
- `get_status()` - 获取状态信息

### VLLMCluster

管理多个 vLLM 实例。

```python
VLLMCluster(
    log_dir: Optional[Path] = None,  # 日志目录
    name: str = "default"           # 集群名称
)
```

方法：
- `add_instance(instance)` - 添加实例
- `start_all()` - 启动所有实例
- `stop_all()` - 停止所有实例
- `health_check()` - 健康检查
- `get_openai_client()` - 获取负载均衡客户端
- `get_status()` - 获取所有实例状态

### VLLMLogger

日志配置。

```python
VLLMLogger(
    log_dir: Optional[Path] = None,
    level: int = logging.INFO,
)
```

### LogAggregator

日志聚合器。

```python
aggregator = LogAggregator(log_dir="./vllm_logs")
logs = aggregator.get_all_logs(limit=100)
aggregator.export_json("output.json")
```

## 🏗️ 架构

```
┌─────────────────────────────────────────────────────────────┐
│                    你的应用程序                              │
│                  from openai import OpenAI                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              VLLMCluster / LoadBalancedClient               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  负载均衡 │ 自动重试 │ 健康检查 │ 日志收集              │  │
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
         │   日志文件自动保存      │
         │  ./vllm_logs/         │
         └───────────────────────┘
```

## 📝 日志示例

启动后，所有日志自动保存到 `./vllm_logs/`：

```
./vllm_logs/
├── vllm_manager_20260227_101234.log  # Manager 日志
├── vllm_server1_20260227_101235.log  # Server 1 日志
└── vllm_server2_20260227_101236.log  # Server 2 日志
```

日志格式：
```
2026-02-27 10:12:35 [INFO] [vllm_manager.server1] VLLMInstance 'server1' initialized
2026-02-27 10:12:35 [INFO] [vllm_manager.server1] Starting vLLM: python -m vllm.entrypoints.openai.api_server ...
2026-02-27 10:12:40 [INFO] [vllm_manager.server1] vLLM started with PID: 12345
2026-02-27 10:12:45 [INFO] [vllm_manager.server1] vLLM is healthy and ready
```

## 📄 许可证

MIT License

## 🤝 贡献

欢迎贡献！请随时提交 Issue 和 Pull Request。

查看 [ROADMAP.md](ROADMAP.md) 了解计划中的功能。

---

<div align="center">

**🎉 如果觉得有用，请给我们一个 Star！**

</div>
