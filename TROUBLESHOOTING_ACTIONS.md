# GitHub Actions 未触发 - 排查指南

## 🔍 问题现象

推送了 tag 但 GitHub Actions 没有触发。

---

## ✅ 排查步骤

### 步骤 1：检查 Actions 是否被禁用

1. 访问：https://github.com/AiKiAi-stack/vllm_startup/settings/actions
2. 找到 **Actions permissions**
3. 确保选择：**Allow all actions and reusable workflows**
4. 如果禁用了，启用后重新推送 tag

### 步骤 2：手动触发 Workflow

1. 访问：https://github.com/AiKiAi-stack/vllm_startup/actions/workflows/publish.yml
2. 点击右上角 **Run workflow** 按钮
3. 选择 **main** 分支
4. 点击 **Run workflow**

这会立即触发发布流程。

### 步骤 3：检查 Secret 配置

1. 访问：https://github.com/AiKiAi-stack/vllm_startup/settings/secrets/actions
2. 确认有 `PYPI_API_TOKEN` secret
3. 值格式：`pypi-AgEIcHlwaS5vcmc...`

### 步骤 4：检查 workflow 文件语法

运行以下命令验证：
```bash
# 安装 actionlint
pip install actionlint

# 验证 workflow
actionlint .github/workflows/publish.yml
```

或者访问：https://rhysd.github.io/actionlint/demo/

---

## 🛠️ 快速修复

### 方法 A：手动触发（最快）

```bash
# 1. 访问 GitHub
https://github.com/AiKiAi-stack/vllm_startup/actions

# 2. 点击 "Release to PyPI" workflow

# 3. 点击 "Run workflow" 按钮

# 4. 等待完成
```

### 方法 B：重新推送 tag

```bash
# 删除远程 tag
git push origin --delete v0.1.0

# 删除本地 tag
git tag -d v0.1.0

# 重新创建并推送
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0
```

### 方法 C：使用 workflow_dispatch

在 workflow 中添加手动触发支持（已添加）：

```yaml
on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:  # ← 允许手动触发
```

---

## 📋 常见原因

| 原因 | 解决方法 |
|------|----------|
| Actions 被禁用 | Settings → Actions → 启用 |
| 仓库是 private 但没有 plan | 升级 GitHub plan |
| workflow 文件有语法错误 | 使用 actionlint 验证 |
| Secret 配置错误 | 检查 PYPI_API_TOKEN |
| 推送到了错误的分支 | 确保推送到了 main |
| tag 格式不对 | 必须是 `v*` 格式 |

---

## 🔗 快速链接

- **Actions 页面**: https://github.com/AiKiAi-stack/vllm_startup/actions
- **Settings**: https://github.com/AiKiAi-stack/vllm_startup/settings
- **Secrets**: https://github.com/AiKiAi-stack/vllm_startup/settings/secrets/actions
- **Workflow 文件**: https://github.com/AiKiAi-stack/vllm_startup/blob/main/.github/workflows/publish.yml

---

## ✅ 验证清单

- [ ] Actions 已启用
- [ ] PYPI_API_TOKEN secret 已配置
- [ ] workflow 文件语法正确
- [ ] tag 格式是 `v*` (如 v0.1.0)
- [ ] 推送到了正确的仓库

---

**如果还是不行，手动触发 workflow 是最快的解决方案！**
