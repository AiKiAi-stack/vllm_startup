# vLLM Manager - Project Roadmap

## 🎯 项目重新定位

**核心问题**: vLLM 官方已经提供了完整的启动和管理能力，本项目不应该重复造轮子。

**新的价值主张**: 
vLLM Manager 不是 vLLM 的替代品，而是 **vLLM 的多实例编排器和集群管理工具**。

就像 Kubernetes 之于 Docker，vLLM Manager 之于 vLLM。

---

## 📊 功能分析

### ❌ 移除（vLLM 官方已提供）

| 功能 | vLLM 官方方案 | 说明 |
|------|--------------|------|
| 启动服务 | `entrypoints.llm` | 官方 Python API |
| HTTP API | OpenAI-compatible | 原生支持 completions/chat.completions |
| 健康检查 | `/health` 端点 | 内置健康检查 |
| 日志管理 | `--log-dir` 参数 | 官方日志配置 |
| 进程管理 | 官方进程管理 | 无需 wrapper |

### ✅ 保留（独特价值）

| 功能 | 价值 | 优先级 |
|------|------|--------|
| **多实例集群管理** | 同时管理多个 vLLM 实例 | 🔴 P0 |
| **负载均衡** | 在多个实例间智能路由请求 | 🔴 P0 |
| **自动故障转移** | 实例故障时自动重启/迁移 | 🔴 P0 |
| **统一配置管理** | 集群级别的配置保存/加载 | 🟡 P1 |
| **资源调度** | GPU 资源分配和限制 | 🟡 P1 |
| **监控聚合** | 多实例指标统一收集 | 🟡 P1 |
| **动态扩缩容** | 根据负载自动增减实例 | 🟢 P2 |

---

## 🗺️ 路线图

### Phase 1: 重构核心 (v0.2.0) - 当前阶段

**目标**: 移除冗余功能，聚焦集群管理

- [x] 分析当前代码和 vLLM 官方能力
- [ ] 移除 subprocess 启动逻辑
- [ ] 改为使用 vLLM 官方 API (`entrypoints.llm`)
- [ ] 重构 VLLMManager：从"进程包装器"变为"实例代理"
- [ ] 保留并强化 VLLMCluster 功能
- [ ] 更新文档和 README

### Phase 2: 负载均衡与路由 (v0.3.0)

**目标**: 实现请求路由和负载分发

- [ ] 实现 Round-Robin 负载均衡
- [ ] 实现基于 GPU 利用率的智能路由
- [ ] 提供统一的 API 入口（代理层）
- [ ] 支持会话粘性（Session Affinity）
- [ ] 实现请求队列和限流

### Phase 3: 高可用性 (v0.4.0)

**目标**: 故障检测和自动恢复

- [ ] 实现健康检查机制（调用 vLLM /health）
- [ ] 实例故障时自动重启
- [ ] 实例故障时请求自动路由到健康实例
- [ ] 支持热更新（不中断服务更新配置）
- [ ] 持久化状态和配置

### Phase 4: 资源管理 (v0.5.0)

**目标**: GPU 资源调度和优化

- [ ] GPU 资源池管理
- [ ] 实例级别的 GPU 限制
- [ ] 基于负载的动态扩缩容
- [ ] 资源使用监控和告警
- [ ] 成本优化建议

### Phase 5: 企业级特性 (v1.0.0)

**目标**: 生产环境就绪

- [ ] Web UI 管理界面
- [ ] REST API 控制面板
- [ ] 多租户支持
- [ ] 认证和授权
- [ ] 详细监控指标（Prometheus/Grafana）
- [ ] 完整的测试覆盖

---

## 🏗️ 架构设计

### 新的类设计

```python
# VLLMInstance - 单个 vLLM 实例的代理
class VLLMInstance:
    """
    代理单个 vLLM 实例，使用官方 API。
    不负责启动/停止进程，只负责与运行中的实例通信。
    """
    def __init__(self, name: str, base_url: str, ...)
    def chat_completion(self, ...)
    def completion(self, ...)
    def health_check(self) -> bool
    def get_metrics(self) -> Metrics

# VLLMCluster - 集群管理
class VLLMCluster:
    """
    管理多个 VLLMInstance，提供负载均衡和高可用。
    """
    def __init__(self, ...)
    def add_instance(self, instance: VLLMInstance)
    def route_request(self, request) -> VLLMInstance
    def get_healthy_instances(self) -> List[VLLMInstance]
    def auto_restart_unhealthy(self)
    
# VLLMRouter - 请求路由
class VLLMRouter:
    """
    提供统一的 API 入口，将请求路由到合适的实例。
    """
    def __init__(self, cluster: VLLMCluster)
    async def chat_completion(self, ...)
    async def completion(self, ...)
```

---

## 📝 迁移指南

### 旧用法（将被移除）
```python
# ❌ 不再支持 - 使用 subprocess 启动
manager = VLLMManager(model="facebook/opt-125m")
manager.start(port=8000)  # 启动子进程
```

### 新用法
```python
# ✅ 新方式 - vLLM Manager 只管理已运行的实例
from vllm_manager import VLLMCluster, VLLMInstance

# 启动 vLLM（使用官方方式）
# vllm serve facebook/opt-125m --port 8000
# vllm serve facebook/opt-125m --port 8001

# vLLM Manager 接管管理
cluster = VLLMCluster()
cluster.add_instance(VLLMInstance("server1", "http://localhost:8000"))
cluster.add_instance(VLLMInstance("server2", "http://localhost:8001"))

# 使用集群（自动负载均衡）
response = cluster.chat_completion(
    model="facebook/opt-125m",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

---

## 🎓 设计理念

1. **Do One Thing Well**: 不替代 vLLM，而是增强 vLLM 的多实例能力
2. **Composability**: 与 vLLM 官方工具链无缝集成
3. **Production-Ready**: 关注高可用、可观测性、易运维
4. **Pythonic API**: 简洁、直观的 Python 接口

---

## 📚 参考

- [vLLM Documentation](https://docs.vllm.ai/)
- [vLLM GitHub](https://github.com/vllm-project/vllm)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)

---

**Last Updated**: 2026-02-26
**Version**: 0.2.0-planning
