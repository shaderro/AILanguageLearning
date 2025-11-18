import SingleFilterOption from './SingleFilterOption'

const FilterBar = ({ 
  filters = [], 
  onFilterChange = () => {},
  className = "",
  sortOrder = 'desc', // 'asc' 或 'desc'
  onSortChange = () => {} // 排序变化回调
}) => {
  // 默认筛选器配置
  const defaultFilters = [
    {
      id: 'category',
      label: 'Category',
      options: [
        { value: 'all', label: 'All Categories' },
        { value: 'fruits', label: 'Fruits' },
        { value: 'vegetables', label: 'Vegetables' },
        { value: 'animals', label: 'Animals' }
      ],
      placeholder: 'Select category'
    },
    {
      id: 'difficulty',
      label: 'Difficulty',
      options: [
        { value: 'all', label: 'All Levels' },
        { value: 'easy', label: 'Easy' },
        { value: 'medium', label: 'Medium' },
        { value: 'hard', label: 'Hard' }
      ],
      placeholder: 'Select difficulty'
    },
    {
      id: 'status',
      label: 'Status',
      options: [
        { value: 'all', label: 'All Status' },
        { value: 'new', label: 'New' },
        { value: 'reviewed', label: 'Reviewed' },
        { value: 'mastered', label: 'Mastered' }
      ],
      placeholder: 'Select status'
    }
  ]

  const filterConfigs = filters.length > 0 ? filters : defaultFilters

  const handleFilterChange = (filterId, value) => {
    onFilterChange(filterId, value)
  }

  return (
    <div className={`w-full h-[100px] bg-gray-50 border-b border-gray-200 px-6 py-2 ${className}`}>
      <div className="max-w-6xl mx-auto h-full">
        {/* Filter Bar Content */}
        <div className="flex items-center justify-between h-full">
          {/* Filters Title */}
          <div className="flex items-center">
            <h2 className="text-lg font-semibold text-gray-900 mr-8">Filters</h2>
          </div>

          {/* Filter Options */}
          <div className="flex items-center space-x-6 flex-1">
            {filterConfigs.map((filter) => (
              <div key={filter.id} className="flex-1 max-w-xs">
                <SingleFilterOption
                  label={filter.label}
                  options={filter.options}
                  placeholder={filter.placeholder}
                  value={filter.value || 'all'}
                  onChange={(value) => handleFilterChange(filter.id, value)}
                  className="w-full"
                />
              </div>
            ))}
            
            {/* 时间排序按钮 */}
            <div className="flex items-end">
              <button
                onClick={() => {
                  const newOrder = sortOrder === 'desc' ? 'asc' : 'desc'
                  onSortChange(newOrder)
                }}
                className="px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 flex items-center space-x-2"
                title={sortOrder === 'desc' ? '按时间倒序（最新在前）' : '按时间正序（最早在前）'}
              >
                <span className="text-sm font-medium text-gray-700">时间排序</span>
                {sortOrder === 'desc' ? (
                  <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                  </svg>
                )}
              </button>
            </div>
          </div>

          {/* Clear All Button */}
          <div className="flex items-center ml-6">
            <button
              onClick={() => {
                // 重置所有筛选器
                filterConfigs.forEach(filter => {
                  handleFilterChange(filter.id, 'all')
                })
              }}
              className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
            >
              Clear All
            </button>
          </div>
        </div>

        {/* Active Filters Display */}
        <div className="flex flex-wrap gap-2 mt-2">
          {filterConfigs.map((filter) => {
            const selectedOption = filter.options.find(option => option.value === filter.value)
            if (selectedOption && selectedOption.value !== 'all') {
              return (
                <span
                  key={filter.id}
                  className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                >
                  {filter.label}: {selectedOption.label}
                  <button
                    onClick={() => handleFilterChange(filter.id, 'all')}
                    className="ml-1 text-blue-600 hover:text-blue-800"
                  >
                    ×
                  </button>
                </span>
              )
            }
            return null
          })}
        </div>
      </div>
    </div>
  )
}

export default FilterBar 