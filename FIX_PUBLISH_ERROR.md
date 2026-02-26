# 修复 PyPI 发布错误 - Trusted Publishing 配置

## ❌ 错误原因

```
invalid-publisher: valid token, but no corresponding publisher
```

GitHub Actions 使用 **OIDC Trusted Publishing** 方式发布到 PyPI，但 PyPI 上没有配置对应的 trusted publisher。

---

## ✅ 解决方案一：在 PyPI 配置 Trusted Publishing（推荐）

### 步骤 1：访问 PyPI 项目页面

1. 访问：https://pypi.org/manage/project/vllm-manager/settings/
2. 如果项目还不存在，先创建一个空项目（发布时会创建）

### 步骤 2：添加 Trusted Publisher

1. 在 **Publishing settings** 部分，点击 **"Add trusted publisher"**
2. 选择 **"GitHub Actions"**
3. 填写信息：

   | 字段 | 值 |
   |------|-----|
   | **Workflow name** | `publish.yml` |
   | **Environment** | `pypi` (可选，留空也可以) |
   | **Owner** | `AiKiAi-stack` |
   | **Repository** | `vllm_startup` |

4. 点击 **"Add"**

### 步骤 3：重新触发发布

```bash
# 删除并重新推送标签
git tag -d v0.1.0
git push origin :refs/tags/v0.1.0

# 重新打标签推送
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0
```

---

## ✅ 解决方案二：使用 API Token（如果 Trusted Publishing 配置失败）

如果 Trusted Publishing 配置不成功，可以改用传统的 API Token 方式。

### 修改 publish.yml

编辑 `.github/workflows/publish.yml`：

```yaml
name: Release to PyPI

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:

jobs:
  build-and-publish:
    name: Build and publish to PyPI
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install build dependencies
        run: |
          python -m pip install --upgrade pip
          pip install build twine

      - name: Build package
        run: python -m build

      - name: Verify package
        run: twine check dist/*

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          print-hash: true
          # 使用 API Token 方式
          password: ${{ secrets.PYPI_API_TOKEN }}
```

### 确保 Secret 已配置

1. 访问：https://github.com/AiKiAi-stack/vllm_startup/settings/secrets/actions
2. 确认有以下 Secret：
   - **Name**: `PYPI_API_TOKEN`
   - **Value**: `pypi-AgEIcHlwaS5vcmc...` (你的 PyPI API token)

### 重新触发发布

```bash
# 删除并重新推送标签
git tag -d v0.1.0
git push origin :refs/tags/v0.1.0

# 重新打标签推送
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0
```

---

## 🔍 如何检查问题

### 检查 GitHub Actions 日志

1. 访问：https://github.com/AiKiAi-stack/vllm_startup/actions
2. 点击失败的 run
3. 查看详细错误信息

### 检查 PyPI Trusted Publisher 配置

1. 访问：https://pypi.org/manage/project/vllm-manager/settings/
2. 查看 **Trusted publishers** 部分
3. 确认有以下配置：
   - Owner: `AiKiAi-stack`
   - Repository: `vllm_startup`
   - Workflow: `publish.yml`

---

## 📊 两种方案对比

| 方案 | 优点 | 缺点 |
|------|------|------|
| **Trusted Publishing** | - 无需管理 token<br>- 更安全（OIDC）<br>- 自动过期 | - 需要额外配置<br>- PyPI 项目必须存在 |
| **API Token** | - 配置简单<br>- 立即可用 | - 需要管理 token<br>- token 可能过期 |

---

## 🎯 快速解决步骤（推荐顺序）

### 方法 A：配置 Trusted Publishing

```bash
# 1. 访问 PyPI 项目设置
# https://pypi.org/manage/project/vllm-manager/settings/

# 2. 添加 Trusted Publisher:
#    Owner: AiKiAi-stack
#    Repository: vllm_startup
#    Workflow: publish.yml

# 3. 重新推送标签
git tag -d v0.1.0 && git push origin :refs/tags/v0.1.0
git tag -a v0.1.0 -m "Release v0.1.0" && git push origin v0.1.0
```

### 方法 B：使用 API Token（如果方法 A 失败）

```bash
# 1. 确认 Secret 已配置
# Settings → Secrets and variables → Actions
# PYPI_API_TOKEN = pypi-AgEIcHlwaS5vcmc...

# 2. 更新 publish.yml（添加 password 参数）

# 3. 重新推送标签
git tag -d v0.1.0 && git push origin :refs/tags/v0.1.0
git tag -a v0.1.0 -m "Release v0.1.0" && git push origin v0.1.0
```

---

## ⚠️ 注意事项

1. **PyPI 项目名必须匹配**: `vllm-manager`（仓库名可以不同）
2. **第一次发布**: PyPI 上可能还没有项目，第一次发布会自动创建
3. **Token 权限**: 确保 API Token 有发布权限
4. **Environment**: 如果 workflow 中配置了 `environment: pypi`，需要在 PyPI 设置中匹配

---

## 🔗 相关资源

- [PyPI Trusted Publishing 文档](https://docs.pypi.org/trusted-publishers/)
- [gh-action-pypi-publish](https://github.com/pypa/gh-action-pypi-publish)
- [PyPI 项目管理](https://pypi.org/manage/project/)

---

**推荐先尝试方法 A（Trusted Publishing），如果不行再用方法 B（API Token）！**
