import StartReviewButton from './StartReviewButton'
import FilterBar from './FilterBar'
import SearchBar from './SearchBar'

const LearnPageLayout = ({ 
  title, 
  children, 
  onStartReview, 
  onFilterChange,
  filters,
  onSearch,
  searchPlaceholder = "搜索...",
  showFilters = true,
  showSearch = true,
  showReviewButton = true,
  backgroundClass = "bg-gray-100",
  onRefresh = null,
  showRefreshButton = false
}) => {
  return (
    <div className={`${backgroundClass} p-8 min-h-[calc(100vh-64px)] overflow-auto`}>
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800">{title}</h1>
          <div className="flex items-center space-x-3">
            {showRefreshButton && onRefresh && (
              <button
                onClick={onRefresh}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
                title="刷新数据"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <span>刷新</span>
              </button>
            )}
            {showReviewButton && (
              <StartReviewButton onClick={onStartReview} />
            )}
          </div>
        </div>

        {/* Search Bar */}
        {showSearch && (
          <div className="mb-4">
            <SearchBar 
              placeholder={searchPlaceholder}
              onSearch={onSearch}
            />
          </div>
        )}

        {/* Filters (below search) */}
        {showFilters && (
          <div className="mb-6">
            <FilterBar onFilterChange={onFilterChange} filters={filters} />
          </div>
        )}

        {/* Content */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {children}
        </div>
      </div>
    </div>
  )
}

export default LearnPageLayout
