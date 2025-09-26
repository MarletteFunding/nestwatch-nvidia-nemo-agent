import React from 'react';

interface IconProps {
  className?: string;
  size?: number;
}

// Outline variant (default)
const InfoCircle: React.FC<IconProps> = ({ className = '', size = 24 }) => (
  <svg 
    width={size} 
    height={size} 
    viewBox="0 0 24 24" 
    fill="none" 
    className={className}
    xmlns="http://www.w3.org/2000/svg"
  >
    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
    <path d="M12 16v-4M12 8h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
  </svg>
);

// Solid variant
export const InfoCircleSolid: React.FC<IconProps> = ({ className = '', size = 24 }) => (
  <svg 
    width={size} 
    height={size} 
    viewBox="0 0 24 24" 
    fill="none" 
    className={className}
    xmlns="http://www.w3.org/2000/svg"
  >
    <circle cx="12" cy="12" r="10" fill="currentColor"/>
    <path d="M11 12h2v4h-2z" fill="white"/>
    <circle cx="12" cy="8" r="1" fill="white"/>
  </svg>
);

export default InfoCircle;
