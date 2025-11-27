import React from 'react';
import { useUIText } from '../../../i18n/useUIText';
import { BaseButton } from '../../../components/base';

const StartReviewButton = ({ onClick, disabled = false, children }) => {
  const t = useUIText();
  const label = children ?? t('开始复习');

  return (
    <BaseButton
      onClick={onClick}
      disabled={disabled}
      size="lg"
      fullWidth
      className="max-w-md"
    >
      {label}
    </BaseButton>
  );
};

export default StartReviewButton;
