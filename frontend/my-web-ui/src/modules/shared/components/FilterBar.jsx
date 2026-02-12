import { useMemo, useState } from 'react'
import SingleFilterOption from './SingleFilterOption'
import { useUIText } from '../../../i18n/useUIText'

const FilterBar = ({ 
  filters = [], 
  onFilterChange = () => {},
  className = "",
  sortOrder = 'desc', // 'asc' 或 'desc'
  onSortChange = () => {}, // 排序变化回调
  onSearch = null,
  searchPlaceholder = '搜索...'
}) => {
  const t = useUIText()
  const [searchTerm, setSearchTerm] = useState('')

  // 默认筛选器配置
  const defaultFilters = useMemo(() => [
    {
      id: 'category',
      label: t('分类'),
      options: [
        { value: 'all', label: t('全部分类') },
        { value: 'fruits', label: t('水果') },
        { value: 'vegetables', label: t('蔬菜') },
        { value: 'animals', label: t('动物') }
      ],
      placeholder: t('选择分类')
    },
    {
      id: 'difficulty',
      label: t('难度'),
      options: [
        { value: 'all', label: t('全部难度') },
        { value: 'easy', label: t('简单') },
        { value: 'medium', label: t('中等') },
        { value: 'hard', label: t('困难') }
      ],
      placeholder: t('选择难度')
    },
    {
      id: 'status',
      label: t('状态'),
      options: [
        { value: 'all', label: t('全部状态') },
        { value: 'new', label: t('最新') },
        { value: 'reviewed', label: t('已复习') },
        { value: 'mastered', label: t('已掌握') }
      ],
      placeholder: t('选择状态')
    }
  ], [t])

  const filterConfigs = filters.length > 0 ? filters : defaultFilters

  const handleFilterChange = (filterId, value) => {
    onFilterChange(filterId, value)
  }

  const handleClearAll = () => {
    // 重置所有筛选器
    filterConfigs.forEach(filter => {
      handleFilterChange(filter.id, 'all')
    })
    // 清空搜索
    if (onSearch) {
      setSearchTerm('')
      onSearch('')
    }
  }

  const handleSearchChange = (e) => {
    const value = e.target.value
    setSearchTerm(value)
    if (onSearch) {
      onSearch(value)
    }
  }

  const handleSearchClick = () => {
    if (onSearch) {
      onSearch(searchTerm)
    }
  }

  // 统一的高度类，确保所有控件高度一致
  const controlHeight = "h-[38px]" // py-2 (0.5rem) + text-sm line-height ≈ 38px

  return (
    <div className={`w-full bg-white border border-gray-200 rounded-lg px-6 py-3 ${className}`}>
      <div className="max-w-6xl mx-auto">
        {/* 两行布局：标题行 + 控件行 */}
        <div className="flex flex-col gap-0">
          {/* 第一行：所有标题 */}
          <div className="flex items-center gap-6">
            {/* 筛选标题（隐藏文字但保留占位） */}
            <div className="w-24">
            </div>

            {/* 筛选器标题 */}
            {filterConfigs.map((filter) => {
              // 根据 filter.id 设置不同的宽度
              const widthClass = filter.id === 'text_id' 
                ? 'flex-1 max-w-[350px] min-w-0'  // 文章筛选框更宽，min-w-0 确保 truncate 生效
                : 'flex-1 max-w-[150px] min-w-0'  // 学习状态筛选框默认宽度
              return (
                <div key={filter.id} className={widthClass}>
                  <span className="text-sm font-medium text-gray-900">
                    {filter.label}
                  </span>
                </div>
              )
            })}

            {/* 排序标题 */}
            <div className="w-32">
              <span className="text-sm font-medium text-gray-900">
                {t('排序')}
              </span>
            </div>

            {/* 搜索标题占位（如果有搜索功能） */}
            {onSearch && (
              <div className="flex-1 max-w-xs"></div>
            )}
          </div>

          {/* 第二行：所有控件，使用 items-center 确保中间对齐 */}
          <div className="flex items-center gap-6">
            {/* 左侧：清除全部按钮 */}
            <div className="w-24 flex items-center">
              <button
                type="button"
                onClick={handleClearAll}
                className="text-xs text-gray-500 hover:text-gray-700 transition-colors"
              >
                {t('清除全部')}
              </button>
            </div>

            {/* 筛选器下拉框 */}
            {filterConfigs.map((filter) => {
              // 根据 filter.id 设置不同的宽度
              const widthClass = filter.id === 'text_id' 
                ? 'flex-1 max-w-[350px] min-w-0'  // 文章筛选框更宽，min-w-0 确保 truncate 生效
                : 'flex-1 max-w-[150px] min-w-0'  // 学习状态筛选框默认宽度
              return (
                <div key={filter.id} className={widthClass}>
                  <SingleFilterOption
                    label=""
                    options={filter.options}
                    placeholder={filter.placeholder}
                    value={filter.value || 'all'}
                    onChange={(value) => handleFilterChange(filter.id, value)}
                    className="w-full"
                  />
                </div>
              )
            })}

            {/* 排序按钮 */}
            <div className="w-32">
              <button
                type="button"
                onClick={() => {
                  const newOrder = sortOrder === 'desc' ? 'asc' : 'desc'
                  onSortChange(newOrder)
                }}
                className={`w-full ${controlHeight} px-3 border border-gray-300 rounded-md shadow-sm text-sm text-gray-700 bg-white hover:bg-[#f2fbf8] hover:border-[#5BE2C2] transition-colors flex items-center justify-between focus:outline-none focus:ring-2 focus:ring-[#5BE2C2] focus:border-[#5BE2C2]`}
                title={sortOrder === 'desc' ? t('按时间倒序（最新在前）') : t('按时间正序（最早在前）')}
              >
                <span>{sortOrder === 'desc' ? t('最新优先') : t('最早优先')}</span>
                {sortOrder === 'desc' ? (
                  <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                  </svg>
                )}
              </button>
            </div>

            {/* 搜索：输入框 + 按钮 */}
            {onSearch && (
              <div className="flex-1 max-w-xs flex items-center gap-2">
                <input
                  type="text"
                  value={searchTerm}
                  onChange={handleSearchChange}
                  placeholder={t(searchPlaceholder)}
                  className={`flex-1 ${controlHeight} px-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-[#5BE2C2] focus:border-[#5BE2C2] text-sm`}
                />
                <button
                  type="button"
                  onClick={handleSearchClick}
                  className={`${controlHeight} px-3 border border-gray-300 rounded-md text-sm text-gray-700 bg-white hover:bg-[#f2fbf8] hover:border-[#5BE2C2] transition-colors whitespace-nowrap`}
                >
                  {t('搜索')}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default FilterBar 