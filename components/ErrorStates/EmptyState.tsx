import React from 'react';

interface EmptyStateProps {
  title: string;
  message: string;
  icon?: string;
  showRefresh?: boolean;
  onRefresh?: () => void;
  showDiagnostics?: boolean;
  eventCount?: number;
}

const EmptyState: React.FC<EmptyStateProps> = ({ 
  title, 
  message, 
  icon = '📊',
  showRefresh = true,
  onRefresh,
  showDiagnostics = true,
  eventCount = 0
}) => {
  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 m-4 text-center">
      <div className="text-6xl mb-4">{icon}</div>
      
      <h3 className="text-xl font-semibold text-gray-900 mb-2">
        {title}
      </h3>
      
      <p className="text-gray-600 mb-6 max-w-md mx-auto">
        {message}
      </p>

      {showDiagnostics && (
        <div className="bg-white border border-gray-200 rounded p-4 mb-6 max-w-md mx-auto">
          <h4 className="font-medium text-gray-900 mb-2">System Status:</h4>
          <div className="text-sm text-gray-700 space-y-1">
            <div className="flex justify-between">
              <span>Events Loaded:</span>
              <span className={eventCount > 0 ? 'text-green-600' : 'text-red-600'}>
                {eventCount}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Data Source:</span>
              <span className="text-blue-600">Real API</span>
            </div>
            <div className="flex justify-between">
              <span>Fallback Data:</span>
              <span className="text-red-600">Disabled</span>
            </div>
            <div className="flex justify-between">
              <span>Last Check:</span>
              <span className="text-gray-500">{new Date().toLocaleTimeString()}</span>
            </div>
          </div>
        </div>
      )}

      {showRefresh && onRefresh && (
        <button
          onClick={onRefresh}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          🔄 Refresh Data
        </button>
      )}

      <div className="mt-4 text-xs text-gray-500">
        No fake data will be shown - only real SRE events
      </div>
    </div>
  );
};

export default EmptyState;
