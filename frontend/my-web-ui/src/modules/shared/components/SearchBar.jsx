import { useState } from 'react'
import { useUIText } from '../../../i18n/useUIText'

const SearchBar = ({ placeholder = '搜索...', onSearch, className = '' }) => {
  const [searchTerm, setSearchTerm] = useState('')
  const t = useUIText()

  const handleSearch = (e) => {
    e.preventDefault()
    if (onSearch) {
      onSearch(searchTerm)
    }
  }

  const handleInputChange = (e) => {
    const value = e.target.value
    setSearchTerm(value)
    if (onSearch) {
      onSearch(value)
    }
  }

  return (
    <div className={`${className}`}>
      <form onSubmit={handleSearch} className="flex gap-2">
        <input
          type="text"
          placeholder={t(placeholder)}
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          value={searchTerm}
          onChange={handleInputChange}
        />
        <button
          type="submit"
          className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
        >
          {t('搜索')}
        </button>
      </form>
    </div>
  )
}

export default SearchBar