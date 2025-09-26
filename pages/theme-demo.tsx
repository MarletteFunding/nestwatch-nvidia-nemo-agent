import React, { useState } from 'react';
import Head from 'next/head';
import NestWatchDemo from '../components/NestWatchDemo';

const ThemeDemoPage: React.FC = () => {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  return (
    <>
      <Head>
        <title>NestWatch Theme Demo</title>
        <meta name="description" content="Experience the NestWatch design system" />
      </Head>
      
      {/* Theme Toggle Controls */}
      <div className="fixed top-4 right-4 z-50 bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4 border">
        <div className="flex gap-2">
          <button
            onClick={() => setTheme('light')}
            className={`px-3 py-2 rounded text-sm font-medium transition-colors ${
              theme === 'light' 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Light
          </button>
          <button
            onClick={() => setTheme('dark')}
            className={`px-3 py-2 rounded text-sm font-medium transition-colors ${
              theme === 'dark' 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Dark
          </button>
        </div>
      </div>

      <NestWatchDemo theme={theme} />
    </>
  );
};

export default ThemeDemoPage;
