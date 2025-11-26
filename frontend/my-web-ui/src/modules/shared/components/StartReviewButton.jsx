import React from 'react';
import { useUIText } from '../../../i18n/useUIText';

const StartReviewButton = ({ onClick, disabled = false, children }) => {
  const t = useUIText();
  const label = children ?? t('开始复习');

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`
        px-6 py-3 bg-blue-600 text-white rounded-lg font-medium
        hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
        transition-colors duration-200
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
      `}
    >
      {label}
    </button>
  );
};

export default StartReviewButton;
