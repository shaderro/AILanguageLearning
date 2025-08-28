import { navigationConfig } from '../config/navigation'

const Navigation = ({ currentPage, onPageChange, title, pages = [] }) => {
  // 使用传入的配置或默认配置
  const navigationTitle = title || navigationConfig.title
  const navigationPages = pages.length > 0 ? pages : navigationConfig.pages

  return (
    <nav className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo/Title */}
          <div className="flex items-center">
            <h1 className="text-xl font-semibold text-gray-900">{navigationTitle}</h1>
          </div>

          {/* Navigation Buttons */}
          <div className="flex items-center space-x-4">
            {navigationPages.map((page) => (
              <button
                key={page.id}
                onClick={() => onPageChange(page.id)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 flex items-center space-x-2 ${
                  currentPage === page.id
                    ? 'bg-blue-500 text-white shadow-md'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
                title={page.description || page.label}
              >
                {page.icon && <span className="text-base">{page.icon}</span>}
                <span>{page.label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navigation 