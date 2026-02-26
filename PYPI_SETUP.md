# PyPI 自动发布配置指南

## 📋 概述

当前配置：**打版本标签** → **自动发布到 PyPI**

触发条件：推送 `v*` 格式的标签（如 `v0.1.0`, `v1.2.3`）

---

## 🔑 第一步：获取 PyPI API Token

### 1.1 注册/登录 PyPI

访问：https://pypi.org/account/login/

### 1.2 创建 API Token

1. 登录后访问：https://pypi.org/manage/account/token/
2. 点击 **"Add API token"**
3. 填写信息：
   - **Token name**: `github-vllm-startup` (任意名称)
   - **Scope**: 选择 **Entire account** (或限制特定项目)
   - **Valid until**: 可选过期时间，或留空永不过期
4. 点击 **"Create API token"**
5. **⚠️ 重要**：立即复制生成的 token（格式：`pypi-AgEIcHlwaS5vcmc...`）
   - **只显示一次！** 刷新页面上就看不到了
   - 如果丢失，需要重新创建

---

## 🔐 第二步：配置 GitHub Secrets

### 2.1 打开仓库设置

访问：https://github.com/AiKiAi-stack/vllm_startup/settings/secrets/actions

或手动操作：
1. 打开 https://github.com/AiKiAi-stack/vllm_startup
2. 点击 **"Settings"** 标签
3. 左侧菜单选择 **"Secrets and variables"** → **"Actions"**

### 2.2 添加 PyPI Token

1. 点击 **"New repository secret"**
2. 填写：
   - **Name**: `PYPI_API_TOKEN`
   - **Secret**: 粘贴刚才复制的 token（`pypi-AgEIcHlwaS5vcmc...`）
3. 点击 **"Add secret"**

### 2.3 验证配置

你应该看到：
```
Name: PYPI_API_TOKEN
Updated: just now
```

---

## 🚀 第三步：发布新版本

### 3.1 更新版本号

在发布前，更新以下两个文件的版本号：

**`pyproject.toml`**:
```toml
[project]
version = "0.1.0"  # 改为新版本号
```

**`src/vllm_manager/__init__.py`**:
```python
__version__ = "0.1.0"  # 改为新版本号
```

### 3.2 提交并打标签

```bash
cd vllm_manager_pkg

# 提交版本变更
git add pyproject.toml src/vllm_manager/__init__.py
git commit -m "chore: release v0.1.0"

# 打标签（格式必须是 v*）
git tag -a v0.1.0 -m "Release v0.1.0"

# 推送代码和标签
git push origin main
git push origin v0.1.0
```

### 3.3 查看自动发布

1. 访问：https://github.com/AiKiAi-stack/vllm_startup/actions
2. 应该看到 **"Release to PyPI"** 工作流正在运行
3. 等待完成（约 2-5 分钟）
4. 成功后访问：https://pypi.org/project/vllm-manager/

---

## 📝 完整发布流程示例

```bash
# 1. 克隆仓库（如果还没克隆）
git clone git@github.com:AiKiAi-stack/vllm_startup.git
cd vllm_startup

# 2. 确认要发布的内容
git log --oneline -5

# 3. 更新版本号（编辑文件）
vim pyproject.toml
vim src/vllm_manager/__init__.py

# 4. 提交变更
git add -A
git commit -m "chore: release v0.1.0"

# 5. 打标签
git tag -a v0.1.0 -m "Release v0.1.0 - Initial release"

# 6. 推送（触发自动发布）
git push origin main
git push origin v0.1.0

# 7. 等待并验证
# 访问 GitHub Actions 查看进度
# 访问 PyPI 验证发布成功
```

---

## ⚙️ 工作流程说明

当前 `.github/workflows/publish.yml` 执行步骤：

```yaml
1. Checkout code          # 拉取代码
2. Set up Python          # 设置 Python 3.11
3. Install dependencies   # 安装 build, twine
4. Build package          # 构建 wheel 和 sdist
5. Verify package         # twine 验证
6. Publish to PyPI        # 发布到 PyPI ✨
7. Test installation      # 验证安装成功
```

---

## 🔧 可选配置

### 使用 TestPyPI 测试

如果你想先测试发布流程，可以使用 TestPyPI：

#### 1. 获取 TestPyPI Token

访问：https://test.pypi.org/manage/account/token/

#### 2. 添加 TestPyPI Secret

Name: `TEST_PYPI_API_TOKEN`

#### 3. 修改 workflow（可选）

在 `publish.yml` 中添加 TestPyPI 发布任务：

```yaml
publish-to-testpypi:
  name: Publish to TestPyPI
  runs-on: ubuntu-latest
  environment:
    name: testpypi
    url: https://test.pypi.org/p/vllm-manager
  permissions:
    id-token: write
    contents: read
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    - run: pip install build twine
    - run: python -m build
    - run: twine check dist/*
    - uses: pypa/gh-action-pypi-publish@release/v1
      with:
        repository-url: https://test.pypi.org/legacy/
```

---

## ❓ 常见问题

### Q: 发布失败了怎么办？

**A:** 查看 GitHub Actions 日志：
1. 访问 https://github.com/AiKiAi-stack/vllm_startup/actions
2. 点击失败的 run
3. 查看详细错误信息

常见错误：
- **403 Forbidden**: Token 无效或权限不足
- **400 File already exists**: 版本号已存在
- **401 Unauthorized**: Token 错误

### Q: 如何重新发布同一版本？

**A:** PyPI 不允许覆盖已发布的版本。需要：
1. 增加版本号（如 0.1.0 → 0.1.1）
2. 删除旧标签：`git tag -d v0.1.0 && git push origin :refs/tags/v0.1.0`
3. 重新打标签发布

### Q: 可以每次 commit 都发布吗？

**A:** 不推荐！最佳实践是：
- **日常开发**: 只提交代码，不打标签
- **正式发布**: 打版本标签触发发布
- **原因**: 
  - PyPI 不允许覆盖已发布版本
  - 频繁发布会造成版本混乱
  - 语义化版本更有意义

### Q: 如何验证发布成功？

**A:** 三种方式：
```bash
# 1. 访问 PyPI 页面
https://pypi.org/project/vllm-manager/

# 2. pip 安装测试
pip install vllm-manager
python -c "import vllm_manager; print(vllm_manager.__version__)"

# 3. 查看 PyPI API
curl https://pypi.org/pypi/vllm-manager/json
```

---

## 📚 相关资源

- [PyPI 官方文档](https://pypi.org/help/)
- [gh-action-pypi-publish](https://github.com/pypa/gh-action-pypi-publish)
- [语义化版本规范](https://semver.org/)
- [GitHub Actions 文档](https://docs.github.com/en/actions)

---

**配置完成后，只需执行 `git push origin v*` 即可自动发布！** 🎉
