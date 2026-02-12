import { useState, useRef, useEffect } from 'react'
import { useUIText } from '../../../i18n/useUIText'

const SingleFilterOption = ({ 
  label = "筛选", 
  options = [], 
  value = "", 
  onChange = () => {},
  placeholder = "选择选项",
  className = ""
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const [selectedValue, setSelectedValue] = useState(value)
  const dropdownRef = useRef(null)
  const t = useUIText()

  // 点击外部关闭下拉框
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [])

  // 更新选中值
  useEffect(() => {
    setSelectedValue(value)
  }, [value])

  const handleSelect = (option) => {
    setSelectedValue(option.value)
    onChange(option.value)
    setIsOpen(false)
  }

  const selectedOption = options.find(option => option.value === selectedValue)

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      {/* Label */}
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label}
      </label>
      
      {/* Dropdown Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={`
          w-full h-[38px] px-3 text-left bg-white border border-gray-300 rounded-md shadow-sm
          focus:outline-none focus:ring-2 focus:ring-[#5BE2C2] focus:border-[#5BE2C2]
          hover:border-[#5BE2C2] transition-colors duration-200 flex items-center min-w-0
          ${isOpen ? 'ring-2 ring-[#5BE2C2] border-[#5BE2C2]' : ''}
        `}
      >
        <div className="flex items-center justify-between min-w-0 flex-1 overflow-hidden">
          <span className={`${selectedOption ? 'text-gray-900' : 'text-gray-500'} truncate flex-1 min-w-0`}>
            {selectedOption ? selectedOption.label : t(placeholder)}
          </span>
          <svg 
            className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${
              isOpen ? 'rotate-180' : ''
            }`} 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg">
          <ul className="py-1 max-h-60 overflow-auto">
            {options.length > 0 ? (
              options.map((option) => (
                <li key={option.value}>
                  <button
                    type="button"
                    onClick={() => handleSelect(option)}
                    className={`
                      w-full px-3 py-2 text-left hover:bg-[#f2fbf8] transition-colors truncate
                      ${selectedValue === option.value ? 'bg-[#f2fbf8] text-[#84c4b5]' : 'text-gray-900'}
                    `}
                    title={option.label}
                  >
                    {option.label}
                  </button>
                </li>
              ))
            ) : (
              <li className="px-3 py-2 text-gray-500 text-sm">
                {t('暂无可选项')}
              </li>
            )}
          </ul>
        </div>
      )}
    </div>
  )
}

export default SingleFilterOption 