import React from 'react';

interface IconProps {
  className?: string;
  size?: number;
}

// Solid variant (default)
const CriticalDiamond: React.FC<IconProps> = ({ className = '', size = 24 }) => (
  <svg 
    width={size} 
    height={size} 
    viewBox="0 0 24 24" 
    fill="none" 
    className={className}
    xmlns="http://www.w3.org/2000/svg"
  >
    <path d="M12 2l8 10-8 10-8-10z" fill="currentColor"/>
    <path d="M11 8h2v6h-2z" fill="white"/>
    <circle cx="12" cy="16" r="1" fill="white"/>
  </svg>
);

// Outline variant
export const CriticalDiamondOutline: React.FC<IconProps> = ({ className = '', size = 24 }) => (
  <svg 
    width={size} 
    height={size} 
    viewBox="0 0 24 24" 
    fill="none" 
    className={className}
    xmlns="http://www.w3.org/2000/svg"
  >
    <path d="M12 2l8 10-8 10-8-10z" stroke="currentColor" strokeWidth="2" fill="none"/>
    <path d="M11 8h2v6h-2z" stroke="currentColor" strokeWidth="2"/>
    <circle cx="12" cy="16" r="1" fill="currentColor"/>
  </svg>
);

export default CriticalDiamond;
