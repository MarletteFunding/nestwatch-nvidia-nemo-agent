import React from 'react';

interface IconProps {
  className?: string;
  size?: number;
}

// Outline variant (default)
const WarningTriangle: React.FC<IconProps> = ({ className = '', size = 24 }) => (
  <svg 
    width={size} 
    height={size} 
    viewBox="0 0 24 24" 
    fill="none" 
    className={className}
    xmlns="http://www.w3.org/2000/svg"
  >
    <path d="M12 2l8 18H4z" stroke="currentColor" strokeWidth="2" fill="none"/>
    <path d="M12 9v4M12 17h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
  </svg>
);

// Solid variant
export const WarningTriangleSolid: React.FC<IconProps> = ({ className = '', size = 24 }) => (
  <svg 
    width={size} 
    height={size} 
    viewBox="0 0 24 24" 
    fill="none" 
    className={className}
    xmlns="http://www.w3.org/2000/svg"
  >
    <path d="M12 2l8 18H4z" fill="currentColor"/>
    <path d="M11 9h2v4h-2z" fill="white"/>
    <circle cx="12" cy="17" r="1" fill="white"/>
  </svg>
);

export default WarningTriangle;
