import type { Meta, StoryObj } from '@storybook/react';
import { HawkyFab } from '../../ui/fab/HawkyFab';

const meta: Meta<typeof HawkyFab> = {
  title: 'NestWatch/HawkyFab',
  component: HawkyFab,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    onClick: { action: 'clicked' },
    disabled: {
      control: 'boolean',
    },
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {},
};

export const Disabled: Story = {
  args: {
    disabled: true,
  },
};

export const WithCustomClass: Story = {
  args: {
    className: 'opacity-75',
  },
};

// Show FAB in context
export const InContext: Story = {
  render: (args: any) => (
    <div className="relative w-96 h-64 bg-gray-100 rounded-lg">
      <p className="p-4 text-gray-600">This shows the FAB positioned as it would appear on a page.</p>
      <HawkyFab {...args} />
    </div>
  ),
  args: {},
};
