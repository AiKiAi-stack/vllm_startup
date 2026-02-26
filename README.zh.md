<div align="center">

<!-- Logo 待添加 -->
<!-- <img src="assets/logo.jpg" alt="vLLM Manager" width="512"> -->

# vLLM Manager: vLLM 服务器管理神器

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

## 🚀 特性亮点

- **🎯 两种启动模式**：参数化配置 或 完整命令执行
- **📝 全方位日志**：自动记录模型名称、日期和服务器标识
- **🛑 优雅关闭**：优雅终止进程，超时自动强制杀死
- **❤️ 健康监控**：内置健康检查和就绪检测
- **🖥️ 多服务器管理**：集群支持，同时运行多个实例
- **🔄 自动重启**：故障自动重启（可选）
- **🎮 CUDA 管理**：GPU 设备选择和资源管理
- **🔧 上下文管理器**：使用 `with` 语句优雅管理资源

## 📦 快速安装

```bash
# 确保已安装 vLLM
pip install vllm

# 安装 vLLM Manager
pip install vllm-manager

# 导入使用
from vllm_manager import VLLMManager
```

## 🎬 快速开始

### 基础用法

```python
from vllm_manager import VLLMManager

# 创建管理器并启动服务
manager = VLLMManager(model="facebook/opt-125m")
manager.start(host="0.0.0.0", port=8000)

# 检查状态
print(manager.get_status())
# {'running': True, 'pid': 12345, 'model': 'facebook/opt-125m', ...}

# 等待服务就绪
manager.wait_for_ready(timeout=60)

# 完成后停止
manager.stop()
```

### 参数化启动

```python
manager = VLLMManager(model="meta-llama/Llama-2-7b-hf")

manager.start(
    host="0.0.0.0",
    port=8000,
    tensor_parallel_size=2,      # 多 GPU 并行
    gpu_memory_utilization=0.9,
    max_model_len=4096,
    dtype="float16",
    quantization="awq",          # 可选：AWQ 量化
    api_key="your-api-key",      # 可选：API 认证
)
```

### 完整命令启动

```python
manager = VLLMManager()

# 使用完整命令启动
manager.start_command(
    "vllm serve facebook/opt-125m --port 8000 --tensor-parallel-size 2"
)

# 或使用列表形式
manager.start_command([
    "vllm", "serve", "facebook/opt-125m",
    "--port", "8000",
    "--host", "0.0.0.0"
])
```

### 上下文管理器

```python
from vllm_manager import VLLMManager

with VLLMManager(model="facebook/opt-125m") as manager:
    manager.start(port=8000)
    # 服务在这里运行
    # 退出上下文时自动停止
```

### 便捷函数

```python
from vllm_manager import serve

# 一行搞定
manager = serve("facebook/opt-125m", port=8001)
# ... 使用服务 ...
manager.stop()
```

## 🖥️ 高级功能

### 多服务器集群

```python
from vllm_manager import VLLMCluster

# 创建集群
cluster = VLLMCluster()

# 添加多个服务器
cluster.add_server("small", model="facebook/opt-125m", port=8001)
cluster.add_server("medium", model="facebook/opt-350m", port=8002, auto_restart=True)

# 全部启动
results = cluster.start_all()

# 健康检查
health = cluster.health_check()

# 获取状态
status = cluster.get_status()

# 全部停止
cluster.stop_all()
```

### 配置持久化

```python
from vllm_manager import VLLMCluster

# 保存配置
cluster = VLLMCluster()
cluster.add_server("model1", model="facebook/opt-125m", port=8001)
cluster.save_config("config.json")

# 加载配置
cluster = VLLMCluster.load_config("config.json")
```

### GPU 选择

```python
from vllm_manager import VLLMManager

# 选择特定 GPU
manager = VLLMManager(model="facebook/opt-125m")
manager.start(
    port=8000,
    cuda_devices=[0, 1],  # 使用 GPU 0 和 1
    tensor_parallel_size=2,
)
```

### 健康监控

```python
from vllm_manager import VLLMManager, health_monitor
import threading

manager = VLLMManager(model="facebook/opt-125m")
manager.start(port=8000)

# 在后台线程中启动健康监控
monitor_thread = threading.Thread(
    target=health_monitor,
    args=(manager,),
    kwargs={"interval": 30, "max_failures": 3},
    daemon=True
)
monitor_thread.start()
```

## 📖 API 参考

### VLLMManager

#### 初始化

```python
VLLMManager(
    model: Optional[str] = None,       # 模型名称/路径
    log_dir: Optional[Path] = None,    # 日志目录
    server_id: Optional[str] = None,   # 自定义服务器 ID
)
```

#### 方法

| 方法 | 描述 |
|------|------|
| `start(**kwargs)` | 参数化启动服务 |
| `start_command(cmd)` | 使用完整命令启动 |
| `stop(timeout=30, force=False)` | 优雅停止服务 |
| `is_running()` | 检查服务是否运行 |
| `get_pid()` | 获取进程 ID |
| `get_uptime()` | 获取运行时间 |
| `wait_for_ready(timeout=60)` | 等待服务就绪 |
| `get_log_file()` | 获取日志文件路径 |
| `get_status()` | 获取综合状态字典 |

#### 启动参数

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `model` | str | - | 模型名称或路径 |
| `host` | str | "0.0.0.0" | 绑定地址 |
| `port` | int | 8000 | 端口号 |
| `tensor_parallel_size` | int | 1 | GPU 并行数量 |
| `dtype` | str | "auto" | 数据类型 |
| `max_model_len` | int | None | 最大上下文长度 |
| `gpu_memory_utilization` | float | 0.9 | GPU 内存利用率 |
| `swap_space` | int | 4 | CPU 交换空间 (GB) |
| `quantization` | str | None | 量化方法 (awq, gptq 等) |
| `api_key` | str | None | API 认证密钥 |
| `cuda_devices` | List[int] | None | GPU 设备 ID 列表 |
| `additional_args` | List[str] | [] | 额外命令行参数 |

### VLLMCluster

#### 方法

| 方法 | 描述 |
|------|------|
| `add_server(name, model, port, **kwargs)` | 添加服务器实例 |
| `start_server(name)` | 启动指定服务器 |
| `stop_server(name)` | 停止指定服务器 |
| `start_all()` | 启动所有服务器 |
| `stop_all()` | 停止所有服务器 |
| `health_check(timeout=5)` | 检查所有服务器健康状态 |
| `get_status()` | 获取所有服务器状态 |
| `save_config(path)` | 保存配置到 JSON |
| `load_config(path)` | 从 JSON 加载配置 |

## 📁 日志文件

日志默认存储在 `./vllm_logs/` 目录下，命名格式：

```
vllm_{model_name}_{YYYYMMDD}_{server_id}.log
```

示例：
```
vllm_facebook_opt-125m_20260226_srv_20260226105451.log
```

日志格式：
```
2026-02-26 10:54:51 [INFO] [vllm.srv_20260226105451] VLLMManager 已初始化
2026-02-26 10:54:52 [INFO] [vllm.srv_20260226105451] 正在启动 vLLM 服务：vllm serve ...
2026-02-26 10:54:53 [INFO] [vllm.srv_20260226105451] vLLM 服务已启动，PID: 12345
```

## ⚠️ 错误处理

```python
from vllm_manager import VLLMManager

manager = VLLMManager(model="facebook/opt-125m")

try:
    manager.start(port=8000)
except RuntimeError as e:
    # 服务已在运行
    print(f"错误：{e}")
except ValueError as e:
    # 未指定模型
    print(f"错误：{e}")
except Exception as e:
    # 其他错误
    print(f"错误：{e}")
finally:
    manager.stop()
```

## 💡 使用示例

### 示例 1：简单服务

```python
from vllm_manager import VLLMManager

# 启动服务
manager = VLLMManager(model="facebook/opt-125m")
manager.start(port=8000)

# 保持运行
import time
while manager.is_running():
    time.sleep(1)
```

### 示例 2：生产环境部署

```python
from vllm_manager import VLLMManager
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 使用生产配置启动
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
    
    # 等待就绪
    if not manager.wait_for_ready(timeout=120):
        raise RuntimeError("服务启动失败")
    
    logger.info("服务已就绪！")
    
    # 保持运行
    while True:
        time.sleep(1)
        
except KeyboardInterrupt:
    logger.info("正在关闭...")
    manager.stop(timeout=60)
except Exception as e:
    logger.error(f"错误：{e}")
    manager.stop(force=True)
    raise
```

### 示例 3：多模型部署

```python
from vllm_manager import VLLMCluster

# 创建多模型集群
cluster = VLLMCluster(log_dir="/var/log/vllm")

# 添加模型
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

# 全部启动
cluster.start_all()

# 监控
import time
while True:
    status = cluster.get_status()
    print(f"状态：{status}")
    time.sleep(10)
```

## 📄 许可证

MIT License

## 🤝 贡献

欢迎贡献！请随时提交 Issue 和 Pull Request。

---

<div align="center">

**🎉 如果觉得有用，请给个 Star 支持一下！**

</div>
