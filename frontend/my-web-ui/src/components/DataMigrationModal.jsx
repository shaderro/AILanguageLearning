/**
 * 数据迁移模态框
 * 
 * 在游客登录/注册时，询问是否迁移本地数据到新账号
 */
import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import guestDataManager from '../utils/guestDataManager'
import { apiService } from '../services/api'

const DataMigrationModal = ({ 
  isOpen, 
  onClose, 
  guestId, 
  onMigrationComplete 
}) => {
  const [isMigrating, setIsMigrating] = useState(false)
  const [error, setError] = useState('')
  const queryClient = useQueryClient()
  
  // 获取游客数据
  const guestData = guestId ? guestDataManager.getAllGuestData(guestId) : { vocabs: [], grammars: [], articles: [] }
  const hasData = guestId ? guestDataManager.hasGuestData(guestId) : false
  
  console.log('📦 [Migration] 游客数据:', guestData)

  const handleMigrate = async () => {
    setIsMigrating(true)
    setError('')
    
    try {
      console.log('🔄 [Migration] 开始迁移游客数据...')
      
      let migratedCount = 0
      
      // 迁移词汇
      for (const vocab of guestData.vocabs) {
        try {
          const response = await apiService.createVocab({
            vocab_body: vocab.vocab_body,
            explanation: vocab.explanation,
            source: 'manual',
            is_starred: vocab.is_starred || false
          })
          migratedCount++
          console.log('✅ [Migration] 词汇已迁移:', vocab.vocab_body)
        } catch (e) {
          // 检查是否是因为已存在
          const errorMsg = e.response?.data?.detail || e.message
          if (errorMsg && errorMsg.includes('already exists')) {
            console.log('⏭️ [Migration] 词汇已存在，跳过:', vocab.vocab_body)
            // 虽然跳过，但也算成功（数据已在账号中）
            migratedCount++
          } else {
            console.warn('⚠️ [Migration] 词汇迁移失败:', vocab.vocab_body, errorMsg)
          }
        }
      }
      
      // 迁移语法规则
      for (const grammar of guestData.grammars) {
        try {
          const response = await apiService.createGrammarRule({
            rule_name: grammar.rule_name,
            rule_summary: grammar.rule_summary,
            source: 'manual',
            is_starred: grammar.is_starred || false
          })
          migratedCount++
          console.log('✅ [Migration] 语法规则已迁移:', grammar.rule_name)
        } catch (e) {
          // 检查是否是因为已存在
          const errorMsg = e.response?.data?.detail || e.message
          if (errorMsg && errorMsg.includes('already exists')) {
            console.log('⏭️ [Migration] 语法规则已存在，跳过:', grammar.rule_name)
            // 虽然跳过，但也算成功（数据已在账号中）
            migratedCount++
          } else {
            console.warn('⚠️ [Migration] 语法规则迁移失败:', grammar.rule_name, errorMsg)
          }
        }
      }
      
      // 迁移文章（需要重新上传文章数据）
      for (const article of guestData.articles || []) {
        try {
          // 文章数据包含 sentences，需要重新构建文章文本
          // 注意：这里简化处理，实际可能需要更复杂的逻辑
          if (article.article_data && article.article_data.sentences) {
            // 重新上传文章（使用文章标题和内容）
            // 注意：这里需要根据实际情况调整
            console.log('📄 [Migration] 准备迁移文章:', article.title || article.article_data?.title)
            // TODO: 实现文章迁移逻辑（可能需要重新调用上传API或创建专门的导入API）
            console.log('⚠️ [Migration] 文章迁移功能待实现:', article.article_id)
            // 暂时跳过文章迁移
          }
        } catch (e) {
          console.warn('⚠️ [Migration] 文章迁移失败:', article.article_id, e.message)
        }
      }
      
      console.log(`✅ [Migration] 迁移完成，共 ${migratedCount} 条数据`)
      
      // 清空游客数据
      guestDataManager.clearGuestData(guestId)
      
      // 刷新 React Query 缓存，显示新数据
      console.log('🔄 [Migration] 刷新数据缓存...')
      queryClient.invalidateQueries({ queryKey: ['vocab'] })
      queryClient.invalidateQueries({ queryKey: ['grammar'] })
      queryClient.invalidateQueries({ queryKey: ['articles'] })
      
      if (onMigrationComplete) {
        onMigrationComplete(migratedCount)
      }
      
      onClose()
    } catch (error) {
      console.error('❌ [Migration] 迁移失败:', error)
      setError('数据迁移失败，请重试')
    } finally {
      setIsMigrating(false)
    }
  }

  const handleSkip = () => {
    console.log('⏭️ [Migration] 跳过数据迁移')
    // 不清空游客数据，用户可以稍后再迁移
    onClose()
  }

  if (!isOpen || !hasData) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-8 max-w-md w-full mx-4">
        {/* 标题 */}
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900">发现本地数据</h2>
          <p className="text-sm text-gray-600 mt-2">
            检测到您在游客模式下创建了一些数据，是否要迁移到新账号？
          </p>
        </div>

        {/* 数据统计 */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <div className="text-sm text-gray-700 space-y-2">
            <div className="flex justify-between">
              <span>📚 词汇:</span>
              <span className="font-semibold">{guestData.vocabs.length} 条</span>
            </div>
            <div className="flex justify-between">
              <span>📖 语法规则:</span>
              <span className="font-semibold">{guestData.grammars.length} 条</span>
            </div>
            <div className="flex justify-between">
              <span>📄 文章:</span>
              <span className="font-semibold">{(guestData.articles || []).length} 篇</span>
            </div>
          </div>
        </div>

        {/* 错误提示 */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm mb-4">
            {error}
          </div>
        )}

        {/* 按钮组 */}
        <div className="flex flex-col space-y-3">
          <button
            onClick={handleMigrate}
            disabled={isMigrating}
            className="w-full bg-blue-500 text-white py-3 px-4 rounded-md hover:bg-blue-600 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
          >
            {isMigrating ? '迁移中...' : '迁移数据到新账号'}
          </button>

          <button
            onClick={handleSkip}
            disabled={isMigrating}
            className="w-full bg-gray-200 text-gray-700 py-3 px-4 rounded-md hover:bg-gray-300 transition-colors disabled:bg-gray-100 font-medium"
          >
            跳过（稍后再迁移）
          </button>
        </div>

        {/* 说明 */}
        <div className="mt-6 text-xs text-gray-500 border-t border-gray-200 pt-4">
          <p>💡 提示：如果跳过，您的游客数据仍会保留在本地，下次可以继续使用或迁移。</p>
        </div>
      </div>
    </div>
  )
}

export default DataMigrationModal

