# API Target 修复：确保上线版本使用 db 模式

## 问题

上线版本（Vercel）显示 `[API] Target: mock`，导致使用了旧 API `/api/articles/{id}` 而非 `/api/v2/texts/{id}`。

## 原因分析

`getApiTarget()` 函数的优先级：
1. URL 参数 `?api=mock` 或 `?api=db`
2. localStorage 中的 `API_TARGET`（可能之前测试时设置了 `mock`）
3. 环境变量 `VITE_API_TARGET`
4. 默认值 `'db'`

如果用户之前访问过带有 `?api=mock` 的 URL，或者 localStorage 中保存了 `mock`，就会导致上线版本使用 `mock` 模式。

## 修复方案

**强制生产环境使用 `db` 模式**，忽略 URL 参数和 localStorage 设置。

### 修改内容

修改 `frontend/my-web-ui/src/services/api.js` 的 `getApiTarget()` 函数：

1. **检测生产环境**：
   - 使用 `import.meta.env.PROD`（Vite 内置）
   - 或检查 hostname 不包含 `localhost` 或 `127.0.0.1`

2. **生产环境强制返回 `'db'`**：
   - 忽略 URL 参数
   - 忽略 localStorage
   - 忽略环境变量（可选，建议也忽略）

3. **开发环境保持原有逻辑**：
   - 允许通过 URL 参数、localStorage 或环境变量切换

## 验证步骤

1. **部署到 Vercel**：
   - 代码修改后，重新部署
   - 确保环境变量 `VITE_API_TARGET` 未设置或设置为 `db`

2. **测试生产环境**：
   - 访问 Vercel 上线版本
   - 打开浏览器控制台
   - 应该看到：`[API] Target: db → https://ailanguagelearning.onrender.com`
   - 不应该看到：`[API] Target: mock`

3. **测试开发环境**：
   - 本地开发时，仍然可以通过 `?api=mock` 或 localStorage 切换模式
   - 这不会影响生产环境

## 注意事项

- **生产环境**：强制使用 `db` 模式，确保使用 `/api/v2/texts/{id}` API
- **开发环境**：保持灵活性，允许切换模式进行测试
- **环境变量**：Vercel 中不需要设置 `VITE_API_TARGET`（生产环境会强制使用 `db`）

## 相关文件

- `frontend/my-web-ui/src/services/api.js` - 已修改
