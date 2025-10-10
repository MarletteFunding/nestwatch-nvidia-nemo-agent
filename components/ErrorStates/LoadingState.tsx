import React from 'react';

interface LoadingStateProps {
  message?: string;
  showProgress?: boolean;
  progress?: number;
  service?: string;
}

const LoadingState: React.FC<LoadingStateProps> = ({ 
  message = "Loading events...",
  showProgress = false,
  progress = 0,
  service = "SRE API"
}) => {
  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 m-4">
      <div className="flex items-center justify-center mb-4">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mr-3"></div>
        <div>
          <h3 className="text-lg font-semibold text-blue-900">
            {message}
          </h3>
          <p className="text-sm text-blue-700">
            Fetching real data from {service}...
          </p>
        </div>
      </div>

      {showProgress && (
        <div className="mb-4">
          <div className="flex justify-between text-sm text-blue-700 mb-1">
            <span>Progress</span>
            <span>{progress}%</span>
          </div>
          <div className="w-full bg-blue-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
        </div>
      )}

      <div className="bg-white border border-blue-100 rounded p-4">
        <h4 className="font-medium text-blue-900 mb-2">What's happening:</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Connecting to {service}</li>
          <li>• Fetching real SRE events</li>
          <li>• Processing event data</li>
          <li>• No fake data will be shown</li>
        </ul>
      </div>

      <div className="mt-4 text-xs text-blue-600 text-center">
        This may take a few moments for large datasets
      </div>
    </div>
  );
};

export default LoadingState;
