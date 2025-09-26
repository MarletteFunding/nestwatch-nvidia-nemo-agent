import React from 'react';

interface IconProps {
  className?: string;
  size?: number;
}

// Geometric hawk icon for Hawky assistant
const HawkGeo: React.FC<IconProps> = ({ className = '', size = 24 }) => (
  <svg 
    width={size} 
    height={size} 
    viewBox="0 0 24 24" 
    fill="none" 
    className={className}
    xmlns="http://www.w3.org/2000/svg"
  >
    <path d="M12 3l3 2-1 4 2 1v3l-2 2-2-1-2 1-2-2v-3l2-1-1-4z" fill="currentColor"/>
    <circle cx="10" cy="8" r="1" fill="white"/>
    <circle cx="14" cy="8" r="1" fill="white"/>
    <path d="M12 10l-1 2h2z" fill="white"/>
  </svg>
);

export default HawkGeo;
