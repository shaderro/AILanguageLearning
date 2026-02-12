import StartReviewButton from './StartReviewButton'
import FilterBar from './FilterBar'
import SearchBar from './SearchBar'
import { useUIText } from '../../../i18n/useUIText'

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
  showRefreshButton = false,
  sortOrder = 'desc',
  onSortChange = () => {}
}) => {
  const t = useUIText()
  const placeholderText = searchPlaceholder ? t(searchPlaceholder) : t('搜索...')

  return (
    <div className={`${backgroundClass} p-8 min-h-[calc(100vh-64px)] overflow-auto relative`}>
      <div className="max-w-6xl mx-auto">

        {/* Search Bar（仅在未集成到 FilterBar 时显示） */}
        {showSearch && !onSearch && (
          <div className="mb-4">
            <SearchBar 
              placeholder={placeholderText}
              onSearch={onSearch}
            />
          </div>
        )}

        {/* Filters (below search) */}
        {showFilters && (
          <div className="mb-6">
            <FilterBar 
              onFilterChange={onFilterChange} 
              filters={filters}
              sortOrder={sortOrder}
              onSortChange={onSortChange}
              onSearch={onSearch}
              searchPlaceholder={searchPlaceholder}
            />
          </div>
        )}

        {/* Content */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {children}
        </div>
      </div>
      
      {/* Start Review Button - Fixed Position (Floating) */}
      {showReviewButton && onStartReview && (
        <div className="fixed bottom-8 left-1/2 transform -translate-x-1/2 z-50">
          <StartReviewButton onClick={onStartReview} />
        </div>
      )}
    </div>
  )
}

export default LearnPageLayout
