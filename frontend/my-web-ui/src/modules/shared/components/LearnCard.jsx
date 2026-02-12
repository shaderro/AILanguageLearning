import CardBase from './CardBase'
import { useUIText } from '../../../i18n/useUIText'

const LearnCard = ({ 
  data, 
  onClick, 
  type = 'vocab', // 'vocab' or 'grammar'
  loading = false,
  error = null,
  customContent = null,
  onToggleStar = null // 新增收藏切换回调
}) => {
  const t = useUIText()

  // 解析和格式化解释文本
  const parseExplanation = (text, vocabBody = null) => {
    if (!text) return ''
    
    let cleanText = text
    
    // 1. 处理字典格式的字符串（如 "{'explanation': '...'}" 或 '{"explanation": "..."}'）
    if (text.includes("'explanation'") || text.includes('"explanation"')) {
      try {
        // 尝试解析 JSON 格式
        const jsonMatch = text.match(/\{[\s\S]*\}/)
        if (jsonMatch) {
          const jsonStr = jsonMatch[0]
          // 先尝试标准 JSON 解析
          try {
            const parsed = JSON.parse(jsonStr)
            cleanText = parsed.explanation || parsed.definition || text
          } catch (e) {
            // 如果不是标准 JSON，尝试处理 Python 字典格式（单引号）
            // 使用更智能的方法：只替换键和字符串分隔符的单引号
            // 先尝试直接提取 explanation 字段的值（支持多行和转义字符）
            const explanationMatch = text.match(/['"]explanation['"]\s*:\s*['"]([\s\S]*?)['"]\s*[,}]/s)
            if (explanationMatch) {
              cleanText = explanationMatch[1]
                .replace(/\\n/g, '\n')  // 处理转义的换行符
                .replace(/\\'/g, "'")   // 处理转义的单引号
                .replace(/\\"/g, '"')   // 处理转义的双引号
            } else {
              // 如果正则匹配失败，尝试将单引号替换为双引号（简单处理）
              const normalized = jsonStr.replace(/'/g, '"')
              try {
                const parsed = JSON.parse(normalized)
                cleanText = parsed.explanation || parsed.definition || text
              } catch (e2) {
                // 如果还是失败，使用原始文本
                cleanText = text
              }
            }
          }
        }
      } catch (e) {
        // 解析失败，使用原始文本
      }
    }
    
    // 2. 处理代码块格式（```json ... ```）
    if (cleanText.includes('```json') && cleanText.includes('```')) {
      try {
        const jsonMatch = cleanText.match(/```json\n(.*?)\n```/s)
        if (jsonMatch) {
          const jsonStr = jsonMatch[1]
          const parsed = JSON.parse(jsonStr)
          cleanText = parsed.explanation || parsed.definition || cleanText
        }
      } catch (e) {
        // 解析失败，继续使用 cleanText
      }
    }
    
    // 3. 清理多余的转义字符和格式化
    // 将 \n 转换为实际的换行
    cleanText = cleanText.replace(/\\n/g, '\n')
    // 移除多余的空白行（连续两个以上的换行符）
    cleanText = cleanText.replace(/\n{3,}/g, '\n\n')
    // 去除首尾空白
    cleanText = cleanText.trim()
    
    // 4. 如果是 vocab 类型，去掉开头的单词原型（在所有解析完成后）
    if (vocabBody) {
      // 转义特殊字符，支持大小写不敏感匹配
      const escapedVocabBody = vocabBody.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
      // 匹配开头的单词原型（可能后面跟着换行、冒号、空格等）
      const regex = new RegExp(`^\\s*${escapedVocabBody}\\s*[:：]?\\s*\\n?`, 'i')
      cleanText = cleanText.replace(regex, '')
      // 再次去除首尾空白
      cleanText = cleanText.trim()
    }
    
    return cleanText
  }

  // 格式化学习状态显示文本
  const formatLearnStatus = (learnStatus) => {
    if (!learnStatus) return t('未掌握')
    if (learnStatus === 'mastered') return t('已掌握')
    if (learnStatus === 'not_mastered') return t('未掌握')
    return t('未掌握') // 默认值
  }

  // 获取学习状态显示颜色
  const getLearnStatusColor = (learnStatus) => {
    if (!learnStatus) return 'text-gray-400'
    if (learnStatus === 'mastered') return 'text-green-600'
    if (learnStatus === 'not_mastered') return 'text-gray-400'
    return 'text-gray-400'
  }

  // 根据数据类型确定显示内容
  const getCardContent = () => {
    if (customContent) {
      return customContent
    }

    if (type === 'vocab') {
      return (
        <>
          <div className="flex-1 space-y-2">
            {/* 词汇本身 */}
            <div className="text-lg font-semibold text-gray-900">
              {data?.vocab_body || t('未知词汇')}
            </div>
            
            {/* 解释内容 */}
            {data?.explanation && (
              <div>
                <div className="text-gray-800 leading-relaxed text-sm line-clamp-4">
                  {parseExplanation(data.explanation, data?.vocab_body)}
                </div>
              </div>
            )}
          </div>
          
          {/* 学习状态显示 - 固定在底部 */}
          <div className="text-xs mt-4">
            <span className={getLearnStatusColor(data?.learn_status)}>
              {t('状态')}: {formatLearnStatus(data?.learn_status)}
            </span>
          </div>
        </>
      )
    }

    if (type === 'grammar') {
      return (
        <>
          <div className="flex-1 space-y-2">
            {/* 语法规则名称 */}
            <div className="text-lg font-semibold text-gray-900">
              {data?.rule_name || t('未知规则')}
            </div>
            
            {/* 解释内容 */}
            {data?.rule_summary && (
              <div>
                <div className="text-gray-800 leading-relaxed text-sm line-clamp-4">
                  {parseExplanation(data.rule_summary)}
                </div>
              </div>
            )}
          </div>
          
          {/* 学习状态显示 - 固定在底部 */}
          <div className="text-xs mt-4">
            <span className={getLearnStatusColor(data?.learn_status)}>
              {t('状态')}: {formatLearnStatus(data?.learn_status)}
            </span>
          </div>
        </>
      )
    }

    return null
  }

  // 获取卡片标题 - 现在标题已经在内容中显示，所以返回空字符串
  const getCardTitle = () => {
    return ''
  }

  return (
    <CardBase
      title={getCardTitle()}
      data={data}
      loading={loading}
      error={error}
      onClick={onClick}
      className="bg-white rounded-lg border border-gray-200 p-4 transition-all duration-300 cursor-pointer transform hover:scale-105 transition-transform h-full flex flex-col"
    >
      {getCardContent()}
    </CardBase>
  )
}

export default LearnCard
