import type { Meta, StoryObj } from '@storybook/react';
import { CriticalDiamond, WarningTriangle, InfoCircle, SuccessCheck } from '../../ui/icons/nestwatch';

const meta: Meta = {
  title: 'NestWatch/Components',
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
};

export default meta;

export const PriorityChips: StoryObj = {
  render: () => (
    <div className="flex gap-4 p-8" data-nestwatch-theme="true">
      <div className="nw-chip nw-chip--p1 nw-focus-ring">
        <CriticalDiamond size={16} className="mr-2" />
        P1 Critical
      </div>
      <div className="nw-chip nw-chip--p2 nw-focus-ring">
        <WarningTriangle size={16} className="mr-2" />
        P2 High
      </div>
      <div className="nw-chip nw-chip--p3 nw-focus-ring">
        <InfoCircle size={16} className="mr-2" />
        P3 Medium
      </div>
      <div className="nw-chip nw-chip--healthy nw-focus-ring">
        <SuccessCheck size={16} className="mr-2" />
        Healthy
      </div>
    </div>
  ),
};

export const Cards: StoryObj = {
  render: () => (
    <div className="grid grid-cols-2 gap-6 p-8" data-nestwatch-theme="true">
      <div className="nw-card p-6">
        <h3 className="nw-heading mb-2">Regular Card</h3>
        <p className="nw-body">This is a standard NestWatch card with rounded corners and shadow.</p>
      </div>
      <div className="nw-card nw-card--critical p-6">
        <h3 className="nw-heading mb-2">Critical Card</h3>
        <p className="nw-body">This card has a critical accent bar on the left side.</p>
      </div>
    </div>
  ),
};

export const Buttons: StoryObj = {
  render: () => (
    <div className="flex gap-4 p-8" data-nestwatch-theme="true">
      <button className="nw-btn--progressive nw-focus-ring">
        Progressive Action
      </button>
      <button className="nw-btn--action nw-focus-ring">
        Secondary Action
      </button>
    </div>
  ),
};

export const Typography: StoryObj = {
  render: () => (
    <div className="p-8 max-w-lg" data-nestwatch-theme="true">
      <h1 className="nw-heading mb-4">Heading Style</h1>
      <h2 className="nw-subtitle mb-3">Subtitle Style</h2>
      <p className="nw-body mb-3">
        This is body text that demonstrates the NestWatch typography system. 
        It uses consistent spacing and readable font sizes.
      </p>
      <p className="nw-hint">This is hint text for additional context or metadata.</p>
    </div>
  ),
};

export const Animations: StoryObj = {
  render: () => (
    <div className="flex gap-8 p-8" data-nestwatch-theme="true">
      <div className="nw-pulse nw-pulse--critical">
        <CriticalDiamond size={32} />
      </div>
      <div className="nw-pulse nw-pulse--warning">
        <WarningTriangle size={32} />
      </div>
      <div className="nw-pulse nw-pulse--healthy">
        <SuccessCheck size={32} />
      </div>
    </div>
  ),
};

export const DarkTheme: StoryObj = {
  render: () => (
    <div className="p-8 min-h-64" data-nestwatch-theme="true" data-theme="dark">
      <div className="nw-card p-6 mb-4">
        <h3 className="nw-heading mb-2">Dark Theme Card</h3>
        <p className="nw-body mb-4">This demonstrates the dark theme variant.</p>
        <div className="flex gap-2">
          <div className="nw-chip nw-chip--p1">Critical</div>
          <div className="nw-chip nw-chip--p2">Warning</div>
          <div className="nw-chip nw-chip--healthy">Healthy</div>
        </div>
      </div>
      <div className="flex gap-4">
        <button className="nw-btn--progressive nw-focus-ring">
          Progressive
        </button>
        <button className="nw-btn--action nw-focus-ring">
          Action
        </button>
      </div>
    </div>
  ),
};
