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
  backgroundClass = "bg-gray-100"
}) => {
  return (
    <div className={`h-full ${backgroundClass} p-8`}>
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800">{title}</h1>
          {showReviewButton && (
            <StartReviewButton onClick={onStartReview} />
          )}
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
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {children}
        </div>
      </div>
    </div>
  )
}

export default LearnPageLayout
