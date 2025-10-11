# Token Selection Session State Fix

## Problem Description

When a user selected a token and asked a question with a reference, the backend returned an error:

```
"No sentence context in session state. Please select a sentence first."
```

### Root Cause

The frontend was not sending the sentence context (sentence_id, text_id, sentence_body) and token information to the backend session state when a token was selected. This meant that:

1. When a user clicked on a token, the selection was only stored locally in the frontend
2. When the user sent a message, the backend had no knowledge of which sentence/token was selected
3. The backend's session state was empty, causing the error

## Solution

### 1. Enhanced `useTokenSelection` Hook

**File:** `frontend/my-web-ui/src/modules/article/hooks/useTokenSelection.js`

Added a new function `buildSelectionContext()` that extracts:
- Sentence information (text_id, sentence_id, sentence_body)
- Selected token details (token objects, token indices)
- Combined selected text

Modified `emitSelection()` to pass this context to the parent component via the `onTokenSelect` callback.

```javascript
const context = buildSelectionContext(activeSentenceRef.current, set)
onTokenSelect(lastTokenText, set, selectedTexts, context)
```

### 2. Updated `ArticleChatView` Component

**File:** `frontend/my-web-ui/src/modules/article/ArticleChatView.jsx`

Modified `handleTokenSelect` to:
- Receive the new `context` parameter from the hook
- Send sentence and token information to the backend via `apiService.session.updateContext()`
- Handle both single and multiple token selections

**Key Logic:**
```javascript
if (context && context.sentence && selectedTexts.length > 0) {
  const updatePayload = {
    sentence: context.sentence
  }
  
  // Handle multiple tokens
  if (context.tokens.length > 1) {
    updatePayload.token = {
      multiple_tokens: context.tokens,
      token_indices: context.tokenIndices,
      token_text: selectedTexts.join(' ')
    }
  } else if (context.tokens.length === 1) {
    // Single token selection
    const token = context.tokens[0]
    updatePayload.token = {
      token_body: token.token_body,
      sentence_token_id: token.sentence_token_id,
      global_token_id: token.global_token_id
    }
  }
  
  await apiService.session.updateContext(updatePayload)
}
```

### 3. Improved `ChatView` Component

**File:** `frontend/my-web-ui/src/modules/article/components/ChatView.jsx`

Modified `handleSendMessage` to preserve token selection when there's quoted text:
- If `quotedText` exists: Keep the current token selection (don't override it)
- If `quotedText` is empty: Clear the token selection (set `token: null`)

**Before:**
```javascript
if (!quotedText) {
  updatePayload.token = null  // Always cleared when no quote
}
```

**After:**
```javascript
if (!quotedText) {
  console.log('💬 [Frontend] 没有引用文本，清除旧 token 选择')
  updatePayload.token = null
} else {
  console.log('💬 [Frontend] 有引用文本，保持当前 token 选择不变')
  // Don't set token field, keep backend selection intact
}
```

## Data Flow

### New Token Selection Flow

1. **User clicks token** → `TokenSpan` component
2. **Selection hook updates** → `useTokenSelection.emitSelection()`
3. **Build context** → `buildSelectionContext()` extracts sentence + token data
4. **Notify parent** → `ArticleChatView.handleTokenSelect()` receives context
5. **Update backend** → `apiService.session.updateContext()` sends to `/api/session/update_context`
6. **Backend stores** → `session_state` now has sentence + token context

### Chat Message Flow

1. **User types question** → Input in `ChatView`
2. **User sends message** → `handleSendMessage()`
3. **Update input only** → `apiService.session.updateContext({ current_input: questionText })`
   - If `quotedText` exists: Keep existing token selection
   - If no `quotedText`: Clear token selection (`token: null`)
4. **Send chat** → `apiService.sendChat({ user_question: questionText })`
5. **Backend processes** → Uses stored session state (sentence + token)

## Backend API Endpoints

### `/api/session/update_context` (POST)

Accepts payload with:
```javascript
{
  sentence: {
    text_id: number,
    sentence_id: number,
    sentence_body: string
  },
  token: {
    token_body: string,
    sentence_token_id: number,
    global_token_id: number
  } | {
    multiple_tokens: Array<Token>,
    token_indices: Array<number>,
    token_text: string
  } | null,
  current_input: string  // Optional
}
```

## Testing

### To Verify the Fix:

1. **Start the backend server**
   ```bash
   cd frontend/my-web-ui/backend
   python server.py
   ```

2. **Start the frontend**
   ```bash
   cd frontend/my-web-ui
   npm run dev
   ```

3. **Test token selection with question:**
   - Open an article
   - Select a token (e.g., "aufkreuzen")
   - Ask a question (e.g., "这个词是什么意思")
   - Check browser console for logs:
     ```
     🎯 [ArticleChatView] Token selection changed:
     📤 [ArticleChatView] Sending selection context to backend...
     ✅ [ArticleChatView] Session context updated:
     ```
   - Backend should show:
     ```
     🔄 [SessionState] Updating session context (batch):
     ✓ sentence set: text_id=X, sentence_id=Y
     ✓ single token set: aufkreuzen
     ```

4. **Expected result:**
   - No error about "No sentence context"
   - AI responds with explanation about the selected token

## Benefits

1. **Proper Session State Management**: Backend always knows the context of user's question
2. **Support for Multiple Tokens**: Can handle both single and multiple token selections
3. **Better Debugging**: Comprehensive logging at each step
4. **Backward Compatible**: Still works with whole-sentence questions (no token selection)

## Files Changed

1. `frontend/my-web-ui/src/modules/article/hooks/useTokenSelection.js`
2. `frontend/my-web-ui/src/modules/article/ArticleChatView.jsx`
3. `frontend/my-web-ui/src/modules/article/components/ChatView.jsx`


