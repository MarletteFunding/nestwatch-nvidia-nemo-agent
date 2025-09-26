import React from 'react';
import { HawkGeo } from '../icons/nestwatch';

interface HawkyFabProps {
  onClick?: () => void;
  className?: string;
  disabled?: boolean;
}

// Hawky Floating Action Button - Additive component, no side effects
const HawkyFab: React.FC<HawkyFabProps> = ({ 
  onClick, 
  className = '', 
  disabled = false 
}) => {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`nw-fab ${className}`}
      aria-label="Open Hawky AI Assistant"
    >
      <HawkGeo size={24} />
    </button>
  );
};

export default HawkyFab;

// Named export for consistency
export { HawkyFab };
