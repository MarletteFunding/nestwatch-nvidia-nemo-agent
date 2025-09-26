// NestWatch Theme Utilities - Additive only, behind THEME_NESTWATCH feature flag
import React from 'react';

export interface ThemeConfig {
  enabled: boolean;
  theme: 'light' | 'dark' | 'auto';
}

// Feature flag check
export const isNestWatchThemeEnabled = (): boolean => {
  if (typeof window === 'undefined') return false;
  
  // Check for environment variable or localStorage flag
  const envFlag = process.env.NEXT_PUBLIC_THEME_NESTWATCH === 'true';
  const localFlag = localStorage.getItem('THEME_NESTWATCH') === 'true';
  
  return envFlag || localFlag;
};

// Apply theme data attributes
export const applyNestWatchTheme = (theme: 'light' | 'dark' | 'auto' = 'auto'): void => {
  if (!isNestWatchThemeEnabled()) return;
  
  const root = document.documentElement;
  
  // Set NestWatch theme flag
  root.setAttribute('data-nestwatch-theme', 'true');
  
  // Determine actual theme
  let actualTheme: 'light' | 'dark' = 'light';
  
  if (theme === 'auto') {
    actualTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  } else {
    actualTheme = theme;
  }
  
  // Set theme attribute
  root.setAttribute('data-theme', actualTheme);
};

// Remove NestWatch theme (fallback to original)
export const removeNestWatchTheme = (): void => {
  const root = document.documentElement;
  root.removeAttribute('data-nestwatch-theme');
  root.removeAttribute('data-theme');
};

// Hook for React components
export const useNestWatchTheme = () => {
  const [enabled, setEnabled] = React.useState(false);
  const [theme, setTheme] = React.useState<'light' | 'dark' | 'auto'>('auto');
  
  React.useEffect(() => {
    const isEnabled = isNestWatchThemeEnabled();
    setEnabled(isEnabled);
    
    if (isEnabled) {
      applyNestWatchTheme(theme);
    }
  }, [theme]);
  
  const toggleTheme = (newTheme: 'light' | 'dark' | 'auto') => {
    setTheme(newTheme);
    if (enabled) {
      applyNestWatchTheme(newTheme);
    }
  };
  
  return {
    enabled,
    theme,
    toggleTheme,
    isEnabled: isNestWatchThemeEnabled
  };
};
