import { useState, useRef, useEffect, useCallback } from 'react'
import { createPortal } from 'react-dom'
import { apiService } from '../../../services/api'
import { useUser } from '../../../contexts/UserContext'
import { useLanguage } from '../../../contexts/LanguageContext'
import guestDataManager from '../../../utils/guestDataManager'
import { useUIText } from '../../../i18n/useUIText'
import { BackButton } from '../../../components/base'

// 文章长度限制（字符数）
const MAX_ARTICLE_LENGTH = 12000

const UploadInterface = ({ onUploadStart, onLengthExceeded, onUploadComplete, onBack }) => {
  const { userId, isGuest } = useUser()
  const { selectedLanguage } = useLanguage()
  const [dragActive, setDragActive] = useState(false)
  const [uploadMethod, setUploadMethod] = useState(null) // 'url', 'file', 'drop', 'text'
  const [showProgress, setShowProgress] = useState(false)
  const [textContent, setTextContent] = useState('')
  const [textTitle, setTextTitle] = useState('')
  const [customTitle, setCustomTitle] = useState('') // 自定义文章名（用于URL和文件上传）
  const MAX_TITLE_LENGTH = 80 // 文章标题最大长度（前端限制）
  const [selectedFile, setSelectedFile] = useState(null) // 选中的文件（来自选择或拖拽）
  const [selectedFileSource, setSelectedFileSource] = useState(null) // 'file' | 'drop'
  const fileInputRef = useRef(null)
  
  // 长度超限对话框状态
  const [showLengthDialog, setShowLengthDialog] = useState(false)
  const [pendingContent, setPendingContent] = useState(null) // { type: 'file'|'text'|'drop', file: File, content: string, title: string }
  
  // 使用 ref 保存待处理的内容，避免组件重新挂载时丢失
  const pendingContentRef = useRef(null)
  const t = useUIText()
  const language = selectedLanguage || '德文' // 上传文章语言：默认使用当前正在学习的语言
  
  // 调试：监听对话框状态变化
  useEffect(() => {
    console.log('🔍 [Frontend] 状态变化 - showLengthDialog:', showLengthDialog, 'pendingContent:', !!pendingContent, 'showProgress:', showProgress)
    if (showLengthDialog && pendingContent) {
      console.log('✅ [Frontend] 对话框应该显示！')
    }
    // 如果状态丢失但 ref 中有数据，恢复状态
    if (!showLengthDialog && pendingContentRef.current) {
      console.log('🔄 [Frontend] 检测到状态丢失，从 ref 恢复')
      setPendingContent(pendingContentRef.current)
      setShowLengthDialog(true)
    }
  }, [showLengthDialog, pendingContent, showProgress])

  // 处理上传成功后的响应（包括游客模式保存到 localStorage）
  const handleUploadSuccess = (responseData) => {
    console.log('📄 [Upload] 文章已创建，完整响应:', responseData)
    
    // 🔧 后端返回格式：{status: 'success', data: {article_id: ..., title: ..., ...}, message: ...}
    // 或者直接是 data 对象：{article_id: ..., title: ..., ...}
    // 需要从 responseData.data 或 responseData 中提取 article_id
    let articleId = null
    let actualData = null
    
    if (responseData && responseData.data) {
      // 格式：{status: 'success', data: {...}}
      actualData = responseData.data
      articleId = actualData.article_id || actualData.text_id
    } else if (responseData) {
      // 格式：直接是 data 对象
      actualData = responseData
      articleId = responseData.article_id || responseData.text_id
    }
    
    console.log('📄 [Upload] 提取的文章ID:', articleId, '实际数据:', actualData)
    
    // 如果是游客模式，保存到 localStorage
    if (actualData && actualData.is_guest && actualData.article_data) {
      const guestId = userId
      if (guestId) {
        const saved = guestDataManager.saveArticle(guestId, {
          article_id: articleId,
          title: actualData.title || actualData.article_data.title,
          ...actualData.article_data
        })
        if (saved) {
          console.log('✅ [Upload] 游客文章已保存到 localStorage')
        }
      }
    }
    
    // 🔧 调用完成回调，传递文章ID
    if (onUploadComplete) {
      console.log('📞 [Upload] 调用 onUploadComplete，articleId:', articleId)
      // 同时传递本次上传选择的语言，供父组件同步上边栏语言并跳转
      onUploadComplete(articleId, language)
    } else {
      console.warn('⚠️ [Upload] onUploadComplete 回调未提供')
    }
  }

  // 检查内容长度并处理
  const checkAndHandleLength = async (content, type, file = null, title = '') => {
    if (content.length > MAX_ARTICLE_LENGTH) {
      // 内容超出限制，显示对话框
      setPendingContent({ type, file, content, title })
      setShowLengthDialog(true)
      return false
    }
    return true
  }

  // 处理自动截取
  const handleTruncate = async () => {
    if (!pendingContent) return
    
    const { type, file, content, title, url } = pendingContent
    const truncatedContent = content.substring(0, MAX_ARTICLE_LENGTH)
    
    setShowLengthDialog(false)
    
    try {
      setShowProgress(true)
      onUploadStart && onUploadStart()
      
      let response
      if (type === 'file' || type === 'drop') {
        const fileName = file?.name || ''
        const fileExtension = '.' + fileName.split('.').pop().toLowerCase()
        const isPdf = fileExtension === '.pdf' || file?.type === 'application/pdf'
        const rawTitle = customTitle.trim() || title || fileName.replace(/\.[^/.]+$/, "")
        const articleTitle = rawTitle.length > MAX_TITLE_LENGTH 
          ? rawTitle.slice(0, MAX_TITLE_LENGTH) 
          : rawTitle

        if (isPdf) {
          // PDF 超长时，与 URL 一致：直接上传截取后的纯文本（跳过长度检查）
          response = await apiService.uploadText(truncatedContent, articleTitle, language, true)
        } else {
          // 对于纯文本文件，仍然走文件上传
          const blob = new Blob([truncatedContent], { type: 'text/plain' })
          const truncatedFile = new File([blob], fileName, { type: 'text/plain' })
          response = await apiService.uploadFile(truncatedFile, articleTitle, language)
        }
      } else if (type === 'text') {
        response = await apiService.uploadText(truncatedContent, title || 'Text Article', language)
      } else if (type === 'url') {
        // 对于URL，直接上传截取后的文本内容
        const rawTitle = customTitle.trim() || title || 'URL Article'
        const articleTitle = rawTitle.length > MAX_TITLE_LENGTH 
          ? rawTitle.slice(0, MAX_TITLE_LENGTH) 
          : rawTitle
        console.log('📝 [UploadInterface] 截取后上传URL内容，使用标题:', articleTitle)
        response = await apiService.uploadText(truncatedContent, articleTitle, language, true) // 🔧 传递 skipLengthCheck
      }
      
      console.log('✅ [Frontend] 截取后上传成功:', response)
      
      // 🔧 统一处理响应格式
      if (response && (response.success || response.status === 'success')) {
        const responseData = response.data || response
        handleUploadSuccess(responseData)
        // 清空文本输入
        if (type === 'text') {
          setTextContent('')
          setTextTitle('')
        }
        // 清空URL输入
        if (type === 'url') {
          const urlInput = document.querySelector('input[name="url"]')
          if (urlInput) urlInput.value = ''
        }
      } else {
        console.error('❌ [Frontend] 截取后上传响应格式错误:', response)
        setShowProgress(false)
        onUploadStart && onUploadStart(false)
        alert(t('上传失败: 响应格式错误'))
      }
      
      setPendingContent(null)
    } catch (error) {
      console.error('❌ [Frontend] 截取后上传失败:', error)
      setShowProgress(false)
      const errorMessage = error.response?.data?.error || error.response?.data?.detail || error.message || '未知错误'
      alert(t('上传失败: {error}').replace('{error}', errorMessage))
      setPendingContent(null)
    }
  }

  // 处理重新上传（取消）
  const handleCancel = () => {
    setShowLengthDialog(false)
    setPendingContent(null)
    // 清空文件选择
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
    // 清空URL输入（如果是URL上传）
    if (pendingContent && pendingContent.type === 'url') {
      const urlInput = document.querySelector('input[name="url"]')
      if (urlInput) urlInput.value = ''
    }
  }

  // 统一的文件上传入口：从 selectedFile 启动真正的上传流程
  const startFileUpload = async (file, sourceType = 'file') => {
    if (!file) {
      alert(t('请先选择或拖入文件'))
      return
    }

    console.log('📁 [Upload] Starting file upload:', {
      name: file.name,
      size: file.size,
      type: file.type,
      sourceType,
    })

    // 基本验证
    const validExtensions = ['.txt', '.md', '.pdf']
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase()
    if (!validExtensions.includes(fileExtension)) {
      alert(
        t('不支持的文件格式: {ext}。请上传 .txt、.md 或 .pdf 文件。').replace('{ext}', fileExtension)
      )
      return
    }

    try {
      const baseTitle = file.name.replace(/\.[^/.]+$/, '')

      // 仅对纯文本文件在前端预检查长度；PDF 让后端提取后再检查
      if (fileExtension === '.txt' || fileExtension === '.md') {
        const fileContent = await file.text()
        const canProceed = await checkAndHandleLength(
          fileContent,
          sourceType,
          file,
          baseTitle
        )
        if (!canProceed) {
          return // 等待用户在长度对话框中选择
        }
      }

      console.log('🚀 [Frontend] 发送文件上传请求...', {
        name: file.name,
        sourceType,
      })
      setShowProgress(true)
      onUploadStart && onUploadStart()
      setUploadMethod(sourceType)

      // 使用统一的apiService（自动添加认证头）
      const articleTitle = customTitle.trim() || baseTitle
      const response = await apiService.uploadFile(file, articleTitle, language)

      console.log('📥 [Frontend] 文件上传响应:', response)

      // 检查响应状态（响应拦截器已经返回了response.data，所以response就是{status, data, error}格式）
      if (response && response.status === 'error') {
        // 检查是否是长度超限错误
        const errorData = response.data
        if (errorData && errorData.error_code === 'CONTENT_TOO_LONG' && errorData.original_content) {
          console.log('⚠️ [Frontend] 检测到长度超限错误，显示对话框')
          setShowProgress(false)
          // 优先通知父组件显示对话框（避免 UploadInterface 在上传过程中卸载导致对话框丢失）
          if (onLengthExceeded) {
            onUploadStart && onUploadStart(false)
            onLengthExceeded({
              type: sourceType,
              file,
              content: errorData.original_content,
              title: articleTitle,
              language,
            })
            return
          }

          // fallback：本组件内对话框
          setPendingContent({
            type: sourceType,
            file,
            content: errorData.original_content,
            title: articleTitle,
          })
          setShowLengthDialog(true)
          return
        }

        // 其他错误
        setShowProgress(false)
        const errorMessage = response.error || '未知错误'
        alert(t('文件上传失败: {error}').replace('{error}', errorMessage))
        return
      }

      // 上传成功后，处理响应
      if (response && (response.success || response.status === 'success')) {
        handleUploadSuccess(response.data || response)
        // 清空已选择文件
        setSelectedFile(null)
        setSelectedFileSource(null)
        if (fileInputRef.current) {
          fileInputRef.current.value = ''
        }
      }
    } catch (error) {
      console.error('❌ [Frontend] 文件上传失败:', error)
      setShowProgress(false)

      // 检查是否是长度超限错误（网络错误等情况）
      const errorData = error.response?.data?.data
      if (errorData && errorData.error_code === 'CONTENT_TOO_LONG' && errorData.original_content) {
        if (onLengthExceeded) {
          onUploadStart && onUploadStart(false)
          onLengthExceeded({
            type: sourceType,
            file,
            content: errorData.original_content,
            title: customTitle.trim() || file.name.replace(/\.[^/.]+$/, ''),
            language,
          })
          return
        }

        // fallback：本组件内对话框
        setPendingContent({
          type: sourceType,
          file,
          content: errorData.original_content,
          title: file.name.replace(/\.[^/.]+$/, ''),
        })
        setShowLengthDialog(true)
        return
      }

      const errorMessage =
        error.response?.data?.error || error.response?.data?.detail || error.message || '未知错误'
      alert(t('文件上传失败: {error}').replace('{error}', errorMessage))
    }
  }

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = async (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0]
      console.log('📁 [Upload] File dropped:', file.name, 'size:', file.size, 'type:', file.type)

      // 验证文件类型（仅用于预先过滤明显错误）
      const validExtensions = ['.txt', '.md', '.pdf']
      const fileExtension = '.' + file.name.split('.').pop().toLowerCase()
      if (!validExtensions.includes(fileExtension)) {
        alert(
          t('不支持的文件格式: {ext}。请上传 .txt、.md 或 .pdf 文件。').replace('{ext}', fileExtension)
        )
        return
      }

      // 仅记录已选择文件，真正上传由"从文件上传"按钮触发
      setSelectedFile(file)
      setSelectedFileSource('drop')
    }
  }

  const handleFileSelect = async (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0]
      console.log('📁 [Upload] File selected:', file.name, 'size:', file.size, 'type:', file.type)
      // 验证文件类型（仅用于预先过滤明显错误）
      const validExtensions = ['.txt', '.md', '.pdf']
      const fileExtension = '.' + file.name.split('.').pop().toLowerCase()
      if (!validExtensions.includes(fileExtension)) {
        alert(
          t('不支持的文件格式: {ext}。请上传 .txt、.md 或 .pdf 文件。').replace('{ext}', fileExtension)
        )
        // 清空文件选择
        e.target.value = ''
        return
      }

      // 仅记录已选择文件，真正上传由"从文件上传"按钮触发
      setSelectedFile(file)
      setSelectedFileSource('file')
    }
  }

  // 统一的文件上传按钮点击处理
  const handleFileUploadClick = async () => {
    if (!selectedFile) {
      alert(t('请先选择文件或拖拽上传文件'))
      return
    }
    await startFileUpload(selectedFile, selectedFileSource || 'file')
  }

  const handleUrlSubmit = async (e) => {
    e.preventDefault()
    const url = e.target.url.value.trim()
    if (url) {
      console.log('🌐 [Upload] URL submitted:', url)
      setUploadMethod('url')
      
      // 基本URL验证
      try {
        new URL(url)
      } catch {
        alert(t('请输入有效的URL地址'))
        return
      }
      
      try {
        console.log('🚀 [Frontend] 发送URL处理请求...')
        setShowProgress(true)
        onUploadStart && onUploadStart()
        
        // 使用统一的apiService（自动添加认证头）
        const articleTitle = customTitle.trim() || 'URL Article'
        const response = await apiService.uploadUrl(url, articleTitle, language)
        
        console.log('📥 [Frontend] URL处理响应:', response)
        console.log('📥 [Frontend] response.status:', response?.status)
        console.log('📥 [Frontend] response.data:', response?.data)
        
        // 检查响应状态（响应拦截器已经返回了response.data，所以response就是{status, data, error}格式）
        if (response && response.status === 'error') {
          console.log('⚠️ [Frontend] 检测到错误响应')
          // 检查是否是长度超限错误
          const errorData = response.data
          console.log('⚠️ [Frontend] errorData:', errorData)
          console.log('⚠️ [Frontend] error_code:', errorData?.error_code)
          console.log('⚠️ [Frontend] original_content存在:', !!errorData?.original_content)
          
          if (errorData && errorData.error_code === 'CONTENT_TOO_LONG' && errorData.original_content) {
            console.log('⚠️ [Frontend] 检测到长度超限错误，通知父组件显示对话框')
            // 通知父组件不要显示进度条
            onUploadStart && onUploadStart(false)
            // 关闭进度条
            setShowProgress(false)
            // 通知父组件显示对话框
            if (onLengthExceeded) {
              try {
                onLengthExceeded({
                  type: 'url',
                  url: url,
                  content: errorData.original_content,
                  title: customTitle.trim() || 'URL Article', // 🔧 使用自定义标题
                  language: language
                })
              } catch (err) {
                console.error('❌ [Frontend] onLengthExceeded 回调执行失败:', err)
                // 如果回调失败，使用本地状态（向后兼容）
                const contentData = {
                  type: 'url',
                  url: url,
                  content: errorData.original_content,
                  title: customTitle.trim() || 'URL Article', // 🔧 使用自定义标题
                  language: language
                }
                pendingContentRef.current = contentData
                setPendingContent(contentData)
                setShowLengthDialog(true)
              }
            } else {
              // 如果没有回调，使用本地状态（向后兼容）
              const contentData = {
                type: 'url',
                url: url,
                content: errorData.original_content,
                title: 'URL Article',
                language: language
              }
              pendingContentRef.current = contentData
              setPendingContent(contentData)
              setShowLengthDialog(true)
            }
            console.log('✅ [Frontend] 已通知父组件显示对话框')
            return // 🔧 确保在长度超限时直接返回，不执行后续代码
          }
          
          // 其他错误
          setShowProgress(false)
          onUploadStart && onUploadStart(false)
          const errorMessage = response.error || '未知错误'
          alert(t('URL处理失败: {error}').replace('{error}', errorMessage))
          return // 🔧 确保在错误时直接返回
        }
        
        // 上传成功后，处理响应
        if (response && (response.success || response.status === 'success')) {
          const responseData = response.data || response
          handleUploadSuccess(responseData)
          
          // 清空URL输入
          e.target.url.value = ''
        } else {
          // 如果响应格式不正确，显示错误
          setShowProgress(false)
          onUploadStart && onUploadStart(false)
          console.error('❌ [Frontend] 响应格式不正确:', response)
          alert(t('URL处理失败: 响应格式不正确'))
        }
      } catch (error) {
        console.error('❌ [Frontend] URL处理失败:', error)
        setShowProgress(false)
        
        // 检查是否是长度超限错误（网络错误等情况）
        const errorData = error.response?.data?.data
        if (errorData && errorData.error_code === 'CONTENT_TOO_LONG' && errorData.original_content) {
          // 显示长度超限对话框
          setPendingContent({
            type: 'url',
            url: url,
            content: errorData.original_content,
            title: 'URL Article'
          })
          setShowLengthDialog(true)
          return
        }
        
        const errorMessage = error.response?.data?.error || error.response?.data?.detail || error.message || '未知错误'
        alert(t('URL处理失败: {error}').replace('{error}', errorMessage))
      }
    }
  }

  const handleTextSubmit = async (e) => {
    e.preventDefault()
    if (textContent.trim()) {
      // 检查语言是否已选择
      if (!language) {
        alert(t('请选择文章语言'))
        return
      }
      
      console.log('📝 [Upload] Text submitted:', { title: textTitle, contentLength: textContent.length, language })
      setUploadMethod('text')
      
      // 检查长度
      const canProceed = await checkAndHandleLength(textContent, 'text', null, textTitle || 'Text Article')
      
      if (!canProceed) {
        return // 等待用户选择
      }
      
      try {
        console.log('🚀 [Frontend] 发送文字处理请求...')
        setShowProgress(true)
        onUploadStart && onUploadStart()
        
        // 使用统一的apiService（自动添加认证头）
        const response = await apiService.uploadText(textContent, textTitle || 'Text Article', language)
        
        console.log('📥 [Frontend] 文字处理响应:', response)
        
        // 检查响应状态（响应拦截器已经返回了response.data，所以response就是{status, data, error}格式）
        if (response && response.status === 'error') {
          // 检查是否是长度超限错误
          const errorData = response.data
          if (errorData && errorData.error_code === 'CONTENT_TOO_LONG' && errorData.original_content) {
            console.log('⚠️ [Frontend] 检测到长度超限错误，显示对话框')
            setShowProgress(false)
            // 显示长度超限对话框
            setPendingContent({
              type: 'text',
              content: errorData.original_content,
              title: textTitle || 'Text Article'
            })
            setShowLengthDialog(true)
            return
          }
          
          // 其他错误
          setShowProgress(false)
          const errorMessage = response.error || '未知错误'
          alert(t('文字处理失败: {error}').replace('{error}', errorMessage))
          return
        }
        
        // 上传成功后，处理响应
        // 🔧 修复：检查 response.status === 'success' 或 response.success
        if (response && (response.success || response.status === 'success')) {
          handleUploadSuccess(response.data || response)
        }
        
        // 清空文本输入
        setTextContent('')
        setTextTitle('')
      } catch (error) {
        console.error('❌ [Frontend] 文字处理失败:', error)
        setShowProgress(false)
        
        // 检查是否是长度超限错误（网络错误等情况）
        const errorData = error.response?.data?.data
        if (errorData && errorData.error_code === 'CONTENT_TOO_LONG' && errorData.original_content) {
          // 显示长度超限对话框
          setPendingContent({
            type: 'text',
            content: errorData.original_content,
            title: textTitle || 'Text Article'
          })
          setShowLengthDialog(true)
          return
        }
        
        const errorMessage = error.response?.data?.error || error.response?.data?.detail || error.message || '未知错误'
        alert(t('文字处理失败: {error}').replace('{error}', errorMessage))
      }
    }
  }

  const triggerFileInput = () => {
    fileInputRef.current?.click()
  }

  // 长度超限对话框（使用 Portal 渲染到 body，确保始终显示）
  const lengthDialog = showLengthDialog && pendingContent ? (
    createPortal(
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center" 
        style={{ zIndex: 99999, position: 'fixed', top: 0, left: 0, right: 0, bottom: 0 }}
        onClick={(e) => {
          // 点击背景关闭对话框
          if (e.target === e.currentTarget) {
            handleCancel()
          }
        }}
      >
        <div 
          className="bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-xl"
          onClick={(e) => e.stopPropagation()}
        >
          <h3 className="text-xl font-semibold text-gray-800 mb-4">{t('文章长度超出限制')}</h3>
          <div className="mb-4">
            <p className="text-gray-600 mb-2">
              {t('文章长度为')} <span className="font-semibold text-red-600">{pendingContent.content.length.toLocaleString()}</span> {t('字符， 超过了最大限制')} <span className="font-semibold">{MAX_ARTICLE_LENGTH.toLocaleString()}</span> {t('字符。')}
            </p>
            <p className="text-sm text-gray-500">
              {t('如果选择自动截取，将只保留前 5,000 个字符。').replace('5,000', MAX_ARTICLE_LENGTH.toLocaleString())}
            </p>
          </div>
          <div className="flex gap-3 justify-end">
            <button
              onClick={handleCancel}
              className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
            >
              {t('重新上传')}
            </button>
            <button
              onClick={handleTruncate}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              {t('自动截取前面部分')}
            </button>
          </div>
        </div>
      </div>,
      document.body
    )
  ) : null
  
  // 调试：检查对话框是否应该渲染
  console.log('🔍 [Frontend] 渲染检查 - showLengthDialog:', showLengthDialog, 'pendingContent:', !!pendingContent, 'lengthDialog:', !!lengthDialog)

  if (showProgress) {
    return (
      <>
        {lengthDialog}
        {null} {/* 进度条由父组件处理 */}
      </>
    )
  }

  return (
    <>
      {lengthDialog}
      <div className="flex-1 min-w-0 flex flex-col gap-4 bg-white p-6 rounded-lg shadow-md overflow-y-auto h-full">
        {/* 标题行：返回按钮左对齐，标题居中 */}
        <div className="relative flex items-center">
          {onBack && (
            <BackButton onClick={onBack} />
          )}
          <h2 className="absolute left-1/2 transform -translate-x-1/2 text-xl font-semibold text-gray-800">{t('上传新文章')}</h2>
        </div>
      
      <div className="flex-1 flex flex-col items-center justify-center space-y-8">
        {/* Upload URL */}
        <div className="w-full max-w-md">
          <h3 className="text-lg font-medium text-gray-700 mb-4 text-center">{t('上传网址')}</h3>
          <form onSubmit={handleUrlSubmit} className="space-y-3">
            <input
              type="url"
              name="url"
              placeholder={t('请输入文章链接...')}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
            <input
              type="text"
              value={customTitle}
              maxLength={MAX_TITLE_LENGTH}
              onChange={(e) => setCustomTitle(e.target.value)}
              placeholder={t('自定义文章名（选填）')}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <button
              type="submit"
              className="w-full bg-green-600 text-white py-3 px-4 rounded-lg hover:bg-green-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {t('从网址上传')}
            </button>
          </form>
        </div>

        {/* Divider */}
        <div className="flex items-center w-full max-w-md">
          <div className="flex-1 border-t border-gray-300"></div>
          <span className="px-4 text-gray-500 text-sm">{t('或')}</span>
          <div className="flex-1 border-t border-gray-300"></div>
        </div>

        {/* Upload File - 合并选择和拖拽 */}
        <div className="w-full max-w-md">
          <h3 className="text-lg font-medium text-gray-700 mb-4 text-center">{t('上传文件')}</h3>
          <div className="space-y-3">
            <input
              type="text"
              value={customTitle}
              maxLength={MAX_TITLE_LENGTH}
              onChange={(e) => setCustomTitle(e.target.value)}
              placeholder={t('自定义文章名（选填）')}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
            />
            {/* 合并的拖拽和选择区域 */}
            <div
              className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
                dragActive 
                  ? 'border-blue-500 bg-blue-50' 
                  : 'border-gray-300 hover:border-gray-400'
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={triggerFileInput}
            >
              <div className="space-y-2">
                <svg 
                  className="mx-auto h-10 w-10 text-gray-400" 
                  stroke="currentColor" 
                  fill="none" 
                  viewBox="0 0 48 48"
                >
                  <path 
                    d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" 
                    strokeWidth={2} 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                  />
                </svg>
                {selectedFile ? (
                  <div className="text-gray-700">
                    <p className="font-medium">{t('已选择文件')}:</p>
                    <p className="text-sm break-all">{selectedFile.name}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {(selectedFile.size / 1024).toFixed(2)} KB
                    </p>
                  </div>
                ) : (
                  <div className="text-gray-600">
                    <span className="font-medium">{t('将文件拖到此处')}</span>
                    <p className="text-sm">{t('或点击选择')}</p>
                  </div>
                )}
                <p className="text-xs text-gray-500">
                  {t('支持：TXT、MD、PDF、DOC、DOCX')}
                </p>
              </div>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".txt,.md,.pdf"
              onChange={handleFileSelect}
              className="hidden"
            />
            {/* 统一的文件上传按钮 */}
            <button
              onClick={handleFileUploadClick}
              disabled={!selectedFile || !language}
              title={
                !language 
                  ? t('请先选择上传文章的语言') 
                  : !selectedFile 
                    ? t('请先选择文件或拖拽上传文件') 
                    : ''
              }
              className="w-full bg-green-600 text-white py-3 px-4 rounded-lg hover:bg-green-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {t('从文件上传')}
            </button>
          </div>
        </div>

        {/* Divider */}
        <div className="flex items-center w-full max-w-md">
          <div className="flex-1 border-t border-gray-300"></div>
          <span className="px-4 text-gray-500 text-sm">{t('或')}</span>
          <div className="flex-1 border-t border-gray-300"></div>
        </div>

        {/* Text Input */}
        <div className="w-full max-w-md">
          <h3 className="text-lg font-medium text-gray-700 mb-4 text-center">{t('输入文本')}</h3>
          <form onSubmit={handleTextSubmit} className="space-y-3">
            <input
              type="text"
              placeholder={t('文章标题（可选）...')}
              value={textTitle}
              onChange={(e) => setTextTitle(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
            <textarea
              placeholder={t('在此输入文章内容...')}
              value={textContent}
              onChange={(e) => setTextContent(e.target.value)}
              rows={6}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-vertical"
              required
            />
            <button
              type="submit"
              disabled={!textContent.trim() || !language}
              title={!language ? t('请先选择上传文章的语言') : (!textContent.trim() ? t('请输入文章内容') : '')}
              className="w-full bg-green-600 text-white py-3 px-4 rounded-lg hover:bg-green-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {t('处理文本')}
            </button>
          </form>
        </div>

        {/* Upload Status */}
        {uploadMethod && (
          <div className="w-full max-w-md">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center">
                <svg className="w-5 h-5 text-blue-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span className="text-blue-700">
                  {uploadMethod === 'url' && t('网址上传成功！')}
                  {uploadMethod === 'file' && t('文件上传成功！')}
                  {uploadMethod === 'drop' && t('拖拽上传成功！')}
                  {uploadMethod === 'text' && t('文本提交成功！')}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
      </div>
    </>
  )
}

export default UploadInterface
