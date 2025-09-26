import type { Meta, StoryObj } from '@storybook/react';
import { 
  CriticalDiamond, 
  CriticalDiamondOutline,
  WarningTriangle,
  WarningTriangleSolid,
  InfoCircle,
  InfoCircleSolid,
  SuccessCheck,
  SuccessCheckSolid,
  Filter,
  Refresh,
  HawkGeo
} from '../../ui/icons/nestwatch';

const meta: Meta = {
  title: 'NestWatch/Icons',
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
};

export default meta;

// Priority Icons
export const PriorityIcons: StoryObj = {
  render: () => (
    <div className="grid grid-cols-4 gap-8 p-8">
      <div className="text-center">
        <CriticalDiamond className="text-red-600 mx-auto mb-2" />
        <p className="text-sm">Critical Diamond</p>
      </div>
      <div className="text-center">
        <CriticalDiamondOutline className="text-red-600 mx-auto mb-2" />
        <p className="text-sm">Critical Outline</p>
      </div>
      <div className="text-center">
        <WarningTriangle className="text-orange-600 mx-auto mb-2" />
        <p className="text-sm">Warning Triangle</p>
      </div>
      <div className="text-center">
        <WarningTriangleSolid className="text-orange-600 mx-auto mb-2" />
        <p className="text-sm">Warning Solid</p>
      </div>
    </div>
  ),
};

export const StatusIcons: StoryObj = {
  render: () => (
    <div className="grid grid-cols-4 gap-8 p-8">
      <div className="text-center">
        <InfoCircle className="text-blue-600 mx-auto mb-2" />
        <p className="text-sm">Info Circle</p>
      </div>
      <div className="text-center">
        <InfoCircleSolid className="text-blue-600 mx-auto mb-2" />
        <p className="text-sm">Info Solid</p>
      </div>
      <div className="text-center">
        <SuccessCheck className="text-green-600 mx-auto mb-2" />
        <p className="text-sm">Success Check</p>
      </div>
      <div className="text-center">
        <SuccessCheckSolid className="text-green-600 mx-auto mb-2" />
        <p className="text-sm">Success Solid</p>
      </div>
    </div>
  ),
};

export const UtilityIcons: StoryObj = {
  render: () => (
    <div className="grid grid-cols-3 gap-8 p-8">
      <div className="text-center">
        <Filter className="text-gray-600 mx-auto mb-2" />
        <p className="text-sm">Filter</p>
      </div>
      <div className="text-center">
        <Refresh className="text-gray-600 mx-auto mb-2" />
        <p className="text-sm">Refresh</p>
      </div>
      <div className="text-center">
        <HawkGeo className="text-lime-600 mx-auto mb-2" />
        <p className="text-sm">Hawk Geo</p>
      </div>
    </div>
  ),
};

export const IconSizes: StoryObj = {
  render: () => (
    <div className="flex items-center gap-8 p-8">
      <CriticalDiamond size={16} className="text-red-600" />
      <CriticalDiamond size={24} className="text-red-600" />
      <CriticalDiamond size={32} className="text-red-600" />
      <CriticalDiamond size={48} className="text-red-600" />
    </div>
  ),
};
