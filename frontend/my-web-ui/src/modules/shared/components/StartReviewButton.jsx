import React from 'react';
import { useUIText } from '../../../i18n/useUIText';

const StartReviewButton = ({ onClick, disabled = false, children }) => {
  const t = useUIText();
  const label = children ?? t('开始复习');

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="bg-[#5BE2C2] hover:bg-[#44c5a7] disabled:bg-gray-300 disabled:cursor-not-allowed text-white px-8 py-3 rounded-[40px] shadow-lg transition-all duration-300 transform hover:scale-105 focus:outline-none focus:ring-4 focus:ring-[#a8f4e3]"
    >
      <div className="flex items-center space-x-2">
        <svg 
          className="w-5 h-5" 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path 
            strokeLinecap="round" 
            strokeLinejoin="round" 
            strokeWidth={2} 
            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" 
          />
        </svg>
        <span className="font-semibold">{label}</span>
      </div>
    </button>
  );
};

export default StartReviewButton;
