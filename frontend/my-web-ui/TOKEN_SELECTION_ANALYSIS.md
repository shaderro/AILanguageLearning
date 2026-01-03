# Token 选择模块逻辑分析与问题诊断

## 当前模块的主要逻辑

### 1. useTokenSelection.js - 选择状态管理

#### 核心数据结构
- `selectedTokenIdsRef` (useRef) - 存储选中的 token ID（Set），作为单一数据源
- `activeSentenceRef` (useRef) - 当前活跃的句子索引
- `selectedTokenIds` (useState) - 用于触发 UI 更新的 state
- `activeSentenceIndex` (useState) - 用于触发 UI 更新的 state

#### 核心函数流程

**`addSingle(sIdx, token)` - 添加/切换单个 token 的选择**
1. 获取 tokenId
2. 检查状态一致性（如果 activeSentenceRef 为 null 但 ref 中有选择，记录警告）
3. 判断是否切换句子：
   - 如果切换到新句子 → 清空之前的选择
   - 如果 activeSentenceRef 为 null → 设置为当前句子
4. **从 ref 实时读取当前选择状态**：`const currentSelection = new Set(selectedTokenIdsRef.current)`
5. 切换选择状态（添加或删除 tokenId）
6. 如果选择为空，清空 activeSentenceRef
7. 调用 `emitSelection(currentSelection, ...)`

**`emitSelection(newSelection, lastTokenText)` - 更新选择状态**
1. 记录更新前的状态（beforeUpdate）
2. **清空并更新 ref**：`selectedTokenIdsRef.current.clear()` → `selectionSet.forEach(id => selectedTokenIdsRef.current.add(id))`
3. 更新 state（触发 UI 更新）
4. 调用 `onTokenSelect` 回调
5. 调用 `selectTokensInContext`（如果存在）

**`clearSelection(options)` - 清空选择**
1. 记录清空前的状态
2. 清空 ref 和 state
3. 清空 activeSentenceRef

### 2. useTokenDrag.js - 拖拽选择管理

#### 核心函数流程

**`handleMouseDownToken` - 鼠标按下**
1. 保存拖拽起始信息（sentenceIdx, tokenIdx）
2. 设置 `isDraggingRef.current = false`

**`handleMouseMove` - 鼠标移动**
1. 检测是否应该开始拖拽（鼠标移动到不同 token）
2. 如果开始拖拽：
   - 设置 `isDraggingRef.current = true`
   - 从 ref 读取当前选择状态
   - 添加拖拽范围内的 token
   - 调用 `emitSelection`

**`handleMouseUp` - 鼠标松开**
1. 检查是否有拖拽操作
2. 如果发生拖拽：
   - 从 ref 读取当前选择状态
   - 添加拖拽范围内的 token
   - 调用 `emitSelection`
3. 如果没有拖拽（只是点击）：
   - **调用 `addSingle(sIdx, token)`**
4. 重置拖拽状态

## 问题分析

### 从日志发现的问题

#### 第一次点击 "Mr" (tokenIdx: 0)
```
🔍 [选择] addSingle 开始
  - activeSentence: 0  (注意：已经是 0，不是 null)
  - currentSelectionSize: 0  (ref 是空的)
🔧 [选择] 设置 activeSentence  (说明之前 activeSentenceRef.current 是 null)
➕ [选择] 添加选择
  - allSelectedTokens: ["0-0"]
📡 [选择] emitSelection 更新
  - beforeUpdate.refSize: 0  (在 emitSelection 被调用时，ref 还是空的！)
  - selectedIds: ["0-0"]
✅ [拖拽] mouseUp 完成
  - finalSelection: ["0-0"]  (正确)
```

#### 第二次点击 "Dursley" (tokenIdx: 3)
```
🔍 [选择] addSingle 开始
  - activeSentence: 0  (正确)
  - currentSelectionSize: 0  (ref 又是空的！应该包含 ["0-0"])
🔧 [选择] 设置 activeSentence  (说明之前 activeSentenceRef.current 又被设置为 null)
➕ [选择] 添加选择
  - allSelectedTokens: ["0-3"]  (只有当前这个，没有之前的 "0-0")
📡 [选择] emitSelection 更新
  - beforeUpdate.refSize: 0  (ref 还是空的)
  - selectedIds: ["0-3"]
✅ [拖拽] mouseUp 完成
  - finalSelection: ["0-3"]  (错误：应该包含 ["0-0", "0-3"])
```

### 根本原因

**问题 1：`emitSelection` 的 `beforeUpdate` 显示 ref 是空的**

这说明在 `addSingle` 调用 `emitSelection` 时，`selectedTokenIdsRef.current` 已经是空的了。

但是，`addSingle` 在调用 `emitSelection` 之前，已经从 ref 读取了选择状态（虽然也是空的），并添加了新的 token。

**问题 2：两次点击之间，ref 被清空了**

从日志看：
- 第一次点击后，`emitSelection` 更新了 ref，应该包含 `["0-0"]`
- 第二次点击时，ref 又是空的

**可能的原因：**

1. **`selectTokensInContext` 或其他回调函数清空了选择**
   - 需要检查是否有代码在 `onTokenSelect` 或 `selectTokensInContext` 中调用了 `clearSelection`

2. **React 重新渲染导致 ref 被重置**
   - 如果 `useTokenSelection` hook 被重新创建，ref 会被重置
   - 需要检查 hook 的依赖项是否稳定

3. **`activeSentenceRef.current` 在两次点击之间被清空**
   - 从日志看，第二次点击时又显示了 `🔧 [选择] 设置 activeSentence`
   - 说明 `activeSentenceRef.current` 在第一次点击后又被设置为 null
   - 可能是在 `addSingle` 中，如果选择为空时清空了 `activeSentenceRef`，但这里选择不为空

4. **时序问题：`emitSelection` 是异步的**
   - `emitSelection` 更新 ref 后，可能还没有完成，就被其他代码清空了
   - 或者 `onTokenSelect` 回调中有异步操作，导致状态被清空

### 最可能的原因

从日志看，`emitSelection` 的 `beforeUpdate` 显示 ref 是空的，这说明在 `addSingle` 调用 `emitSelection` 时，ref 已经被清空了。

但是，`addSingle` 在开始时从 ref 读取时，ref 也是空的。这说明在 `addSingle` 被调用之前，ref 就已经被清空了。

**最可能的原因：在两次点击之间，有代码清空了选择。**

需要检查：
1. `clearSelection` 是否被调用（应该会有日志 `🧹 [选择] clearSelection 被调用`）
2. `selectTokensInContext` 是否清空了选择
3. `onTokenSelect` 回调中是否有清空选择的逻辑

## 解决方案

### 方案 1：确保 ref 在两次点击之间不被清空

1. 检查所有调用 `clearSelection` 的地方
2. 确保 `selectTokensInContext` 不会清空选择
3. 确保 `onTokenSelect` 回调不会清空选择

### 方案 2：修复 `addSingle` 的逻辑

如果 ref 在两次点击之间被清空是不可避免的，需要修复 `addSingle` 的逻辑：

1. 在 `addSingle` 开始时，如果 `activeSentenceRef.current === sIdx` 但 ref 是空的，说明状态不一致，需要从 state 恢复
2. 或者，在 `emitSelection` 后，确保 ref 不会被清空

### 方案 3：使用 state 作为备份

如果 ref 可能被清空，可以使用 state 作为备份：
- 在 `addSingle` 开始时，如果 ref 是空的，尝试从 state 恢复
- 或者，在 `emitSelection` 后，将 state 同步到 ref

## 建议的修复

最直接的修复是：在 `addSingle` 开始时，如果 ref 是空的但 `activeSentenceRef.current === sIdx`，说明状态不一致，需要从 state 恢复 ref。

但是，从日志看，`activeSentenceRef.current` 在第二次点击时也是 null（因为显示了 `🔧 [选择] 设置 activeSentence`），这说明 `activeSentenceRef` 也被清空了。

**最可能的原因：在 `mouseUp` 完成后，有代码清空了选择。**

需要检查 `handleMouseUp` 完成后，是否有其他代码清空了选择。

