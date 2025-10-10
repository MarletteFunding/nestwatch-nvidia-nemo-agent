import React from 'react';

interface APIErrorStateProps {
  error: string;
  service: 'SRE API' | 'AI Service' | 'Backend';
  onRetry?: () => void;
  showDiagnostics?: boolean;
}

const APIErrorState: React.FC<APIErrorStateProps> = ({ 
  error, 
  service, 
  onRetry, 
  showDiagnostics = true 
}) => {
  const getServiceIcon = () => {
    switch (service) {
      case 'SRE API': return '🔧';
      case 'AI Service': return '🤖';
      case 'Backend': return '⚙️';
      default: return '❌';
    }
  };

  const getServiceColor = () => {
    switch (service) {
      case 'SRE API': return 'text-orange-600';
      case 'AI Service': return 'text-purple-600';
      case 'Backend': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-6 m-4">
      <div className="flex items-center mb-4">
        <span className="text-2xl mr-3">{getServiceIcon()}</span>
        <div>
          <h3 className={`text-lg font-semibold ${getServiceColor()}`}>
            {service} Unavailable
          </h3>
          <p className="text-sm text-gray-600">
            {service} connection failed - no fake data will be shown
          </p>
        </div>
      </div>

      <div className="bg-white border border-red-100 rounded p-4 mb-4">
        <h4 className="font-medium text-gray-900 mb-2">Error Details:</h4>
        <code className="text-sm text-red-700 bg-red-50 px-2 py-1 rounded">
          {error}
        </code>
      </div>

      {showDiagnostics && (
        <div className="bg-gray-50 border border-gray-200 rounded p-4 mb-4">
          <h4 className="font-medium text-gray-900 mb-2">Diagnostic Information:</h4>
          <ul className="text-sm text-gray-700 space-y-1">
            <li>• Service: {service}</li>
            <li>• Status: Connection Failed</li>
            <li>• Data Source: Real API (no fallbacks)</li>
            <li>• Error Time: {new Date().toLocaleTimeString()}</li>
          </ul>
        </div>
      )}

      <div className="bg-blue-50 border border-blue-200 rounded p-4">
        <h4 className="font-medium text-blue-900 mb-2">Troubleshooting Steps:</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Check if {service} is running</li>
          <li>• Verify network connectivity</li>
          <li>• Check console logs for detailed errors</li>
          <li>• Ensure proper authentication/credentials</li>
          {onRetry && <li>• Try the retry button below</li>}
        </ul>
      </div>

      {onRetry && (
        <div className="mt-4 flex justify-center">
          <button
            onClick={onRetry}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            🔄 Retry Connection
          </button>
        </div>
      )}
    </div>
  );
};

export default APIErrorState;
