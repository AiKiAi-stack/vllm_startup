# vLLM Manager - PyPI 发布指南

## 📦 包结构

```
vllm_manager_pkg/
├── pyproject.toml          # PyPI 包配置（元数据、依赖、构建配置）
├── README.md               # 包文档（显示在 PyPI 页面）
├── LICENSE                 # 开源许可证
├── MANIFEST.in             # 包包含文件清单
├── src/
│   └── vllm_manager/
│       ├── __init__.py     # 包入口，导出所有公共 API
│       ├── core.py         # VLLMManager 核心实现
│       ├── enhanced.py     # VLLMCluster 增强功能
│       └── py.typed        # 类型注解标记
├── tests/
│   └── test_vllm_manager.py  # 测试套件
└── .github/
    └── workflows/
        └── publish.yml     # GitHub Actions 自动发布
```

## 🚀 快速开始

### 安装（发布后）

```bash
# 从 PyPI 安装
pip install vllm-manager

# 使用示例
from vllm_manager import VLLMManager

manager = VLLMManager(model="facebook/opt-125m")
manager.start(port=8000)
```

### 本地开发和测试

```bash
# 进入包目录
cd vllm_manager_pkg

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/ -v

# 构建包
python -m build

# 本地安装测试
pip install dist/vllm_manager-0.1.0-py3-none-any.whl
```

## 📤 发布到 PyPI

### 准备工作

1. **注册 PyPI 账号**
   - 访问 https://pypi.org/account/register/
   - 验证邮箱

2. **获取 API Token**
   - 访问 https://pypi.org/manage/account/token/
   - 创建新的 API token
   - 保存 token（格式：`pypi-AgEIcHlwaS5vcmc...`）

3. **配置账号信息**
   
   在项目根目录创建 `~/.pypirc`：
   ```ini
   [distutils]
   index-servers =
       pypi
       testpypi

   [pypi]
   username = __token__
   password = pypi-AgEIcHlwaS5vcmc...

   [testpypi]
   repository = https://test.pypi.org/legacy/
   username = __token__
   password = pypi-AgEIcHlwaS5vcmc...
   ```

### 发布流程

#### 1. 更新版本号

编辑 `pyproject.toml` 和 `src/vllm_manager/__init__.py`：

```toml
# pyproject.toml
[project]
version = "0.1.0"  # 遵循语义化版本：major.minor.patch
```

```python
# __init__.py
__version__ = "0.1.0"
```

#### 2. 构建包

```bash
cd vllm_manager_pkg
python -m build
```

这会生成：
- `dist/vllm_manager-0.1.0.tar.gz` (源码分发包)
- `dist/vllm_manager-0.1.0-py3-none-any.whl` (wheel 包)

#### 3. 验证包

```bash
# 检查元数据
twine check dist/*

# 应该看到：
# Checking dist/vllm_manager-0.1.0-py3-none-any.whl: PASSED
# Checking dist/vllm_manager-0.1.0.tar.gz: PASSED
```

#### 4. 发布到 TestPyPI（推荐先测试）

```bash
twine upload --repository testpypi dist/*
```

验证 TestPyPI 安装：
```bash
pip install --index-url https://test.pypi.org/simple/ vllm-manager
```

#### 5. 发布到正式 PyPI

```bash
twine upload dist/*
```

上传成功后，访问：https://pypi.org/project/vllm-manager/

### 使用 GitHub Actions 自动发布

1. **配置 PyPI 环境变量**

   在 GitHub 仓库设置中：
   - Settings → Secrets and variables → Actions
   - 添加新 secret：`PYPI_API_TOKEN`，值为你的 PyPI API token

2. **打标签发布**

   ```bash
   # 更新版本号后，打标签
   git tag v0.1.0
   git push origin v0.1.0
   ```

   GitHub Actions 会自动：
   - 构建包
   - 验证包
   - 发布到 PyPI

## 📝 版本管理

遵循 [语义化版本 2.0.0](https://semver.org/)：

- **MAJOR.MINOR.PATCH** (例如：1.2.3)
  - MAJOR: 不兼容的 API 变更
  - MINOR: 向后兼容的功能新增
  - PATCH: 向后兼容的问题修复

### 发布新版本 checklist

- [ ] 更新 `pyproject.toml` 中的 `version`
- [ ] 更新 `src/vllm_manager/__init__.py` 中的 `__version__`
- [ ] 更新 `CHANGELOG.md` 记录变更
- [ ] 运行测试确保通过：`pytest tests/ -v`
- [ ] 构建包：`python -m build`
- [ ] 验证包：`twine check dist/*`
- [ ] 打 git 标签：`git tag v0.1.0 && git push origin v0.1.0`
- [ ] 上传到 PyPI：`twine upload dist/*`

## 🔧 修改作者信息

在发布前，请更新以下文件中的作者信息：

### pyproject.toml
```toml
[project]
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
```

### src/vllm_manager/__init__.py
```python
__author__ = "Your Name"
__author_email__ = "your.email@example.com"
```

### pyproject.toml URLs
```toml
[project.urls]
Homepage = "https://github.com/YOUR_USERNAME/vllm-manager"
```

## 📊 PyPI 项目优化

### 提高包的可发现性

1. **Keywords** - 在 `pyproject.toml` 中添加相关关键词
2. **Classifiers** - 添加适当的分类标签
3. **Description** - 写清晰的包描述

### 提升下载量

1. **完善的 README** - 包含快速开始、API 文档、示例
2. **清晰的文档** - 使用 docstring 和类型注解
3. **测试覆盖** - 展示包的质量
4. **持续维护** - 及时响应 issue 和 PR

## 🛠️ 故障排除

### 常见问题

**问题：`twine upload` 认证失败**
```
HTTPError: 401 Unauthorized
```
解决：检查 `~/.pypirc` 配置或设置 `TWINE_USERNAME` 和 `TWINE_PASSWORD` 环境变量

**问题：包名已被占用**
```
HTTPError: 400 This name has already been taken
```
解决：更换包名，如 `vllm-manager-utils`

**问题：构建失败**
```
ERROR: Failed to build 'vllm-manager'
```
解决：运行 `python -m build --no-isolation` 查看详细错误

## 📚 相关资源

- [PyPI 官方文档](https://pypi.org/help/)
- [packaging.python.org](https://packaging.python.org/)
- [twine 文档](https://twine.readthedocs.io/)
- [语义化版本](https://semver.org/)
- [GitHub Actions 文档](https://docs.github.com/en/actions)

---

**祝发布顺利！🎉**
