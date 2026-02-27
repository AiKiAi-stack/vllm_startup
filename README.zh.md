<div align="center">

<!-- Logo 占位符 -->
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

**vLLM Manager 不是 vLLM 的替代品。它为 vLLM 增加了多实例编排能力。**

可以把它想象成：
- **vLLM 的 Kubernetes** - 将多个 vLLM 实例作为集群管理
- **LLM 的负载均衡器** - 跨实例的智能请求路由
- **高可用层** - 自动故障转移和健康监控

### 为什么需要 vLLM Manager？

虽然 vLLM 提供了优秀的单实例服务能力，但生产环境部署通常需要：

| 需求 | 仅使用 vLLM | 配合 vLLM Manager |
|------|------------|------------------|
| 不同 GPU 上的多模型 | ❌ 手动配置 | ✅ 自动编排 |
| 跨实例负载均衡 | ❌ 不支持 | ✅ 内置路由策略 |
| 自动故障转移 | ❌ 不支持 | ✅ 健康检查 & 自动重启 |
| 统一 API 端点 | ❌ 多端口 | ✅ 单一入口 |
| 请求队列 | ❌ 不支持 | ✅ 内置队列管理 |

## 🚀 功能特性

- **🎯 多实例集群管理**：将多个 vLLM 实例作为统一集群管理
- **⚖️ 智能负载均衡**：使用轮询、随机或健康优先策略路由请求
- **🔄 自动故障转移**：自动检测不健康实例并路由到健康实例
- **❤️ 健康监控**：持续健康检查与自动恢复
- **📊 请求指标**：跟踪每个实例的延迟、错误率和吞吐量
- **🔧 Pythonic API**：简单直观的集群操作接口
- **🌐 OpenAI 兼容**：与 vLLM 原生 OpenAI 兼容 API 配合使用

## 📦 安装

```bash
# 先安装 vLLM
pip install vllm

# 安装 vLLM Manager
pip install vllm-manager
```

## 🎬 快速开始

### 1. 启动 vLLM 实例

首先，使用官方 vLLM CLI 启动你的服务器：

```bash
# 终端 1 - 服务器 1
vllm serve facebook/opt-125m --port 8000

# 终端 2 - 服务器 2
vllm serve facebook/opt-350m --port 8001
```

### 2. 创建集群

```python
from vllm_manager import VLLMCluster, VLLMInstance

# 创建集群
cluster = VLLMCluster()

# 添加实例（假设 vLLM 已在运行）
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

# 检查健康状态
health = cluster.health_check()
print(f"健康状态: {health}")
```

### 3. 使用负载均衡路由请求

```python
from vllm_manager import VLLMRouter, RoutingStrategy

# 创建轮询策略的路由器
router = VLLMRouter(cluster, strategy=RoutingStrategy.ROUND_ROBIN)

# 发送请求（自动负载均衡）
response = router.chat_completion(
    model="facebook/opt-125m",
    messages=[{"role": "user", "content": "你好，最近怎么样？"}]
)

print(response["choices"][0]["message"]["content"])
```

### 4. 直接使用集群

```python
# 对话补全（自动路由到合适的实例）
response = cluster.chat_completion(
    model="facebook/opt-125m",
    messages=[{"role": "user", "content": "给我讲个笑话"}]
)

# 文本补全
response = cluster.completion(
    model="facebook/opt-350m",
    prompt="从前有座山",
    max_tokens=100
)

# 获取指标
metrics = cluster.get_metrics()
print(f"集群指标: {metrics}")
```

## 🖥️ 高级用法

### 配置持久化

```python
# 保存集群配置
cluster.save_config("cluster.json")

# 之后加载配置
cluster = VLLMCluster.load_config("cluster.json")
```

### 自定义路由策略

```python
from vllm_manager import RoutingStrategy

# 健康优先：路由到最健康的实例
router = VLLMRouter(cluster, strategy=RoutingStrategy.HEALTH_PRIORITY)

# 最少连接：路由到最不忙的实例
router = VLLMRouter(cluster, strategy=RoutingStrategy.LEAST_CONNECTIONS)
```

### 直接客户端访问

```python
from vllm_manager import VLLMClient

# 直接连接到 vLLM 实例
client = VLLMClient(base_url="http://localhost:8000")

# 健康检查
if client.health_check():
    response = client.chat_completion(
        model="facebook/opt-125m",
        messages=[{"role": "user", "content": "你好！"}]
    )
```

### 故障时自动重启

```python
# 为关键实例启用自动重启
cluster.add_instance(VLLMInstance(
    name="critical-server",
    base_url="http://localhost:8000",
    auto_restart=True,
    max_restarts=3
))

# 健康检查会自动重启失败的实例
cluster.health_check()
```

## 📖 API 参考

### VLLMInstance

代表单个 vLLM 实例。

```python
VLLMInstance(
    name: str,                    # 唯一实例名称
    base_url: str,                 # vLLM 服务器 URL
    model: Optional[str] = None,   # 模型名称（可选）
    api_key: Optional[str] = None, # API 密钥（可选）
    auto_restart: bool = False,    # 启用自动重启
    max_restarts: int = 3,         # 最大重启次数
)
```

方法：
- `health_check()` - 检查实例是否健康
- `chat_completion(**kwargs)` - 发送对话补全请求
- `completion(**kwargs)` - 发送文本补全请求
- `embedding(**kwargs)` - 发送嵌入请求
- `get_metrics()` - 获取实例指标

### VLLMCluster

管理多个 VLLMInstance 对象。

```python
VLLMCluster()
```

方法：
- `add_instance(instance)` - 添加实例到集群
- `remove_instance(name)` - 从集群移除实例
- `health_check()` - 检查所有实例的健康状态
- `get_healthy_instances()` - 获取健康实例列表
- `chat_completion(**kwargs)` - 路由对话补全请求
- `completion(**kwargs)` - 路由补全请求
- `get_metrics()` - 获取所有实例的指标
- `save_config(path)` - 保存配置到 JSON
- `load_config(path)` - 从 JSON 加载配置

### VLLMRouter

具有多种策略的智能请求路由器。

```python
VLLMRouter(
    cluster: VLLMCluster,
    strategy: RoutingStrategy = RoutingStrategy.ROUND_ROBIN,
    health_check_interval: float = 30.0,
)
```

路由策略：
- `ROUND_ROBIN` - 均匀分配请求
- `RANDOM` - 随机选择实例
- `LEAST_CONNECTIONS` - 路由到最近最少使用
- `HEALTH_PRIORITY` - 优先选择最健康的实例

### VLLMClient

vLLM OpenAI 兼容 API 的直接客户端。

```python
VLLMClient(
    base_url: str,                  # vLLM 服务器 URL
    api_key: Optional[str] = None,  # API 密钥（可选）
    timeout: float = 30.0,          # 请求超时时间
)
```

## 🏗️ 架构

```
┌─────────────────────────────────────────────────────────────┐
│                    你的应用程序                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  VLLMRouter / VLLMCluster                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  负载均衡 │ 健康检查 │ 故障转移 │ 指标监控              │  │
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

## ⚠️ 从 v0.1.x 迁移

**v0.2.0 中的破坏性变更：**

vLLM Manager v0.2.0 是一次完全重写，专注于集群管理而非进程管理。

### 旧 API (v0.1.x) - 已移除
```python
# ❌ 不再支持
from vllm_manager import VLLMManager

manager = VLLMManager(model="facebook/opt-125m")
manager.start(port=8000)  # 这管理子进程 - 已移除
```

### 新 API (v0.2.0+)
```python
# ✅ 新方式 - vLLM Manager 管理集群，而非进程
from vllm_manager import VLLMCluster, VLLMInstance

# 使用官方 CLI 启动 vLLM
# vllm serve facebook/opt-125m --port 8000

# 然后使用 vLLM Manager 管理
cluster = VLLMCluster()
cluster.add_instance(VLLMInstance("server1", "http://localhost:8000"))
```

**为什么改变？**
vLLM 已经提供了优秀的进程管理。vLLM Manager 现在专注于 vLLM 不提供的内容：多实例编排。

## 📄 许可证

MIT License

## 🤝 贡献

欢迎贡献！请随时提交 Issue 和 Pull Request。

查看 [ROADMAP.md](ROADMAP.md) 了解计划中的功能。

---

<div align="center">

**🎉 如果觉得有用，请给我们一个 Star！**

</div>
