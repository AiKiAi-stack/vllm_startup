<div align="center">

# vLLM Manager

**多实例 vLLM 集群管理与日志收集工具**

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![vLLM](https://img.shields.io/badge/vLLM-Latest-brightgreen?style=flat&logo=cpu&logoColor=white)](https://github.com/vllm-project/vllm)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/vllm-manager?color=blue&logo=pypi&logoColor=white)](https://pypi.org/project/vllm-manager/)

**[English](README.md)** | **[中文](README.zh.md)**

</div>

---

## 📖 简介

vLLM Manager 提供多实例 vLLM 集群管理、自动日志收集和负载均衡功能。

- **启动 vLLM**：使用官方 CLI (`python -m vllm.entrypoints.openai.api_server`)
- **发送请求**：使用官方 OpenAI SDK (`from openai import OpenAI`)
- **集群管理**：自动启停、健康检查、故障转移
- **日志收集**：所有实例日志自动保存到文件

## ✨ 功能特性

- 🎯 **多实例管理**：一键启动/停止多个 vLLM 实例
- 📝 **自动日志**：日志文件按模型和端口命名，易于识别
- 🔄 **故障转移**：请求失败时自动重试其他实例
- ❤️ **健康检查**：持续监控实例健康状态
- 🔧 **OpenAI SDK**：返回标准 OpenAI 客户端，无缝兼容现有代码
- ⚖️ **负载均衡**：轮询策略分发请求

## 🛠️ 技术栈

- **Python** 3.8+
- **vLLM** - LLM 推理引擎
- **OpenAI SDK** - API 客户端
- **Requests** - HTTP 客户端

## 📦 安装

```bash
# 1. 安装 vLLM
pip install vllm

# 2. 安装依赖
pip install -r requirements.txt

# 或单独安装
pip install openai requests
```

## 🚀 快速开始

### 基础用法

```python
from vllm_manager import VLLMCluster, VLLMInstance

# 1. 创建集群
cluster = VLLMCluster(log_dir="./vllm_logs")

# 2. 添加实例
cluster.add_instance(VLLMInstance(
    name="server1",
    model="facebook/opt-125m",
    port=8000,
    gpu_memory_utilization=0.5,
))

# 3. 启动所有实例
cluster.start_all()

# 4. 获取 OpenAI 客户端
client = cluster.get_openai_client()

# 5. 发送请求（自动负载均衡）
response = client.completions.create(
    model="facebook/opt-125m",
    prompt="San Francisco is a",
)
print(response)

# 6. 停止集群
cluster.stop_all()
```

### 多模型示例

```python
from vllm_manager import VLLMCluster, VLLMInstance

cluster = VLLMCluster()

# 添加不同模型的实例
cluster.add_instance(VLLMInstance(
    name="qwen-server",
    model="Qwen/Qwen2.5-1.5B-Instruct",
    port=8000,
))

cluster.add_instance(VLLMInstance(
    name="llama-server",
    model="meta-llama/Llama-2-7b-chat",
    port=8001,
))

cluster.start_all()

# 查看每个实例的模型名称
for instance in cluster.instances.values():
    print(f"{instance.name}: {instance.served_model_name}")
# qwen-server: Qwen2.5-1.5B-Instruct
# llama-server: Llama-2-7b-chat

# 日志文件会自动包含模型名称
# vllm_Qwen2.5-1.5B-Instruct_8000_20260227_101234.log
# vllm_Llama-2-7b-chat_8001_20260227_101235.log
```

## 📖 API 参考

### VLLMInstance

```python
VLLMInstance(
    name: str,                    # 实例名称
    model: str,                   # 模型名称/路径
    port: int = 8000,             # 端口
    host: str = "0.0.0.0",        # 主机
    log_dir: Optional[Path] = None,
    
    # vLLM 参数（继承自 AsyncEngineArgs）
    gpu_memory_utilization: float = 0.9,
    tensor_parallel_size: int = 1,
    pipeline_parallel_size: int = 1,
    max_model_len: Optional[int] = None,
    quantization: Optional[str] = None,
    dtype: str = "auto",
    # ... 支持所有 AsyncEngineArgs 参数
)

# 属性
instance.served_model_name  # 模型名称（路径最后一部分）
instance.base_url           # http://host:port
instance.api_url            # http://host:port/v1
instance.log_file           # 日志文件路径
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

## 📝 日志管理

### 日志文件命名

日志文件按 **模型名称 + 端口 + 时间戳** 命名，便于区分不同实例：

```
./vllm_logs/
├── vllm_manager_20260227_101234.log          # Manager 日志
├── vllm_Qwen2.5-1.5B-Instruct_8000_101235.log  # Qwen 模型
└── vllm_Llama-2-7b-chat_8001_101236.log        # Llama 模型
```

### 查看日志

```python
from vllm_manager import LogAggregator

aggregator = LogAggregator(log_dir="./vllm_logs")

# 获取所有日志
logs = aggregator.get_all_logs(limit=100)
for log in logs:
    print(f"[{log.timestamp}] {log.instance}: {log.message}")

# 导出为 JSON
aggregator.export_json("logs.json")
```

## ❓ 常见问题

### Q: 为什么要用 vLLM Manager？

**A**: 当你需要同时运行多个 vLLM 实例（不同模型、不同 GPU）时，vLLM Manager 提供统一的集群管理和日志收集。

### Q: 支持哪些 vLLM 参数？

**A**: 所有 `AsyncEngineArgs` 的参数都支持，因为 `VLLMInstance` 继承自 `AsyncEngineArgs`。

### Q: 日志文件如何命名？

**A**: 格式为 `vllm_{model_name}_{port}_{timestamp}.log`，其中 `model_name` 是模型路径的最后一部分（如 `Qwen2.5-1.5B-Instruct`）。

### Q: 如何查看每个实例运行的模型？

**A**: 使用 `instance.served_model_name` 属性：
```python
for instance in cluster.instances.values():
    print(f"{instance.name}: {instance.served_model_name}")
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

```bash
# 1. Fork 项目
# 2. 创建分支 (git checkout -b feature/AmazingFeature)
# 3. 提交更改 (git commit -m 'Add some AmazingFeature')
# 4. 推送到分支 (git push origin feature/AmazingFeature)
# 5. 提交 Pull Request
```

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 📬 联系方式

- **项目地址**: https://github.com/AiKiAi-stack/vllm_startup
- **Issues**: https://github.com/AiKiAi-stack/vllm_startup/issues
- **作者**: AiKiAi-stack

## 🙏 致谢

- [vLLM](https://github.com/vllm-project/vllm) - LLM 推理引擎
- [OpenAI Python SDK](https://github.com/openai/openai-python) - API 客户端
