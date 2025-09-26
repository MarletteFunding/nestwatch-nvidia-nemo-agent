// NestWatch Icon System - Additive only, behind THEME_NESTWATCH feature flag
// All icons are 24x24 viewBox with 2px stroke, consistent rounded geometry

// Priority/Status Icons
export { default as CriticalDiamond, CriticalDiamondOutline } from './CriticalDiamond';
export { default as WarningTriangle, WarningTriangleSolid } from './WarningTriangle';
export { default as InfoCircle, InfoCircleSolid } from './InfoCircle';
export { default as SuccessCheck, SuccessCheckSolid } from './SuccessCheck';

// Utility Icons
export { default as Filter } from './Filter';
export { default as Refresh } from './Refresh';

// Brand Icons
export { default as HawkGeo } from './HawkGeo';

// Icon Props Interface
export interface IconProps {
  className?: string;
  size?: number;
}
