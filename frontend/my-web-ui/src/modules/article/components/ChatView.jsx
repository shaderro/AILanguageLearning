import { useState, useRef, useEffect } from 'react'
import ToastNotice from './ToastNotice'
import SuggestedQuestions from './SuggestedQuestions'
import { useChatEvent } from '../contexts/ChatEventContext'

export default function ChatView({ quotedText, onClearQuote, disabled = false, hasSelectedToken = false, selectedTokenCount = 1, selectionContext = null, markAsAsked = null, articleId = null }) {
  const { pendingMessage, clearPendingMessage, pendingToast, clearPendingToast } = useChatEvent()
  const [messages, setMessages] = useState([
    { id: 1, text: "你好！我是聊天助手，有什么可以帮助你的吗？", isUser: false, timestamp: new Date() }
  ])
  const [inputText, setInputText] = useState('')
  const [showToast, setShowToast] = useState(false)
  const [toastMessage, setToastMessage] = useState('')
  // 新增：多实例 toast 栈
  const [toasts, setToasts] = useState([]) // {id, message, slot}
  const messagesEndRef = useRef(null)
  const [shouldAutoScroll, setShouldAutoScroll] = useState(false)

  // 新增：自动滚动到底部的函数
  const scrollToBottom = () => {
    if (shouldAutoScroll) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }

  // 抽取：显示“知识点已加入”提示卡片
  const showKnowledgeToast = (currentKnowledge) => {
    const text = String(currentKnowledge ?? '').trim()
    const msg = `${text} 知识点已总结并加入列表`
    // 兼容旧的单实例
    setToastMessage(msg)
    setShowToast(true)
    // 新：推入多实例栈
    const id = Date.now() + Math.random()
    // 为每个 toast 设置独立的显示时间，避免同一批次由父层重渲染触发同一时刻开始计时
    setTimeout(() => {
      setToasts(prev => {
        const slot = prev.length // 固定槽位：加入时的序号
        return [...prev, { id, message: msg, slot }]
      })
    }, 0)
  }

  // 新增：监听messages变化，自动滚动到底部（只在有新消息时）
  useEffect(() => {
    // 只有在消息数量大于1时才自动滚动（避免初始化时滚动）
    if (messages.length > 1) {
      setShouldAutoScroll(true)
      scrollToBottom()
    }
  }, [messages])

  // 新增：监听待发送消息
  useEffect(() => {
    if (pendingMessage) {
      // 判断消息类型：如果没有 quotedText，说明是 AI 直接响应
      if (!pendingMessage.quotedText) {
        // AI 响应消息
        const aiMessage = {
          id: Date.now(),
          text: pendingMessage.text,
          isUser: false,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, aiMessage])
      } else {
        // 用户提问消息
        const userMessage = {
          id: Date.now(),
          text: pendingMessage.text,
          isUser: true,
          timestamp: pendingMessage.timestamp,
          quote: pendingMessage.quotedText
        }
        setMessages(prev => [...prev, userMessage])
        
        // 清空当前引用（如果有的话）
        if (onClearQuote) {
          onClearQuote()
        }
      }
      
      // 清除待发送消息
      clearPendingMessage()
    }
  }, [pendingMessage, clearPendingMessage, onClearQuote])

  // 新增：监听跨组件触发的 toast
  useEffect(() => {
    if (pendingToast) {
      showKnowledgeToast(pendingToast)
      clearPendingToast()
    }
  }, [pendingToast, clearPendingToast])

  // 新增：测试连续 Toast 的方法（按下 S 键触发，每 0.5s 一次，共 3 次）
  const triggerSequentialToasts = () => {
    const items = ['测试Toast 1', '测试Toast 2', '测试Toast 3']
    items.forEach((msg, idx) => {
      setTimeout(() => {
        showKnowledgeToast(msg)
      }, idx * 500)
    })
  }

  // 注释掉按s键触发Toast的测试功能（保留代码以备将来使用）
  // useEffect(() => {
  //   const onKeyDown = (e) => {
  //     if ((e.key || '').toLowerCase() === 's') {
  //       triggerSequentialToasts()
  //     }
  //   }
  //   window.addEventListener('keydown', onKeyDown)
  //   return () => window.removeEventListener('keydown', onKeyDown)
  // }, [])

  const handleSendMessage = async () => {
    if (inputText.trim() === '') return

    const questionText = inputText
    // 保存当前的引用文本和上下文，因为后面会清空
    const currentQuotedText = quotedText
    const currentSelectionContext = selectionContext
    
    // Add user message with quote if exists
    const userMessage = {
      id: Date.now(),
      text: questionText,
      isUser: true,
      timestamp: new Date(),
      quote: currentQuotedText || null
    }
    
    setMessages(prev => [...prev, userMessage])
    setInputText('')

    // 调用后端 chat API
    try {
      console.log('\n' + '='.repeat(80))
      console.log('💬 [ChatView] ========== 发送消息 ==========')
      console.log('📝 [ChatView] 问题文本:', questionText)
      console.log('📌 [ChatView] 引用文本 (quotedText):', currentQuotedText || '无')
      console.log('📋 [ChatView] 选择上下文 (selectionContext):')
      if (currentSelectionContext) {
        console.log('  - 句子 ID:', currentSelectionContext.sentence?.sentence_id)
        console.log('  - 文章 ID:', currentSelectionContext.sentence?.text_id)
        console.log('  - 句子原文:', currentSelectionContext.sentence?.sentence_body)
        console.log('  - 选中的 tokens:', currentSelectionContext.selectedTexts)
        console.log('  - Token 数量:', currentSelectionContext.tokens?.length)
      } else {
        console.log('  - 无上下文（未选择任何token）')
      }
      console.log('='.repeat(80) + '\n')
      
      const { apiService } = await import('../../../services/api')
      
      // 构建更新payload
      const updatePayload = {
        current_input: questionText
      }
      
      // 如果有选择上下文，重新发送句子和token信息以确保后端有完整上下文
      if (currentSelectionContext && currentSelectionContext.sentence) {
        console.log('💬 [ChatView] 重新发送完整的句子和token上下文到后端...')
        
        // 添加句子信息
        updatePayload.sentence = currentSelectionContext.sentence
        
        // 添加token信息
        if (currentSelectionContext.tokens && currentSelectionContext.tokens.length > 0) {
          if (currentSelectionContext.tokens.length > 1) {
            // 多个token
            updatePayload.token = {
              multiple_tokens: currentSelectionContext.tokens,
              token_indices: currentSelectionContext.tokenIndices,
              token_text: currentSelectionContext.selectedTexts.join(' ')
            }
          } else {
            // 单个token
            const token = currentSelectionContext.tokens[0]
            updatePayload.token = {
              token_body: token.token_body,
              sentence_token_id: token.sentence_token_id,
              global_token_id: token.global_token_id
            }
          }
        }
        
        console.log('📤 [ChatView] 发送的完整payload:', JSON.stringify(updatePayload, null, 2))
      } else if (!currentQuotedText) {
        // 如果没有引用文本，清除旧的token选择
        console.log('💬 [ChatView] 没有引用文本，清除旧 token 选择')
        updatePayload.token = null
      }
      
      const updateResponse = await apiService.session.updateContext(updatePayload)
      console.log('✅ [ChatView] Session context 更新完成:', updateResponse)
      
      // 调用 chat 接口
      console.log('💬 [Frontend] 步骤4: 调用 /api/chat 接口...')
      const response = await apiService.sendChat({
        user_question: questionText
      })
      
      console.log('✅ [Frontend] 步骤5: 收到响应')
      console.log('✅ [Frontend] 响应完整数据:', JSON.stringify(response, null, 2))
      
      // 标记选中的tokens为已提问
      console.log('🔍 [DEBUG] 检查标记条件:', {
        hasMarkAsAsked: !!markAsAsked,
        hasContext: !!currentSelectionContext,
        hasTokens: !!(currentSelectionContext?.tokens),
        tokenCount: currentSelectionContext?.tokens?.length,
        articleId: articleId
      })
      
      if (markAsAsked && currentSelectionContext && currentSelectionContext.tokens && currentSelectionContext.tokens.length > 0) {
        console.log('✅ [ChatView] 进入标记逻辑')
        console.log('🏷️ [ChatView] Marking selected tokens as asked...')
        
        // 标记所有选中的tokens为已提问
        const markPromises = currentSelectionContext.tokens.map((token, tokenIdx) => {
          // 使用fallback确保字段存在
          const sentenceTokenId = token.sentence_token_id ?? (tokenIdx + 1)
          const sentenceId = currentSelectionContext.sentence?.sentence_id
          const textId = currentSelectionContext.sentence?.text_id ?? articleId  // ← 使用articleId作为fallback
          
          console.log(`🔍 [DEBUG] Token ${tokenIdx}:`, {
            token_body: token.token_body,
            textId,
            sentenceId,
            sentenceTokenId
          })
          
          if (sentenceId && textId && sentenceTokenId != null) {
            console.log(`🏷️ [ChatView] Marking token: "${token.token_body}" (${textId}:${sentenceId}:${sentenceTokenId})`)
            return markAsAsked(textId, sentenceId, sentenceTokenId)
          } else {
            console.error(`❌ [ChatView] 缺少必需字段:`, { sentenceId, textId, sentenceTokenId })
            return Promise.resolve(false)
          }
        })
        
        try {
          const results = await Promise.all(markPromises)
          const successCount = results.filter(r => r).length
          console.log(`✅ [ChatView] Successfully marked ${successCount}/${markPromises.length} tokens as asked`)
          
          // 如果标记成功，等待一小段时间让状态更新
          if (successCount > 0) {
            setTimeout(() => {
              console.log('🔄 [ChatView] Token states should be updated now')
            }, 100)
          } else {
            console.warn('⚠️ [ChatView] 没有token被成功标记')
          }
        } catch (error) {
          console.error('❌ [ChatView] Error marking tokens as asked:', error)
        }
      } else {
        console.warn('⚠️ [ChatView] 标记条件不满足（未进入标记逻辑）')
      }
      
      // 添加session state调试信息
      console.log('🔍 [SESSION STATE DEBUG] After sending message:')
      console.log('  - Question text:', questionText)
      console.log('  - Quoted text:', quotedText || 'None')
      console.log('  - Update payload:', updatePayload)
      console.log('  - Update response:', updateResponse)
      
      if (response.success && response.data) {
        const { ai_response, grammar_summaries, vocab_summaries, grammar_to_add, vocab_to_add, examples } = response.data
        
        // 详细打印session state中的vocab/grammar/example状态
        console.log('\n' + '='.repeat(80))
        console.log('📊 [SESSION STATE] 本轮对话生成的知识点状态：')
        console.log('='.repeat(80))
        
        // 新增语法
        if (grammar_to_add && grammar_to_add.length > 0) {
          console.log('🆕 新增语法 (grammar_to_add):', grammar_to_add.length, '个')
          grammar_to_add.forEach((g, idx) => {
            console.log(`  ${idx + 1}. ${g.name}`)
            console.log(`     - 总结: ${g.summary || '无'}`)
            console.log(`     - 详情: ${g.explanation || '无'}`)
          })
        } else {
          console.log('🆕 新增语法 (grammar_to_add): 无')
        }
        
        // 新增词汇
        if (vocab_to_add && vocab_to_add.length > 0) {
          console.log('🆕 新增词汇 (vocab_to_add):', vocab_to_add.length, '个')
          vocab_to_add.forEach((v, idx) => {
            console.log(`  ${idx + 1}. ${v.vocab}`)
            console.log(`     - 翻译: ${v.translation || '无'}`)
            console.log(`     - 用法: ${v.usage || '无'}`)
          })
        } else {
          console.log('🆕 新增词汇 (vocab_to_add): 无')
        }
        
        // 相关语法总结
        if (grammar_summaries && grammar_summaries.length > 0) {
          console.log('📚 相关语法总结 (grammar_summaries):', grammar_summaries.length, '个')
          grammar_summaries.forEach((g, idx) => {
            console.log(`  ${idx + 1}. ${g.name}`)
            console.log(`     - 总结: ${g.summary || '无'}`)
          })
        } else {
          console.log('📚 相关语法总结 (grammar_summaries): 无')
        }
        
        // 相关词汇总结
        if (vocab_summaries && vocab_summaries.length > 0) {
          console.log('📖 相关词汇总结 (vocab_summaries):', vocab_summaries.length, '个')
          vocab_summaries.forEach((v, idx) => {
            console.log(`  ${idx + 1}. ${v.vocab}`)
            console.log(`     - 翻译: ${v.translation || '无'}`)
          })
        } else {
          console.log('📖 相关词汇总结 (vocab_summaries): 无')
        }
        
        // 例句
        if (examples && examples.length > 0) {
          console.log('📝 例句 (examples):', examples.length, '个')
          examples.forEach((ex, idx) => {
            console.log(`  ${idx + 1}. ${ex.example || ex.sentence || ex}`)
            if (ex.translation) {
              console.log(`     译文: ${ex.translation}`)
            }
          })
        } else {
          console.log('📝 例句 (examples): 无')
        }
        
        console.log('='.repeat(80) + '\n')
        
        // 显示 AI 响应
        if (ai_response) {
          const aiMessage = {
            id: Date.now() + 1,
            text: ai_response,
            isUser: false,
            timestamp: new Date()
          }
          setMessages(prev => [...prev, aiMessage])
        }
        
        // 显示总结的语法和词汇（通过 Toast）
        const summaryItems = []
        
        if (grammar_to_add && grammar_to_add.length > 0) {
          grammar_to_add.forEach(g => {
            summaryItems.push(`🆕 语法: ${g.name}`)
          })
        }
        
        if (vocab_to_add && vocab_to_add.length > 0) {
          vocab_to_add.forEach(v => {
            summaryItems.push(`🆕 词汇: ${v.vocab}`)
          })
        }
        
        if (grammar_summaries && grammar_summaries.length > 0) {
          grammar_summaries.forEach(g => {
            summaryItems.push(`📚 语法: ${g.name}`)
          })
        }
        
        if (vocab_summaries && vocab_summaries.length > 0) {
          vocab_summaries.forEach(v => {
            summaryItems.push(`📖 词汇: ${v.vocab}`)
          })
        }
        
        // 逐个显示 Toast
        summaryItems.forEach((item, idx) => {
          setTimeout(() => {
            showKnowledgeToast(item)
          }, idx * 600)
        })
      } else {
        console.error('❌ [Frontend] Chat request failed:', response.error)
        // 显示错误消息
        const errorMessage = {
          id: Date.now() + 1,
          text: `抱歉，处理您的问题时出现错误: ${response.error}`,
          isUser: false,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, errorMessage])
      }
      
      // ✅ 不再自动清空引用 - 保持引用以便用户继续追问
      // 引用会在用户选择新的 token 或点击文章空白处时自动更新/清空
      console.log('✅ [ChatView] 消息发送完成，保持引用以便继续追问')
    } catch (error) {
      console.error('💥 [Frontend] ❌❌❌ Chat request 发生错误 (handleSendMessage) ❌❌❌')
      console.error('💥 [Frontend] 错误对象:', error)
      console.error('💥 [Frontend] 错误消息:', error.message)
      console.error('💥 [Frontend] 错误堆栈:', error.stack)
      if (error.response) {
        console.error('💥 [Frontend] 响应状态:', error.response.status)
        console.error('💥 [Frontend] 响应数据:', error.response.data)
      }
      
      // 显示错误消息
      const errorMessage = {
        id: Date.now() + 1,
        text: `抱歉，处理您的问题时出现错误: ${error.message || '未知错误'}`,
        isUser: false,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
      
      // ✅ 即使出错也不清空引用，保持引用以便用户重试
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleToastClose = () => {
    setShowToast(false)
    setToastMessage('')
  }

  const handleSuggestedQuestionSelect = async (question) => {
    // 保存当前的引用文本和上下文，因为后面会清空
    const currentQuotedText = quotedText
    const currentSelectionContext = selectionContext
    
    // 自动发送已选择的问题
    const userMessage = {
      id: Date.now(),
      text: question,
      isUser: true,
      timestamp: new Date(),
      quote: currentQuotedText || null
    }
    
    setMessages(prev => [...prev, userMessage])

    // 调用后端 chat API（与 handleSendMessage 相同的逻辑）
    try {
      console.log('\n' + '='.repeat(80))
      console.log('💬 [ChatView] ========== 发送建议问题 ==========')
      console.log('📝 [ChatView] 问题文本:', question)
      console.log('📌 [ChatView] 引用文本 (quotedText):', currentQuotedText || '无')
      console.log('📋 [ChatView] 选择上下文 (selectionContext):')
      if (currentSelectionContext) {
        console.log('  - 句子 ID:', currentSelectionContext.sentence?.sentence_id)
        console.log('  - 文章 ID:', currentSelectionContext.sentence?.text_id)
        console.log('  - 句子原文:', currentSelectionContext.sentence?.sentence_body)
        console.log('  - 选中的 tokens:', currentSelectionContext.selectedTexts)
        console.log('  - Token 数量:', currentSelectionContext.tokens?.length)
      } else {
        console.log('  - 无上下文（未选择任何token）')
      }
      console.log('='.repeat(80) + '\n')
      
      const { apiService } = await import('../../../services/api')
      
      // 构建更新payload
      const updatePayload = {
        current_input: question
      }
      
      // 如果有选择上下文，重新发送句子和token信息以确保后端有完整上下文
      if (currentSelectionContext && currentSelectionContext.sentence) {
        console.log('💬 [ChatView] 重新发送完整的句子和token上下文到后端...')
        
        // 添加句子信息
        updatePayload.sentence = currentSelectionContext.sentence
        
        // 添加token信息
        if (currentSelectionContext.tokens && currentSelectionContext.tokens.length > 0) {
          if (currentSelectionContext.tokens.length > 1) {
            // 多个token
            updatePayload.token = {
              multiple_tokens: currentSelectionContext.tokens,
              token_indices: currentSelectionContext.tokenIndices,
              token_text: currentSelectionContext.selectedTexts.join(' ')
            }
          } else {
            // 单个token
            const token = currentSelectionContext.tokens[0]
            updatePayload.token = {
              token_body: token.token_body,
              sentence_token_id: token.sentence_token_id,
              global_token_id: token.global_token_id
            }
          }
        }
        
        console.log('📤 [ChatView] 发送的完整payload:', JSON.stringify(updatePayload, null, 2))
      } else if (!currentQuotedText) {
        // 如果没有引用文本，清除旧的token选择
        console.log('💬 [ChatView] 没有引用文本，清除旧 token 选择')
        updatePayload.token = null
      }
      
      const updateResponse = await apiService.session.updateContext(updatePayload)
      console.log('✅ [ChatView] Session context 更新完成:', updateResponse)
      
      // 调用 chat 接口
      const response = await apiService.sendChat({
        user_question: question
      })
      
      console.log('✅ [Frontend] Chat response received:', response)
      
      // 标记选中的tokens为已提问
      console.log('🔍 [DEBUG] 检查标记条件（建议问题）:', {
        hasMarkAsAsked: !!markAsAsked,
        hasContext: !!currentSelectionContext,
        hasTokens: !!(currentSelectionContext?.tokens),
        tokenCount: currentSelectionContext?.tokens?.length,
        articleId: articleId
      })
      
      if (markAsAsked && currentSelectionContext && currentSelectionContext.tokens && currentSelectionContext.tokens.length > 0) {
        console.log('✅ [ChatView] 进入标记逻辑（建议问题）')
        console.log('🏷️ [ChatView] Marking selected tokens as asked (suggested question)...')
        
        // 标记所有选中的tokens为已提问
        const markPromises = currentSelectionContext.tokens.map((token, tokenIdx) => {
          // 使用fallback确保字段存在
          const sentenceTokenId = token.sentence_token_id ?? (tokenIdx + 1)
          const sentenceId = currentSelectionContext.sentence?.sentence_id
          const textId = currentSelectionContext.sentence?.text_id ?? articleId  // ← 使用articleId作为fallback
          
          console.log(`🔍 [DEBUG] Token ${tokenIdx} (建议问题):`, {
            token_body: token.token_body,
            textId,
            sentenceId,
            sentenceTokenId
          })
          
          if (sentenceId && textId && sentenceTokenId != null) {
            console.log(`🏷️ [ChatView] Marking token: "${token.token_body}" (${textId}:${sentenceId}:${sentenceTokenId})`)
            return markAsAsked(textId, sentenceId, sentenceTokenId)
          } else {
            console.error(`❌ [ChatView] 缺少必需字段（建议问题）:`, { sentenceId, textId, sentenceTokenId })
            return Promise.resolve(false)
          }
        })
        
        try {
          const results = await Promise.all(markPromises)
          const successCount = results.filter(r => r).length
          console.log(`✅ [ChatView] Successfully marked ${successCount}/${markPromises.length} tokens as asked (suggested question)`)
          
          // 如果标记成功，等待一小段时间让状态更新
          if (successCount > 0) {
            setTimeout(() => {
              console.log('🔄 [ChatView] Token states should be updated now (suggested question)')
            }, 100)
          } else {
            console.warn('⚠️ [ChatView] 没有token被成功标记（建议问题）')
          }
        } catch (error) {
          console.error('❌ [ChatView] Error marking tokens as asked (suggested question):', error)
        }
      } else {
        console.warn('⚠️ [ChatView] 标记条件不满足（建议问题，未进入标记逻辑）')
      }
      
      // 添加session state调试信息
      console.log('🔍 [SESSION STATE DEBUG] After suggested question selection:')
      console.log('  - Question text:', question)
      console.log('  - Quoted text:', currentQuotedText || 'None')
      console.log('  - Update payload:', updatePayload)
      
      if (response.success && response.data) {
        const { ai_response, grammar_summaries, vocab_summaries, grammar_to_add, vocab_to_add, examples } = response.data
        
        // 详细打印session state中的vocab/grammar/example状态
        console.log('\n' + '='.repeat(80))
        console.log('📊 [SESSION STATE] 本轮对话生成的知识点状态（建议问题）：')
        console.log('='.repeat(80))
        
        // 新增语法
        if (grammar_to_add && grammar_to_add.length > 0) {
          console.log('🆕 新增语法 (grammar_to_add):', grammar_to_add.length, '个')
          grammar_to_add.forEach((g, idx) => {
            console.log(`  ${idx + 1}. ${g.name}`)
            console.log(`     - 总结: ${g.summary || '无'}`)
            console.log(`     - 详情: ${g.explanation || '无'}`)
          })
        } else {
          console.log('🆕 新增语法 (grammar_to_add): 无')
        }
        
        // 新增词汇
        if (vocab_to_add && vocab_to_add.length > 0) {
          console.log('🆕 新增词汇 (vocab_to_add):', vocab_to_add.length, '个')
          vocab_to_add.forEach((v, idx) => {
            console.log(`  ${idx + 1}. ${v.vocab}`)
            console.log(`     - 翻译: ${v.translation || '无'}`)
            console.log(`     - 用法: ${v.usage || '无'}`)
          })
        } else {
          console.log('🆕 新增词汇 (vocab_to_add): 无')
        }
        
        // 相关语法总结
        if (grammar_summaries && grammar_summaries.length > 0) {
          console.log('📚 相关语法总结 (grammar_summaries):', grammar_summaries.length, '个')
          grammar_summaries.forEach((g, idx) => {
            console.log(`  ${idx + 1}. ${g.name}`)
            console.log(`     - 总结: ${g.summary || '无'}`)
          })
        } else {
          console.log('📚 相关语法总结 (grammar_summaries): 无')
        }
        
        // 相关词汇总结
        if (vocab_summaries && vocab_summaries.length > 0) {
          console.log('📖 相关词汇总结 (vocab_summaries):', vocab_summaries.length, '个')
          vocab_summaries.forEach((v, idx) => {
            console.log(`  ${idx + 1}. ${v.vocab}`)
            console.log(`     - 翻译: ${v.translation || '无'}`)
          })
        } else {
          console.log('📖 相关词汇总结 (vocab_summaries): 无')
        }
        
        // 例句
        if (examples && examples.length > 0) {
          console.log('📝 例句 (examples):', examples.length, '个')
          examples.forEach((ex, idx) => {
            console.log(`  ${idx + 1}. ${ex.example || ex.sentence || ex}`)
            if (ex.translation) {
              console.log(`     译文: ${ex.translation}`)
            }
          })
        } else {
          console.log('📝 例句 (examples): 无')
        }
        
        console.log('='.repeat(80) + '\n')
        
        // 显示 AI 响应
        if (ai_response) {
          const aiMessage = {
            id: Date.now() + 1,
            text: ai_response,
            isUser: false,
            timestamp: new Date()
          }
          setMessages(prev => [...prev, aiMessage])
        }
        
        // 显示总结的语法和词汇（通过 Toast）
        const summaryItems = []
        
        if (grammar_to_add && grammar_to_add.length > 0) {
          grammar_to_add.forEach(g => {
            summaryItems.push(`🆕 语法: ${g.name}`)
          })
        }
        
        if (vocab_to_add && vocab_to_add.length > 0) {
          vocab_to_add.forEach(v => {
            summaryItems.push(`🆕 词汇: ${v.vocab}`)
          })
        }
        
        if (grammar_summaries && grammar_summaries.length > 0) {
          grammar_summaries.forEach(g => {
            summaryItems.push(`📚 语法: ${g.name}`)
          })
        }
        
        if (vocab_summaries && vocab_summaries.length > 0) {
          vocab_summaries.forEach(v => {
            summaryItems.push(`📖 词汇: ${v.vocab}`)
          })
        }
        
        // 逐个显示 Toast
        summaryItems.forEach((item, idx) => {
          setTimeout(() => {
            showKnowledgeToast(item)
          }, idx * 600)
        })
      } else {
        console.error('❌ [Frontend] Chat request failed:', response.error)
        // 显示错误消息
        const errorMessage = {
          id: Date.now() + 1,
          text: `抱歉，处理您的问题时出现错误: ${response.error}`,
          isUser: false,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, errorMessage])
      }
      
      // ✅ 不再自动清空引用 - 保持引用以便用户继续追问
      console.log('✅ [ChatView] 建议问题发送完成，保持引用以便继续追问')
    } catch (error) {
      console.error('💥 [Frontend] ❌❌❌ Chat request 发生错误 (handleSuggestedQuestionSelect) ❌❌❌')
      console.error('💥 [Frontend] 错误对象:', error)
      console.error('💥 [Frontend] 错误消息:', error.message)
      console.error('💥 [Frontend] 错误堆栈:', error.stack)
      if (error.response) {
        console.error('💥 [Frontend] 响应状态:', error.response.status)
        console.error('💥 [Frontend] 响应数据:', error.response.data)
      }
      
      // 显示错误消息
      const errorMessage = {
        id: Date.now() + 1,
        text: `抱歉，处理您的问题时出现错误: ${error.message || '未知错误'}`,
        isUser: false,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
      
      // ✅ 即使出错也不清空引用，保持引用以便用户重试
    }
  }

  const handleQuestionClick = (question) => {
    // 当问题被点击时，可以在这里添加额外的逻辑
    console.log('Question clicked:', question)
  }

  const handleChatContainerClick = (e) => {
    // 如果点击的是聊天容器而不是输入框或建议问题，可以在这里添加逻辑
    // 目前这个功能由SuggestedQuestions组件内部处理
  }

  const formatTime = (date) => {
    return date.toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  }

  return (
    <div className={`w-80 flex flex-col bg-white rounded-lg shadow-md h-full relative ${disabled ? 'opacity-50' : ''}`}>
      {/* Chat Header */}
      <div className="p-4 border-b border-gray-200 bg-gray-50 rounded-t-lg">
        <h2 className="text-lg font-semibold text-gray-800">
          {disabled ? '聊天助手 (暂时不可用)' : '聊天助手'}
        </h2>
        <p className="text-sm text-gray-600">
          {disabled ? '请先上传文章内容' : '随时为您提供帮助'}
        </p>
      </div>

      {/* Messages Area */}
      <div className="flex-1 min-h-0 overflow-y-auto p-4 space-y-3 max-h-[calc(100vh-200px)]">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs px-3 py-2 rounded-lg ${
                message.isUser
                  ? 'bg-blue-500 text-white rounded-br-none'
                  : 'bg-gray-100 text-gray-800 rounded-bl-none'
              }`}
            >
              {/* Quote display */}
              {message.quote && (
                <div className={`mb-2 p-2 rounded text-xs ${
                  message.isUser 
                    ? 'bg-blue-400 text-blue-50' 
                    : 'bg-gray-200 text-gray-600'
                }`}>
                  <div className="font-medium mb-1">引用</div>
                  <div className="italic">"{message.quote}"</div>
                </div>
              )}
              
              <p className="text-sm">{message.text}</p>
              <p className={`text-xs mt-1 ${
                message.isUser ? 'text-blue-100' : 'text-gray-500'
              }`}>
                {formatTime(message.timestamp)}
              </p>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Quote Display */}
      {quotedText && (
        <div className="px-4 py-2 bg-blue-50 border-t border-blue-200">
          <div className="flex items-center gap-2">
            <div className="flex-1">
              <div className="text-xs text-blue-600 font-medium mb-1">引用（继续提问将保持此引用）</div>
              <div className="text-sm text-blue-800 italic">"{quotedText}"</div>
            </div>
            <button
              onClick={onClearQuote}
              className="flex-shrink-0 p-1.5 hover:bg-blue-100 rounded-lg transition-colors"
              title="清空引用"
            >
              <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* Suggested Questions */}
      <SuggestedQuestions
        quotedText={quotedText}
        onQuestionSelect={handleSuggestedQuestionSelect}
        isVisible={!!quotedText}
        inputValue={inputText}
        onQuestionClick={handleQuestionClick}
        tokenCount={selectedTokenCount}
      />

      {/* Input Area */}
      <div className="p-4 border-t border-gray-200 bg-gray-50 rounded-b-lg">
        <div className="flex space-x-2">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={
              disabled ? "聊天暂时不可用" : 
              !hasSelectedToken ? "请先选择文章中的词汇或句子" :
              (quotedText ? `回复引用："${quotedText}"` : "输入消息...")
            }
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={disabled || !hasSelectedToken}
          />
          <button
            onClick={handleSendMessage}
            disabled={inputText.trim() === '' || disabled || !hasSelectedToken}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title={!hasSelectedToken ? "请先选择文章中的词汇" : "发送消息"}
          >
            发送
          </button>
        </div>
      </div>

      {/* Toast Stack - 底部居中，固定槽位，避免上移 */}
      <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50 pointer-events-none" style={{ position: 'fixed' }}>
        {toasts.map(t => (
          <div
            key={t.id}
            className="pointer-events-auto"
            style={{
              position: 'absolute',
              bottom: `${t.slot * 64}px`, // 每个槽位 64px 间距
              left: '50%',
              transform: 'translateX(-50%)',
            }}
          >
            <ToastNotice
              message={t.message}
              isVisible={true}
              duration={20000}
              onClose={() => setToasts(prev => prev.filter(x => x.id !== t.id))}
            />
          </div>
        ))}
      </div>
    </div>
  )
}



