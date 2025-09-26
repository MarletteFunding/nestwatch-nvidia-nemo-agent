import React from 'react';
import { CriticalDiamond, WarningTriangle, InfoCircle, SuccessCheck, HawkGeo } from '../ui/icons/nestwatch';
import { HawkyFab } from '../ui/fab/HawkyFab';

interface NestWatchDemoProps {
  theme?: 'light' | 'dark';
}

const NestWatchDemo: React.FC<NestWatchDemoProps> = ({ theme = 'light' }) => {
  return (
    <div 
      data-nestwatch-theme="true" 
      data-theme={theme}
      className="p-8 min-h-screen transition-colors duration-200"
      style={{ 
        backgroundColor: theme === 'dark' ? 'var(--nw-navy-tint)' : 'var(--nw-beige)',
        color: theme === 'dark' ? 'var(--nw-white)' : 'var(--nw-navy)'
      }}
    >
      {/* Header */}
      <div className="mb-8">
        <h1 className="nw-heading text-4xl mb-2">NestWatch Theme Demo</h1>
        <p className="nw-body">Experience the new NestWatch design system with modern components and accessibility features.</p>
      </div>

      {/* Priority Chips */}
      <section className="mb-8">
        <h2 className="nw-subtitle mb-4">Priority Event Chips</h2>
        <div className="flex flex-wrap gap-4">
          <div className="nw-chip nw-chip--p1 nw-focus-ring" tabIndex={0}>
            <CriticalDiamond size={16} className="mr-2" />
            P1 Critical
          </div>
          <div className="nw-chip nw-chip--p2 nw-focus-ring" tabIndex={0}>
            <WarningTriangle size={16} className="mr-2" />
            P2 High Priority
          </div>
          <div className="nw-chip nw-chip--p3 nw-focus-ring" tabIndex={0}>
            <InfoCircle size={16} className="mr-2" />
            P3 Medium Priority
          </div>
          <div className="nw-chip nw-chip--healthy nw-focus-ring" tabIndex={0}>
            <SuccessCheck size={16} className="mr-2" />
            System Healthy
          </div>
        </div>
      </section>

      {/* Cards */}
      <section className="mb-8">
        <h2 className="nw-subtitle mb-4">Dashboard Cards</h2>
        <div className="grid md:grid-cols-2 gap-6">
          <div className="nw-card p-6">
            <h3 className="nw-heading text-lg mb-3">System Overview</h3>
            <p className="nw-body mb-4">
              Monitor your infrastructure with real-time insights and automated alerts.
            </p>
            <div className="flex gap-2">
              <button className="nw-btn--progressive nw-focus-ring">
                View Details
              </button>
              <button className="nw-btn--action nw-focus-ring">
                Configure
              </button>
            </div>
          </div>

          <div className="nw-card nw-card--critical p-6">
            <h3 className="nw-heading text-lg mb-3 flex items-center">
              <CriticalDiamond size={20} className="mr-2 text-red-600" />
              Critical Alert
            </h3>
            <p className="nw-body mb-4">
              Database connection pool exhausted. Immediate attention required.
            </p>
            <div className="flex gap-2">
              <button className="nw-btn--progressive nw-focus-ring">
                Investigate
              </button>
              <button className="nw-btn--action nw-focus-ring">
                Acknowledge
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Icons Showcase */}
      <section className="mb-8">
        <h2 className="nw-subtitle mb-4">NestWatch Icons</h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
          <div className="text-center">
            <div className="nw-pulse nw-pulse--critical mb-2">
              <CriticalDiamond size={32} className="mx-auto" />
            </div>
            <p className="nw-hint">Critical</p>
          </div>
          <div className="text-center">
            <div className="nw-pulse nw-pulse--warning mb-2">
              <WarningTriangle size={32} className="mx-auto" />
            </div>
            <p className="nw-hint">Warning</p>
          </div>
          <div className="text-center">
            <InfoCircle size={32} className="mx-auto mb-2 text-blue-600" />
            <p className="nw-hint">Info</p>
          </div>
          <div className="text-center">
            <div className="nw-pulse nw-pulse--healthy mb-2">
              <SuccessCheck size={32} className="mx-auto" />
            </div>
            <p className="nw-hint">Success</p>
          </div>
          <div className="text-center">
            <HawkGeo size={32} className="mx-auto mb-2 text-[var(--nw-lime)]" />
            <p className="nw-hint">Hawky AI</p>
          </div>
        </div>
      </section>

      {/* Typography */}
      <section className="mb-8">
        <h2 className="nw-subtitle mb-4">Typography System</h2>
        <div className="space-y-3">
          <h1 className="nw-heading text-3xl">Main Heading - Large</h1>
          <h2 className="nw-heading text-xl">Section Heading - Medium</h2>
          <h3 className="nw-subtitle">Subtitle - Emphasized</h3>
          <p className="nw-body">
            Body text provides clear, readable content for users. It maintains proper contrast 
            ratios and spacing for optimal accessibility across all devices.
          </p>
          <p className="nw-hint">
            Hint text offers additional context or metadata in a subtle, secondary style.
          </p>
        </div>
      </section>

      {/* Theme Toggle */}
      <section className="mb-8">
        <h2 className="nw-subtitle mb-4">Theme Controls</h2>
        <p className="nw-body mb-4">
          Current theme: <span className="font-semibold">{theme}</span>
        </p>
        <p className="nw-hint">
          Toggle between light and dark themes to see the adaptive color system in action.
        </p>
      </section>

      {/* Hawky FAB */}
      <HawkyFab 
        onClick={() => alert('Hawky AI Assistant activated!')} 
      />
    </div>
  );
};

export default NestWatchDemo;
