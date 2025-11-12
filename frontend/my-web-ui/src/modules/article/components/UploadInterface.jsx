import { useState, useRef } from 'react'
import { apiService } from '../../../services/api'

const UploadInterface = ({ onUploadStart }) => {
  const [dragActive, setDragActive] = useState(false)
  const [uploadMethod, setUploadMethod] = useState(null) // 'url', 'file', 'drop', 'text'
  const [showProgress, setShowProgress] = useState(false)
  const [textContent, setTextContent] = useState('')
  const [textTitle, setTextTitle] = useState('')
  const fileInputRef = useRef(null)

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
      setUploadMethod('drop')
      
      // 验证文件类型
      const validExtensions = ['.txt', '.md']
      const fileExtension = '.' + file.name.split('.').pop().toLowerCase()
      if (!validExtensions.includes(fileExtension)) {
        alert(`不支持的文件格式: ${fileExtension}。请上传 .txt 或 .md 文件。`)
        return
      }
      
      try {
        console.log('🚀 [Frontend] 发送拖拽文件上传请求...')
        setShowProgress(true)
        onUploadStart && onUploadStart()
        
        // 使用统一的apiService（自动添加认证头）
        const response = await apiService.uploadFile(file, file.name.replace(/\.[^/.]+$/, ""))
        
        console.log('✅ [Frontend] 拖拽文件上传成功:', response)
        
        // 上传成功后，可以在这里处理响应（例如跳转到文章页面）
        if (response.data && response.data.success) {
          console.log('📄 [Upload] 文章已创建:', response.data.data)
        }
      } catch (error) {
        console.error('❌ [Frontend] 拖拽文件上传失败:', error)
        setShowProgress(false)
        const errorMessage = error.response?.data?.error || error.response?.data?.detail || error.message || '未知错误'
        alert(`文件上传失败: ${errorMessage}`)
      }
    }
  }

  const handleFileSelect = async (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0]
      console.log('📁 [Upload] File selected:', file.name, 'size:', file.size, 'type:', file.type)
      setUploadMethod('file')
      
      // 验证文件类型
      const validExtensions = ['.txt', '.md']
      const fileExtension = '.' + file.name.split('.').pop().toLowerCase()
      if (!validExtensions.includes(fileExtension)) {
        alert(`不支持的文件格式: ${fileExtension}。请上传 .txt 或 .md 文件。`)
        // 清空文件选择
        e.target.value = ''
        return
      }
      
      try {
        console.log('🚀 [Frontend] 发送文件上传请求...')
        setShowProgress(true)
        onUploadStart && onUploadStart()
        
        // 使用统一的apiService（自动添加认证头）
        const response = await apiService.uploadFile(file, file.name.replace(/\.[^/.]+$/, ""))
        
        console.log('✅ [Frontend] 文件上传成功:', response)
        
        // 上传成功后，可以在这里处理响应（例如跳转到文章页面）
        if (response.data && response.data.success) {
          console.log('📄 [Upload] 文章已创建:', response.data.data)
        }
        
        // 清空文件选择，允许再次选择同一文件
        e.target.value = ''
      } catch (error) {
        console.error('❌ [Frontend] 文件上传失败:', error)
        setShowProgress(false)
        const errorMessage = error.response?.data?.error || error.response?.data?.detail || error.message || '未知错误'
        alert(`文件上传失败: ${errorMessage}`)
        // 清空文件选择
        e.target.value = ''
      }
    }
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
        alert('请输入有效的URL地址')
        return
      }
      
      try {
        console.log('🚀 [Frontend] 发送URL处理请求...')
        setShowProgress(true)
        onUploadStart && onUploadStart()
        
        // 使用统一的apiService（自动添加认证头）
        const response = await apiService.uploadUrl(url, 'URL Article')
        
        console.log('✅ [Frontend] URL处理成功:', response)
        
        // 上传成功后，可以在这里处理响应（例如跳转到文章页面）
        if (response.data && response.data.success) {
          console.log('📄 [Upload] 文章已创建:', response.data.data)
        }
        
        // 清空URL输入
        e.target.url.value = ''
      } catch (error) {
        console.error('❌ [Frontend] URL处理失败:', error)
        setShowProgress(false)
        const errorMessage = error.response?.data?.error || error.response?.data?.detail || error.message || '未知错误'
        alert(`URL处理失败: ${errorMessage}`)
      }
    }
  }

  const handleTextSubmit = async (e) => {
    e.preventDefault()
    if (textContent.trim()) {
      console.log('📝 [Upload] Text submitted:', { title: textTitle, contentLength: textContent.length })
      setUploadMethod('text')
      
      try {
        console.log('🚀 [Frontend] 发送文字处理请求...')
        setShowProgress(true)
        onUploadStart && onUploadStart()
        
        // 使用统一的apiService（自动添加认证头）
        const response = await apiService.uploadText(textContent, textTitle || 'Text Article')
        
        console.log('✅ [Frontend] 文字处理成功:', response)
        
        // 上传成功后，可以在这里处理响应（例如跳转到文章页面）
        if (response.data && response.data.success) {
          console.log('📄 [Upload] 文章已创建:', response.data.data)
        }
        
        // 清空文本输入
        setTextContent('')
        setTextTitle('')
      } catch (error) {
        console.error('❌ [Frontend] 文字处理失败:', error)
        setShowProgress(false)
        const errorMessage = error.response?.data?.error || error.response?.data?.detail || error.message || '未知错误'
        alert(`文字处理失败: ${errorMessage}`)
      }
    }
  }

  const triggerFileInput = () => {
    fileInputRef.current?.click()
  }

  if (showProgress) {
    return null // 进度条由父组件处理
  }

  return (
    <div className="flex-1 min-w-0 flex flex-col gap-4 bg-white p-6 rounded-lg shadow-md overflow-y-auto h-full">
      <h2 className="text-xl font-semibold text-gray-800">Upload New Article</h2>
      
      <div className="flex-1 flex flex-col items-center justify-center space-y-8">
        {/* Upload URL */}
        <div className="w-full max-w-md">
          <h3 className="text-lg font-medium text-gray-700 mb-4 text-center">Upload URL</h3>
          <form onSubmit={handleUrlSubmit} className="space-y-3">
            <input
              type="url"
              name="url"
              placeholder="Enter article URL..."
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
            <button
              type="submit"
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Upload from URL
            </button>
          </form>
        </div>

        {/* Divider */}
        <div className="flex items-center w-full max-w-md">
          <div className="flex-1 border-t border-gray-300"></div>
          <span className="px-4 text-gray-500 text-sm">OR</span>
          <div className="flex-1 border-t border-gray-300"></div>
        </div>

        {/* Upload File */}
        <div className="w-full max-w-md">
          <h3 className="text-lg font-medium text-gray-700 mb-4 text-center">Upload File</h3>
          <button
            onClick={triggerFileInput}
            className="w-full bg-green-600 text-white py-3 px-4 rounded-lg hover:bg-green-700 transition-colors"
          >
            Choose File
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".txt,.md,.pdf,.doc,.docx"
            onChange={handleFileSelect}
            className="hidden"
          />
        </div>

        {/* Divider */}
        <div className="flex items-center w-full max-w-md">
          <div className="flex-1 border-t border-gray-300"></div>
          <span className="px-4 text-gray-500 text-sm">OR</span>
          <div className="flex-1 border-t border-gray-300"></div>
        </div>

        {/* Drop File */}
        <div className="w-full max-w-md">
          <h3 className="text-lg font-medium text-gray-700 mb-4 text-center">Drop File</h3>
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              dragActive 
                ? 'border-blue-500 bg-blue-50' 
                : 'border-gray-300 hover:border-gray-400'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <div className="space-y-2">
              <svg 
                className="mx-auto h-12 w-12 text-gray-400" 
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
              <div className="text-gray-600">
                <span className="font-medium">Drop your file here</span>
                <p className="text-sm">or click to browse</p>
              </div>
              <p className="text-xs text-gray-500">
                Supports: TXT, MD, PDF, DOC, DOCX
              </p>
            </div>
          </div>
        </div>

        {/* Divider */}
        <div className="flex items-center w-full max-w-md">
          <div className="flex-1 border-t border-gray-300"></div>
          <span className="px-4 text-gray-500 text-sm">OR</span>
          <div className="flex-1 border-t border-gray-300"></div>
        </div>

        {/* Text Input */}
        <div className="w-full max-w-md">
          <h3 className="text-lg font-medium text-gray-700 mb-4 text-center">Enter Text</h3>
          <form onSubmit={handleTextSubmit} className="space-y-3">
            <input
              type="text"
              placeholder="Article title (optional)..."
              value={textTitle}
              onChange={(e) => setTextTitle(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
            <textarea
              placeholder="Enter your article text here..."
              value={textContent}
              onChange={(e) => setTextContent(e.target.value)}
              rows={6}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-vertical"
              required
            />
            <button
              type="submit"
              disabled={!textContent.trim()}
              className="w-full bg-purple-600 text-white py-3 px-4 rounded-lg hover:bg-purple-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              Process Text
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
                  {uploadMethod === 'url' && 'URL uploaded successfully!'}
                  {uploadMethod === 'file' && 'File uploaded successfully!'}
                  {uploadMethod === 'drop' && 'File dropped successfully!'}
                  {uploadMethod === 'text' && 'Text submitted successfully!'}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default UploadInterface
