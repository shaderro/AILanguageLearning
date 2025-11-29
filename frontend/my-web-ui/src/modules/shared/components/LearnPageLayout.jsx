import StartReviewButton from './StartReviewButton'
import FilterBar from './FilterBar'
import SearchBar from './SearchBar'
import { useUIText } from '../../../i18n/useUIText'
import { BaseButton } from '../../../components/base/BaseButton'

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
    <div className={`${backgroundClass} p-8 min-h-[calc(100vh-64px)] overflow-auto`}>
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800">{title}</h1>
          <div className="flex items-center space-x-3">
            {showRefreshButton && onRefresh && (
              <BaseButton
                variant="secondary"
                size="sm"
                onClick={onRefresh}
                title={t('刷新数据')}
                leftIcon={
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                }
              >
                {t('刷新')}
              </BaseButton>
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
            />
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
