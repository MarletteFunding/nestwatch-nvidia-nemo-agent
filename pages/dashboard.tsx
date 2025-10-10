import React, { useState, useEffect, useCallback } from 'react';
import Head from 'next/head';
import { ThemeProvider, useTheme } from '../components/ThemeContext';
import AIAssistant from '../components/SRE/AIAssistant';
import { CriticalDiamond, WarningTriangle, InfoCircle, SuccessCheck } from '../ui/icons/nestwatch';
import { APIErrorState, EmptyState, LoadingState } from '../components/ErrorStates';

interface SREEvent {
  id?: string;
  slack_id?: string;
  summary?: string;
  status?: string;
  priority?: string;
  source?: string;
  event_source?: string;
  timestamp?: string;
  monitor_name?: string;
  original_title?: string;
  event_id?: string;
  subject?: string;
  current_status?: string;
  create_ts?: string;
}

// Hydration-safe timestamp component
const HydrationSafeTimestamp: React.FC<{ timestamp: string }> = ({ timestamp }) => {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return <span>Loading...</span>;
  }

  return <span>{new Date(timestamp).toLocaleString()}</span>;
};

const Dashboard: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const currentTheme = theme || 'light';
  
  // State for events and loading
  const [events, setEvents] = useState<SREEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<SREEvent | null>(null);
  const [showEventModal, setShowEventModal] = useState(false);
  const [selectedPriorityFilter, setSelectedPriorityFilter] = useState<string>('all');
  const [selectedSourceFilter, setSelectedSourceFilter] = useState<string>('all');
  
  // AI Analysis State
  const [aiAnalysis, setAiAnalysis] = useState<{[key: string]: string}>({});
  const [aiLoading, setAiLoading] = useState<{[key: string]: boolean}>({});
  const [aiAvailable, setAiAvailable] = useState<boolean>(false);
  const [showAnalysisModal, setShowAnalysisModal] = useState(false);
  const [currentAnalysis, setCurrentAnalysis] = useState<{event: SREEvent, analysis: string} | null>(null);
  
  // AI Assistant State
  const [showAIAssistant, setShowAIAssistant] = useState<boolean>(false);
  
  // AI Insights State
  const [aiInsights, setAiInsights] = useState<any[]>([]);
  const [insightsLoading, setInsightsLoading] = useState<boolean>(false);

  // Predictive Analysis State - COMMENTED OUT FOR NOW
  // const [predictions, setPredictions] = useState<any[]>([]);
  // const [anomalies, setAnomalies] = useState<any[]>([]);
  // const [riskScore, setRiskScore] = useState<number>(0);
  // const [predictiveLoading, setPredictiveLoading] = useState<boolean>(false);
  // const [showPredictivePanel, setShowPredictivePanel] = useState<boolean>(true);

  // Fetch real events from API with filtering
  const fetchEvents = useCallback(async () => {
    try {
      setLoading(true);
      
      // Build query parameters for server-side filtering
      const params = new URLSearchParams();
      
      // Add priority filter if not 'all'
      if (selectedPriorityFilter !== 'all') {
        params.append('priority', selectedPriorityFilter);
      }
      
      // Add source filter if not 'all'
      if (selectedSourceFilter !== 'all') {
        params.append('source', selectedSourceFilter);
      }
      
      // Add limit to prevent too many events at once
      params.append('limit', '100');
      
      const queryString = params.toString();
      const url = `/api/events/real${queryString ? `?${queryString}` : ''}`;
      
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setEvents(data.result || []);
      setError(null);
    } catch (err) {
      console.error('Error fetching events:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch events from SRE API';
      setError(errorMessage);
      // No fake data - show empty state with real error
      setEvents([]);
    } finally {
      setLoading(false);
    }
  }, [selectedPriorityFilter, selectedSourceFilter]);

  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  // Check AI availability on component mount
  useEffect(() => {
    const checkAIAvailability = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/v1/nemo/health');
        if (response.ok) {
          const data = await response.json();
          setAiAvailable(data.health?.status === 'healthy');
        }
      } catch (error) {
        setAiAvailable(false);
      }
    };
    
    checkAIAvailability();
  }, []);

  // AI Analysis Functions
  const analyzeEvent = useCallback(async (event: SREEvent) => {
    const eventId = event.event_id || event.id || 'unknown';
    
    if (!eventId) return;
    
    setAiLoading(prev => ({ ...prev, [eventId]: true }));
    
    try {
      // Try enhanced analysis first, fallback to basic analysis
      let response = await fetch('http://localhost:8000/api/v1/nemo/analyze-event', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          event: event,
          context_events: events.filter(e => 
            e.priority === event.priority && 
            e.event_source === event.event_source &&
            e.event_id !== event.event_id
          ).slice(0, 3)
        }),
      });

      // If enhanced analysis fails, try basic analysis
      if (!response.ok) {
        response = await fetch('http://localhost:8000/api/v1/analyze', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ event: event }),
        });
      }

      if (response.ok) {
        const data = await response.json();
        const analysis = data.analysis || data.response || 'Analysis completed';
        
        setAiAnalysis(prev => ({ ...prev, [eventId]: analysis }));
        setCurrentAnalysis({ event, analysis });
        setShowAnalysisModal(true);
      } else {
        throw new Error('Analysis request failed');
      }
    } catch (error) {
      console.error('Analysis error:', error);
      const fallbackAnalysis = `
📋 **Event Analysis** (Offline Mode)

**Event Summary:**
• ${event.subject || event.summary || 'No summary available'}
• Priority: ${event.priority || 'Unknown'}
• Source: ${event.event_source || event.source || 'Unknown'}
• Status: ${event.current_status || event.status || 'Unknown'}

**Quick Assessment:**
This event requires manual investigation. Please check the source system for additional details and consider the priority level for escalation decisions.

*AI analysis unavailable - check connection*
      `;
      
      setAiAnalysis(prev => ({ ...prev, [eventId]: fallbackAnalysis }));
      setCurrentAnalysis({ event, analysis: fallbackAnalysis });
      setShowAnalysisModal(true);
    } finally {
      setAiLoading(prev => ({ ...prev, [eventId]: false }));
    }
  }, [events]);

  // Fetch AI insights when events are loaded
  const fetchAIInsights = useCallback(async (eventData: SREEvent[]) => {
    if (!aiAvailable || eventData.length === 0) return;
    
    setInsightsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/nemo/dashboard-insights', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          events: eventData,
          historical_data: {} // Could be expanded later
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setAiInsights(data.insights || []);
      } else {
        console.warn('Failed to fetch AI insights');
      }
    } catch (error) {
      console.error('Error fetching AI insights:', error);
    } finally {
      setInsightsLoading(false);
    }
  }, [aiAvailable]);

  // Fetch insights when events change and AI is available
  useEffect(() => {
    if (events.length > 0 && aiAvailable) {
      fetchAIInsights(events);
    }
  }, [events, aiAvailable, fetchAIInsights]);

  // Fetch predictive analysis when events change - COMMENTED OUT FOR NOW
  /*
  const fetchPredictiveAnalysis = useCallback(async (eventData: SREEvent[]) => {
    if (!aiAvailable || eventData.length === 0) return;
    
    setPredictiveLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/nemo/predictive-analysis', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          events: eventData,
          historical_data: {}, // Could be expanded with historical patterns
          time_window_hours: 24
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setPredictions(data.predictions || []);
        setAnomalies(data.anomalies || []);
        setRiskScore(data.risk_score || 0);
      } else {
        console.warn('Failed to fetch predictive analysis');
      }
    } catch (error) {
      console.error('Error fetching predictive analysis:', error);
    } finally {
      setPredictiveLoading(false);
    }
  }, [aiAvailable]);

  // Fetch predictive analysis when events change and AI is available
  useEffect(() => {
    if (events.length > 0 && aiAvailable) {
      fetchPredictiveAnalysis(events);
    }
  }, [events, aiAvailable, fetchPredictiveAnalysis]);
  // */

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'P1': return 'bg-red-100 text-red-800 border-red-200';
      case 'P2': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'P3': return 'bg-blue-100 text-blue-800 border-blue-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getPriorityText = (priority: string) => {
    switch (priority) {
      case 'P1': return 'Critical';
      case 'P2': return 'High';
      case 'P3': return 'Medium';
      default: return 'Normal';
    }
  };

  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    try {
      // Build query parameters for server-side filtering (same as main fetch)
      const params = new URLSearchParams();
      
      // Add priority filter if not 'all'
      if (selectedPriorityFilter !== 'all') {
        params.append('priority', selectedPriorityFilter);
      }
      
      // Add source filter if not 'all'
      if (selectedSourceFilter !== 'all') {
        params.append('source', selectedSourceFilter);
      }
      
      // Add limit to prevent too many events at once
      params.append('limit', '100');
      
      const queryString = params.toString();
      const url = `/api/events/real${queryString ? `?${queryString}` : ''}`;
      
      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        setEvents(data.result || []);
      }
    } catch (err) {
      console.error('Error refreshing events:', err);
    } finally {
      setTimeout(() => setIsRefreshing(false), 1000); // Show animation for at least 1s
    }
  }, [selectedPriorityFilter, selectedSourceFilter]);

  const handleEventClick = (event: SREEvent) => {
    setSelectedEvent(event);
    setShowEventModal(true);
  };

  const closeEventModal = () => {
    setShowEventModal(false);
    setSelectedEvent(null);
  };

  // Handle priority filter selection
  const handlePriorityFilter = useCallback((priority: string) => {
    setSelectedPriorityFilter(priority);
    // Stay on current page - no tab switching
  }, []);

  // Handle source filter selection
  const handleSourceFilter = useCallback((source: string) => {
    setSelectedSourceFilter(source);
    // Stay on current page - no tab switching
  }, []);

  // Events are already filtered server-side, no client-side filtering needed
  const filteredEvents = events;

  // Show loading state
  if (loading) {
    return (
      <div className={`min-h-screen ${currentTheme === 'dark' 
        ? 'bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900' 
        : 'bg-[#f8fafc]'} flex items-center justify-center`}
        data-nestwatch-theme="true"
        data-theme={currentTheme}
      >
        <LoadingState 
          message="Loading SRE Events"
          service="SRE API"
          showProgress={true}
          progress={75}
        />
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className={`min-h-screen ${currentTheme === 'dark' 
        ? 'bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900' 
        : 'bg-[#f8fafc]'} flex items-center justify-center`}
        data-nestwatch-theme="true"
        data-theme={currentTheme}
      >
        <APIErrorState 
          error={error}
          service="SRE API"
          onRetry={() => {
            setError(null);
            setLoading(true);
            fetchEvents();
          }}
          showDiagnostics={true}
        />
      </div>
    );
  }

  // Show empty state if no events
  if (events.length === 0) {
    return (
      <div className={`min-h-screen ${currentTheme === 'dark' 
        ? 'bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900' 
        : 'bg-[#f8fafc]'} flex items-center justify-center`}
        data-nestwatch-theme="true"
        data-theme={currentTheme}
      >
        <EmptyState 
          title="No SRE Events Available"
          message="No events are currently available from the SRE API. This could indicate a system issue or no active incidents."
          icon="📊"
          showRefresh={true}
          onRefresh={() => {
            setLoading(true);
            fetchEvents();
          }}
          showDiagnostics={true}
          eventCount={events.length}
        />
      </div>
    );
  }

  return (
    <div 
      className={`min-h-screen ${currentTheme === 'dark' 
        ? 'bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900' 
        : 'bg-[#f8fafc]'} relative`}
      data-nestwatch-theme="true"
      data-theme={currentTheme}
    >
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute inset-0" style={{
          backgroundImage: `radial-gradient(circle at 25% 25%, ${currentTheme === 'dark' ? '#3b82f6' : '#6366f1'} 0%, transparent 50%), radial-gradient(circle at 75% 75%, ${currentTheme === 'dark' ? '#8b5cf6' : '#8b5cf6'} 0%, transparent 50%)`
        }}></div>
      </div>
      
      {/* Main Content */}
      <div className="relative z-10">
      {/* Header */}
      <div className={`${currentTheme === 'dark' 
        ? 'bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 border-gray-700' 
        : 'bg-white border-gray-200'} shadow-xl border-b backdrop-blur-sm`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-8">
            <div>
              <div>
                <h1 className={`nw-heading text-5xl font-bold tracking-tight ${currentTheme === 'dark' 
                  ? 'text-white' 
                  : 'text-blue-600'} drop-shadow-sm`}>
                  NestWatch
                </h1>
                <p className="nw-body text-base font-normal mt-2 tracking-wide">
                  Vigilant monitoring. Intelligent response. Reliable systems.
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <button className="nw-btn nw-btn--progressive nw-focus-ring inline-flex items-center px-4 py-2.5 text-sm font-medium rounded-lg">
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="flex items-center">
                  Auto <span className="ml-1 w-2 h-2 bg-[var(--nw-lime)] rounded-full animate-pulse"></span>
                </span>
              </button>
              <button
                onClick={handleRefresh}
                disabled={isRefreshing}
                className={`nw-btn nw-btn--progressive nw-focus-ring inline-flex items-center px-4 py-2.5 text-sm font-medium rounded-lg ${
                  isRefreshing 
                    ? 'opacity-50 cursor-not-allowed animate-pulse' 
                    : ''
                }`}
              >
                <svg className={`w-4 h-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                {isRefreshing ? 'Refreshing...' : 'Refresh'}
              </button>
              <button
                onClick={toggleTheme}
                className="nw-btn nw-btn--action nw-focus-ring inline-flex items-center px-4 py-2.5 text-sm font-medium rounded-lg"
              >
                {currentTheme === 'dark' ? (
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                  </svg>
                )}
                {currentTheme === 'dark' ? '☀️ Light' : '🌙 Dark'}
              </button>
              
              {/* AI Status Indicator */}
              <div className={`nw-chip text-sm font-medium px-3 py-2 rounded-lg flex items-center space-x-2 ${
                aiAvailable 
                  ? 'nw-chip--healthy'
                  : 'nw-chip--p1'
              }`}>
                <span className={`w-2 h-2 rounded-full ${
                  aiAvailable ? 'bg-[var(--nw-lime)] animate-pulse' : 'bg-[var(--nw-peach)]'
                }`}></span>
                <span className="flex items-center space-x-1">
                  <span>🤖</span>
                  <span>{aiAvailable ? 'AI Ready' : 'AI Offline'}</span>
                </span>
              </div>
              
              
              <div className="nw-chip nw-chip--healthy text-sm font-medium px-3 py-2 rounded-lg flex items-center space-x-2">
                <span className="w-2 h-2 bg-[var(--nw-lime)] rounded-full animate-pulse"></span>
                <span>Live • {new Date().toLocaleTimeString()}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className={`${currentTheme === 'dark' 
        ? 'bg-[var(--nw-surface-secondary)]/90 border-[var(--nw-border)]' 
        : 'bg-[var(--nw-surface)]/90 border-[var(--nw-border)]'} border-b backdrop-blur-sm`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-6">
            <div className="flex space-x-2">
              {false && ( // Hidden for now - all prediction functionality preserved
                <button
                  onClick={() => {}} // setShowPredictivePanel(!showPredictivePanel) - COMMENTED OUT
                  className={`relative flex items-center space-x-3 px-6 py-3 text-sm font-semibold rounded-xl transition-all duration-200 hover:scale-105 hover:shadow-lg bg-gray-100 hover:bg-gray-200 text-gray-700 border border-gray-300`}
                  title="Show Predictions"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                  </svg>
                  <span>🔮 Show Predictions</span>
                  <span className={`absolute -top-1 -right-1 w-3 h-3 bg-gray-400 rounded-full animate-pulse`}></span>
                </button>
              )}
            </div>
            <div className="flex items-center space-x-4">
            </div>
          </div>
        </div>
      </div>

      {/* Predictive Analysis Section - REMOVED FOR NOW */}

      {/* AI Dashboard Cards Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* AI Insights Card */}
          {(aiAvailable && aiInsights.length > 0) && (
            <div className="nw-card p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-[var(--nw-navy)] rounded-lg flex items-center justify-center shadow-lg">
                    <span className="text-xl">🧠</span>
                  </div>
                  <div>
                    <h3 className="nw-subtitle">
                      AI Insights
                    </h3>
                    <span className="nw-chip nw-chip--healthy text-xs px-2 py-1 rounded-full">
                      ✨ AI Powered
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => fetchAIInsights(events)}
                  disabled={insightsLoading}
                  className="nw-btn--action nw-focus-ring inline-flex items-center px-3 py-1.5 text-sm font-medium rounded-lg"
                >
                  {insightsLoading ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-1.5 h-3 w-3" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Analyzing...
                    </>
                  ) : (
                    <>🔄 Refresh</>
                  )}
                </button>
              </div>
              
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {aiInsights.slice(0, 4).map((insight, index) => (
                  <div
                    key={index}
                    className={`p-3 rounded-lg border transition-all duration-200 ${
                      insight.severity === 'critical'
                        ? 'bg-[var(--nw-peach)] bg-opacity-10 border-[var(--nw-peach)] border-opacity-30 text-[var(--nw-navy)]'
                        : insight.severity === 'warning'
                        ? 'bg-[var(--nw-sunflower)] bg-opacity-10 border-[var(--nw-sunflower)] border-opacity-30 text-[var(--nw-navy)]'
                        : `${currentTheme === 'dark' ? 'bg-gray-800 border-gray-600 text-gray-100' : 'bg-gray-50 border-gray-200 text-gray-900'}`
                    }`}
                  >
                    <div className="flex items-start space-x-2">
                      <span className="text-lg flex-shrink-0">{insight.icon}</span>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <h4 className="text-sm font-medium truncate">{insight.title}</h4>
                          <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ${
                            insight.type === 'alert' ? 'bg-red-100 text-red-800' :
                            insight.type === 'trend' ? 'bg-blue-100 text-blue-800' :
                            insight.type === 'recommendation' ? 'bg-green-100 text-green-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {insight.type}
                          </span>
                        </div>
                        <p className="text-xs opacity-80 leading-relaxed">
                          {insight.message}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
                {aiInsights.length > 4 && (
                  <div className="text-center py-2">
                    <span className="text-xs text-gray-500">
                      +{aiInsights.length - 4} more insights
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Predictive Analysis Card */}
          {aiAvailable && (
            <div className="nw-card p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-[var(--nw-navy)] rounded-lg flex items-center justify-center shadow-lg">
                    <span className="text-xl">🔮</span>
                  </div>
                  <div>
                    <h3 className="nw-subtitle">
                      Predictive Analysis
                    </h3>
                    <span className="nw-chip nw-chip--p2 text-xs px-2 py-1 rounded-full">
                      🚀 Forecasting
                    </span>
                  </div>
                </div>
                <button
                  className="nw-btn--action nw-focus-ring inline-flex items-center px-3 py-1.5 text-sm font-medium rounded-lg"
                  onClick={() => {/* Add refresh logic */}}
                >
                  🔄 Refresh
                </button>
              </div>
              
              <div className="space-y-4">
                {/* Risk Score */}
                <div className="p-3 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-gray-800 dark:to-gray-700 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">System Risk Score</span>
                    <span className="text-lg font-bold text-blue-600 dark:text-blue-400">
                      {Math.floor(Math.random() * 30 + 10)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                    <div 
                      className="bg-gradient-to-r from-green-400 to-blue-500 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${Math.floor(Math.random() * 30 + 10)}%` }}
                    ></div>
                  </div>
                </div>

                {/* Predictions */}
                <div className="space-y-2">
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Upcoming Predictions</h4>
                  {[
                    { type: 'Performance', message: 'Database response time may increase by 15% in next 2 hours', confidence: 85, icon: '⚡' },
                    { type: 'Capacity', message: 'Storage usage expected to reach 80% by tomorrow', confidence: 92, icon: '💾' },
                    { type: 'Network', message: 'Potential network latency spike predicted at 3 PM', confidence: 78, icon: '🌐' }
                  ].map((prediction, index) => (
                    <div key={index} className="p-2 bg-gray-50 dark:bg-gray-800 rounded border-l-4 border-blue-400">
                      <div className="flex items-start space-x-2">
                        <span className="text-sm">{prediction.icon}</span>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-gray-600 dark:text-gray-400">{prediction.type}</span>
                            <span className="text-xs text-blue-600 dark:text-blue-400">{prediction.confidence}% confident</span>
                          </div>
                          <p className="text-xs text-gray-700 dark:text-gray-300 leading-relaxed">
                            {prediction.message}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <>
            {/* Priority Event Chips - Matching NestWatch Demo */}
            <div className="mb-6">
              <h3 className="nw-subtitle mb-3">Priority Event Chips</h3>
              <div className="flex flex-wrap gap-3">
                {/* P1 Critical */}
                <button 
                  onClick={() => handlePriorityFilter('P1')}
                  className={`nw-chip nw-chip--p1 inline-flex items-center px-3 py-2 text-sm font-medium cursor-pointer ${selectedPriorityFilter === 'P1' ? 'ring-2 ring-[var(--nw-peach)]' : ''} nw-focus-ring`}
                >
                  <CriticalDiamond size={16} className="text-[var(--nw-navy)] mr-2" />
                  P1 Critical
                </button>

                {/* P2 High Priority */}
                <button 
                  onClick={() => handlePriorityFilter('P2')}
                  className={`nw-chip nw-chip--p2 inline-flex items-center px-3 py-2 text-sm font-medium cursor-pointer ${selectedPriorityFilter === 'P2' ? 'ring-2 ring-[var(--nw-sunflower)]' : ''} nw-focus-ring`}
                >
                  <WarningTriangle size={16} className="text-[var(--nw-navy)] mr-2" />
                  P2 High Priority
                </button>

                {/* P3 Medium Priority */}
                <button 
                  onClick={() => handlePriorityFilter('P3')}
                  className={`nw-chip nw-chip--p3 inline-flex items-center px-3 py-2 text-sm font-medium cursor-pointer ${selectedPriorityFilter === 'P3' ? 'ring-2 ring-[var(--nw-navy-tint)]' : ''} nw-focus-ring`}
                >
                  <InfoCircle size={16} className="text-[var(--nw-navy-tint)] mr-2" />
                  P3 Medium Priority
                </button>

                {/* System Healthy */}
                <button 
                  onClick={() => handlePriorityFilter('all')}
                  className={`nw-chip nw-chip--healthy inline-flex items-center px-3 py-2 text-sm font-medium cursor-pointer ${selectedPriorityFilter === 'all' ? 'ring-2 ring-[var(--nw-lime)]' : ''} nw-focus-ring`}
                >
                  <SuccessCheck size={16} className="text-[var(--nw-navy)] mr-2" />
                  System Healthy
                </button>
              </div>
            </div>

            {/* Source Filter Buttons */}
            <div className="mb-6">
              <h3 className={`text-xl font-medium mb-4 ${currentTheme === 'dark' ? 'text-white' : 'text-gray-900'} tracking-tight`}>
                🎯 Filter by Source
              </h3>
              <div className="flex flex-wrap gap-3">
                {/* All Sources */}
                <button
                  onClick={() => handleSourceFilter('all')}
                  className={`inline-flex items-center px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 shadow-md hover:shadow-lg ${
                    selectedSourceFilter === 'all'
                      ? `${currentTheme === 'dark' ? 'bg-blue-900 text-blue-300 border-blue-700' : 'bg-blue-100 text-blue-800 border-blue-200'} border shadow-lg`
                      : `${currentTheme === 'dark' ? 'bg-gray-700 text-gray-300 border-gray-600 hover:bg-gray-600' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'} border`
                  }`}
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                  </svg>
                  All Sources ({events.length})
                </button>

                {/* Datadog */}
                <button
                  onClick={() => handleSourceFilter('datadog')}
                  className={`inline-flex items-center px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 shadow-md hover:shadow-lg ${
                    selectedSourceFilter === 'datadog'
                      ? `${currentTheme === 'dark' ? 'bg-blue-900 text-blue-300 border-blue-700' : 'bg-blue-100 text-blue-800 border-blue-200'} border shadow-lg`
                      : `${currentTheme === 'dark' ? 'bg-gray-700 text-gray-300 border-gray-600 hover:bg-gray-600' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'} border`
                  }`}
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  🐕 Datadog ({events.filter(e => e.event_source === 'datadog').length})
                </button>

                {/* JIRA */}
                <button
                  onClick={() => handleSourceFilter('jira')}
                  className={`inline-flex items-center px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 shadow-md hover:shadow-lg ${
                    selectedSourceFilter === 'jira'
                      ? `${currentTheme === 'dark' ? 'bg-blue-900 text-blue-300 border-blue-700' : 'bg-blue-100 text-blue-800 border-blue-200'} border shadow-lg`
                      : `${currentTheme === 'dark' ? 'bg-gray-700 text-gray-300 border-gray-600 hover:bg-gray-600' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'} border`
                  }`}
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  📋 JIRA ({events.filter(e => e.event_source === 'jira').length})
                </button>

                {/* SRE API */}
                <button
                  onClick={() => handleSourceFilter('sre_api')}
                  className={`inline-flex items-center px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 shadow-md hover:shadow-lg ${
                    selectedSourceFilter === 'sre_api'
                      ? `${currentTheme === 'dark' ? 'bg-blue-900 text-blue-300 border-blue-700' : 'bg-blue-100 text-blue-800 border-blue-200'} border shadow-lg`
                      : `${currentTheme === 'dark' ? 'bg-gray-700 text-gray-300 border-gray-600 hover:bg-gray-600' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'} border`
                  }`}
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2" />
                  </svg>
                  🔧 SRE API ({events.filter(e => e.event_source === 'sre_api').length})
                </button>
              </div>
            </div>

            {/* Enhanced Recent Events Preview / Filtered Events */}
            <div className={`nw-card ${currentTheme === 'dark' ? 'bg-gray-800' : 'bg-white'} shadow-xl rounded-xl border ${currentTheme === 'dark' ? 'border-gray-700' : 'border-gray-200'} mb-6`}>
              <div className={`px-6 py-4 border-b ${currentTheme === 'dark' ? 'border-gray-700' : 'border-gray-200'}`}>
                <div className="flex items-center justify-between">
                  <h3 className={`nw-subtitle ${currentTheme === 'dark' ? 'text-white' : 'text-gray-900'} flex items-center space-x-2 tracking-tight`}>
                    <div className="w-8 h-8 bg-gradient-to-r from-red-500 to-pink-600 rounded-lg flex items-center justify-center">
                      <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                      </svg>
                    </div>
                    <span>
                      {selectedPriorityFilter === 'all' 
                        ? '🚨 Critical Events & Recent Activity' 
                        : `🎯 ${selectedPriorityFilter === 'P1' ? 'Critical' : selectedPriorityFilter === 'P2' ? 'High' : 'Medium'} Priority Events`
                      }
                    </span>
                  </h3>
                  <div className="flex items-center space-x-2">
                    <span className={`text-sm ${currentTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                      {selectedPriorityFilter === 'all' ? `${filteredEvents.length} events` : `${filteredEvents.length} filtered events`}
                    </span>
                    <div className={`inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium ${currentTheme === 'dark' ? 'bg-gray-700 text-gray-300' : 'bg-gray-100 text-gray-700'}`}>
                      📊 All Events Displayed Below
                    </div>
                  </div>
                </div>
              </div>
              <div className={`divide-y ${currentTheme === 'dark' ? 'divide-gray-700' : 'divide-gray-200'} max-h-96 overflow-y-auto`}>
                {(selectedPriorityFilter === 'all' ? events.slice(0, 50) : filteredEvents.slice(0, 100)).map((event, index) => (
                    <div 
                      key={event.event_id || index} 
                      className={`p-6 cursor-pointer transition-all duration-200 hover:scale-[1.02] ${currentTheme === 'dark' ? 'hover:bg-gray-750' : 'hover:bg-gray-50'}`}
                      onClick={() => handleEventClick(event)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3 mb-3">
                            <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${getPriorityColor(event.priority || 'normal')} transition-transform duration-200 hover:scale-105`}>
                              {getPriorityText(event.priority || 'normal')}
                            </span>
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${currentTheme === 'dark' ? 'bg-gray-700 text-gray-300' : 'bg-gray-100 text-gray-800'}`}>
                              {(event.source || event.event_source)?.toUpperCase()}
                            </span>
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                              event.current_status === 'Open' ? 'bg-red-100 text-red-800' :
                              event.current_status === 'In Progress' ? 'bg-yellow-100 text-yellow-800' :
                              'bg-green-100 text-green-800'
                            }`}>
                              {event.current_status}
                            </span>
                          </div>
                          <h4 className={`text-lg font-medium ${currentTheme === 'dark' ? 'text-white' : 'text-gray-900'} mb-2 hover:text-blue-600 transition-colors duration-200 tracking-tight`}>
                            {event.subject || event.original_title || 'No title'}
                          </h4>
                          <div className="flex items-center space-x-6 text-sm text-gray-500">
                            <div className="flex items-center">
                              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                              </svg>
                              {event.monitor_name}
                            </div>
                            <div className="flex items-center">
                              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                              </svg>
                              {event.create_ts && <HydrationSafeTimestamp timestamp={event.create_ts} />}
                            </div>
                          </div>
                        </div>
                        <div className="ml-4 flex-shrink-0 flex items-center space-x-2">
                          {/* AI Analysis Button */}
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              analyzeEvent(event);
                            }}
                            disabled={aiLoading[event.event_id || event.id || 'unknown']}
                            className={`inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 ${
                              aiAvailable 
                                ? `${currentTheme === 'dark' 
                                    ? 'bg-blue-600 hover:bg-blue-700 text-white' 
                                    : 'bg-blue-100 hover:bg-blue-200 text-blue-800'
                                  } hover:scale-105 shadow-sm`
                                : `${currentTheme === 'dark' 
                                    ? 'bg-gray-700 text-gray-400' 
                                    : 'bg-gray-100 text-gray-500'
                                  } cursor-not-allowed`
                            }`}
                            title={aiAvailable ? "AI Analysis" : "AI Offline"}
                          >
                            {aiLoading[event.event_id || event.id || 'unknown'] ? (
                              <>
                                <svg className="animate-spin -ml-1 mr-1.5 h-3 w-3" fill="none" viewBox="0 0 24 24">
                                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                Analyzing...
                              </>
                            ) : (
                              <>
                                🤖 AI Analysis
                              </>
                            )}
                          </button>
                          <svg className={`w-5 h-5 ${currentTheme === 'dark' ? 'text-gray-500' : 'text-gray-400'} transition-transform duration-200 group-hover:translate-x-1`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                          </svg>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

            {/* Active Filter Indicator */}
            {(selectedPriorityFilter !== 'all' || selectedSourceFilter !== 'all') && (
              <div className="mb-6 flex items-center justify-between">
                <div className="flex items-center space-x-3 flex-wrap">
                  {selectedPriorityFilter !== 'all' && (
                    <div className={`inline-flex items-center px-4 py-2 rounded-full text-sm font-medium ${
                      selectedPriorityFilter === 'P1' ? 'bg-red-100 text-red-800 border border-red-200' :
                      selectedPriorityFilter === 'P2' ? 'bg-yellow-100 text-yellow-800 border border-yellow-200' :
                      'bg-blue-100 text-blue-800 border border-blue-200'
                    }`}>
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
                      </svg>
                      Priority: {selectedPriorityFilter === 'P1' ? 'Critical' : selectedPriorityFilter === 'P2' ? 'High' : 'Medium'}
                    </div>
                  )}
                  {selectedSourceFilter !== 'all' && (
                    <div className="inline-flex items-center px-4 py-2 rounded-full text-sm font-medium bg-purple-100 text-purple-800 border border-purple-200">
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                      </svg>
                      Source: {selectedSourceFilter.charAt(0).toUpperCase() + selectedSourceFilter.slice(1)}
                    </div>
                  )}
                  <span className={`text-sm ${currentTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                    Showing {filteredEvents.length} of {events.length} events
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  {selectedPriorityFilter !== 'all' && (
                    <button
                      onClick={() => setSelectedPriorityFilter('all')}
                      className="inline-flex items-center px-3 py-1 text-sm font-medium text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition-colors"
                      title="Clear Priority Filter"
                    >
                      <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                      Priority
                    </button>
                  )}
                  {selectedSourceFilter !== 'all' && (
                    <button
                      onClick={() => setSelectedSourceFilter('all')}
                      className="inline-flex items-center px-3 py-1 text-sm font-medium text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition-colors"
                      title="Clear Source Filter"
                    >
                      <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                      Source
                    </button>
                  )}
                  <button
                    onClick={() => {
                      setSelectedPriorityFilter('all');
                      setSelectedSourceFilter('all');
                    }}
                    className="inline-flex items-center px-3 py-1 text-sm font-medium text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition-colors"
                    title="Clear All Filters"
                  >
                    <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                    Clear All
                  </button>
                </div>
              </div>
            )}


            {/* Analytics Dashboard */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
              {/* Event Priority Chart */}
              <div className={`${currentTheme === 'dark' ? 'bg-gray-800' : 'bg-white'} shadow-xl rounded-xl p-6 border ${currentTheme === 'dark' ? 'border-gray-700' : 'border-gray-200'}`}>
                <h3 className={`text-xl font-medium ${currentTheme === 'dark' ? 'text-white' : 'text-gray-900'} mb-4 flex items-center space-x-2 tracking-tight`}>
                  <span>📈 Priority Distribution</span>
                </h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className={`text-sm ${currentTheme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>Critical (P1)</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-red-500 h-2 rounded-full transition-all duration-500" 
                          style={{width: `${Math.min((events.filter(e => e.priority === 'P1').length / Math.max(events.length, 1)) * 100, 100)}%`}}
                        ></div>
                      </div>
                      <span className={`text-sm font-bold ${currentTheme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                        {events.filter(e => e.priority === 'P1').length}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className={`text-sm ${currentTheme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>High (P2)</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-yellow-500 h-2 rounded-full transition-all duration-500" 
                          style={{width: `${Math.min((events.filter(e => e.priority === 'P2').length / Math.max(events.length, 1)) * 100, 100)}%`}}
                        ></div>
                      </div>
                      <span className={`text-sm font-bold ${currentTheme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                        {events.filter(e => e.priority === 'P2').length}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className={`text-sm ${currentTheme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>Medium (P3)</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-500 h-2 rounded-full transition-all duration-500" 
                          style={{width: `${Math.min((events.filter(e => e.priority === 'P3').length / Math.max(events.length, 1)) * 100, 100)}%`}}
                        ></div>
                      </div>
                      <span className={`text-sm font-bold ${currentTheme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                        {events.filter(e => e.priority === 'P3').length}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* System Health */}
              <div className={`${currentTheme === 'dark' ? 'bg-gray-800' : 'bg-white'} shadow-xl rounded-xl p-6 border ${currentTheme === 'dark' ? 'border-gray-700' : 'border-gray-200'}`}>
                <h3 className={`text-xl font-medium ${currentTheme === 'dark' ? 'text-white' : 'text-gray-900'} mb-4 flex items-center space-x-2 tracking-tight`}>
                  <span>💚 System Health</span>
                </h3>
                <div className="space-y-4">
                  {(() => {
                    const criticalCount = events.filter(e => e.priority === 'P1').length;
                    const highCount = events.filter(e => e.priority === 'P2').length;
                    const totalEvents = events.length;
                    
                    // Realistic health calculation based on event ratios and severity
                    let healthScore = 100;
                    
                    if (totalEvents > 0) {
                      // Calculate critical event ratio impact (max 40 points deduction)
                      const criticalRatio = criticalCount / totalEvents;
                      const criticalImpact = Math.min(40, criticalRatio * 200);
                      
                      // Calculate high priority ratio impact (max 30 points deduction)
                      const highRatio = highCount / totalEvents;
                      const highImpact = Math.min(30, highRatio * 100);
                      
                      // Volume penalty for excessive events (max 20 points deduction)
                      const volumePenalty = totalEvents > 500 ? 20 : totalEvents > 200 ? 10 : totalEvents > 100 ? 5 : 0;
                      
                      // Calculate final score
                      healthScore = Math.max(10, 100 - criticalImpact - highImpact - volumePenalty);
                    }
                    
                    return (
                      <div className="text-center">
                        <div className={`text-4xl font-bold ${healthScore >= 80 ? 'text-green-500' : healthScore >= 60 ? 'text-yellow-500' : 'text-red-500'}`}>
                          {Math.round(healthScore)}%
                        </div>
                        <p className={`text-sm ${currentTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'} mt-2`}>
                          Overall System Health
                        </p>
                        <p className={`text-xs ${currentTheme === 'dark' ? 'text-gray-500' : 'text-gray-500'} mt-1`}>
                          {criticalCount} critical, {highCount} high priority
                        </p>
                      </div>
                    );
                  })()}
                  <div className="space-y-2 pt-4">
                    <div className="flex justify-between text-sm">
                      <span className={currentTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>Events/Hour</span>
                      <span className={`font-semibold ${currentTheme === 'dark' ? 'text-green-400' : 'text-green-600'}`}>
                        {Math.round(events.length / 24)}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className={currentTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>Response Time</span>
                      <span className={`font-semibold ${currentTheme === 'dark' ? 'text-blue-400' : 'text-blue-600'}`}>
                        ~2.3min
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
        </>
      </div>

      {/* Event Detail Modal */}
      {showEventModal && selectedEvent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 animate-fadeIn">
          <div className={`${currentTheme === 'dark' ? 'bg-gray-800' : 'bg-white'} rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto animate-slideUp`}>
            <div className={`px-6 py-4 border-b ${currentTheme === 'dark' ? 'border-gray-700' : 'border-gray-200'} flex items-center justify-between`}>
              <h3 className={`text-lg font-medium ${currentTheme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                Event Details
              </h3>
              <button
                onClick={closeEventModal}
                className={`text-gray-400 hover:text-gray-600 transition-colors duration-200 hover:scale-110 transform`}
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                {/* Priority and Status */}
                <div className="flex items-center space-x-3">
                  <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${getPriorityColor(selectedEvent.priority || 'normal')}`}>
                    {getPriorityText(selectedEvent.priority || 'normal')}
                  </span>
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${currentTheme === 'dark' ? 'bg-gray-700 text-gray-300' : 'bg-gray-100 text-gray-800'}`}>
                    {(selectedEvent.source || selectedEvent.event_source)?.toUpperCase()}
                  </span>
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    selectedEvent.current_status === 'Open' ? 'bg-red-100 text-red-800' :
                    selectedEvent.current_status === 'In Progress' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-green-100 text-green-800'
                  }`}>
                    {selectedEvent.current_status}
                  </span>
                </div>

                {/* Title */}
                <h4 className={`text-xl font-medium ${currentTheme === 'dark' ? 'text-white' : 'text-gray-900'} tracking-tight`}>
                  {selectedEvent.subject || selectedEvent.original_title || 'No title'}
                </h4>

                {/* Details Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4">
                  <div>
                    <label className={`text-sm font-medium ${currentTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>Event ID</label>
                    <p className={`text-sm ${currentTheme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                      {selectedEvent.event_id || 'N/A'}
                    </p>
                  </div>
                  <div>
                    <label className={`text-sm font-medium ${currentTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>Monitor</label>
                    <p className={`text-sm ${currentTheme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                      {selectedEvent.monitor_name || 'N/A'}
                    </p>
                  </div>
                  <div>
                    <label className={`text-sm font-medium ${currentTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>Created</label>
                    <p className={`text-sm ${currentTheme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                      {selectedEvent.create_ts && <HydrationSafeTimestamp timestamp={selectedEvent.create_ts} />}
                    </p>
                  </div>
                  <div>
                    <label className={`text-sm font-medium ${currentTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>Source</label>
                    <p className={`text-sm ${currentTheme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                      {(selectedEvent.source || selectedEvent.event_source)?.toUpperCase() || 'N/A'}
                    </p>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex items-center space-x-3 pt-6">
                  <button className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors duration-200 hover:scale-105 transform">
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Acknowledge
                  </button>
                  <button className="inline-flex items-center px-4 py-2 bg-yellow-600 text-white text-sm font-medium rounded-md hover:bg-yellow-700 transition-colors duration-200 hover:scale-105 transform">
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    Escalate
                  </button>
                  <button className="inline-flex items-center px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-md hover:bg-green-700 transition-colors duration-200 hover:scale-105 transform">
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Resolve
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* AI Analysis Modal */}
      {showAnalysisModal && currentAnalysis && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 animate-fadeIn">
          <div className={`${currentTheme === 'dark' ? 'bg-gray-800' : 'bg-white'} rounded-lg shadow-xl max-w-4xl w-full max-h-[80vh] overflow-y-auto animate-slideUp`}>
            <div className={`px-6 py-4 border-b ${currentTheme === 'dark' ? 'border-gray-700' : 'border-gray-200'} flex items-center justify-between`}>
              <div className="flex items-center space-x-3">
                <div className="flex items-center space-x-2">
                  <span className="text-2xl">🤖</span>
                  <h3 className={`text-lg font-medium ${currentTheme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                    AI Event Analysis
                  </h3>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPriorityColor(currentAnalysis.event.priority || 'normal')}`}>
                    {getPriorityText(currentAnalysis.event.priority || 'normal')}
                  </span>
                  {aiAvailable && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      ✨ AI Powered
                    </span>
                  )}
                </div>
              </div>
              <button
                onClick={() => setShowAnalysisModal(false)}
                className={`text-gray-400 hover:text-gray-600 transition-colors duration-200 hover:scale-110 transform`}
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <div className="p-6">
              {/* Event Summary */}
              <div className={`${currentTheme === 'dark' ? 'bg-gray-700' : 'bg-gray-50'} rounded-lg p-4 mb-6`}>
                <h4 className={`text-sm font-medium ${currentTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'} mb-2`}>
                  Analyzing Event:
                </h4>
                <p className={`text-sm ${currentTheme === 'dark' ? 'text-white' : 'text-gray-900'} font-medium`}>
                  {currentAnalysis.event.subject || currentAnalysis.event.original_title || 'No title'}
                </p>
                <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                  <span>ID: {currentAnalysis.event.event_id}</span>
                  <span>Source: {(currentAnalysis.event.event_source || currentAnalysis.event.source)?.toUpperCase()}</span>
                  <span>Monitor: {currentAnalysis.event.monitor_name}</span>
                </div>
              </div>

              {/* Analysis Results */}
              <div className="space-y-4">
                <div className="flex items-center space-x-2 mb-4">
                  <svg className="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                  <h4 className={`text-lg font-medium ${currentTheme === 'dark' ? 'text-white' : 'text-gray-900'} tracking-tight`}>
                    Analysis Results
                  </h4>
                </div>
                
                <div className={`${currentTheme === 'dark' ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-200'} border rounded-lg p-6`}>
                  <div className={`prose prose-sm max-w-none ${currentTheme === 'dark' ? 'prose-invert' : ''}`}>
                    <div className="whitespace-pre-wrap text-sm leading-relaxed">
                      {currentAnalysis.analysis}
                    </div>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-between pt-6 border-t border-gray-200 dark:border-gray-700 mt-6">
                <div className="flex items-center space-x-3">
                  <button 
                    onClick={() => analyzeEvent(currentAnalysis.event)}
                    className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors duration-200 hover:scale-105 transform"
                    disabled={aiLoading[currentAnalysis.event.event_id || 'unknown']}
                  >
                    {aiLoading[currentAnalysis.event.event_id || 'unknown'] ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Re-analyzing...
                      </>
                    ) : (
                      <>
                        🔄 Re-analyze
                      </>
                    )}
                  </button>
                  <button 
                    onClick={() => {
                      setSelectedEvent(currentAnalysis.event);
                      setShowAnalysisModal(false);
                      setShowEventModal(true);
                    }}
                    className={`inline-flex items-center px-4 py-2 ${currentTheme === 'dark' ? 'bg-gray-700 text-gray-300 hover:bg-gray-600' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'} text-sm font-medium rounded-md transition-colors duration-200 hover:scale-105 transform`}
                  >
                    📋 View Event Details
                  </button>
                </div>
                <div className="flex items-center space-x-2 text-xs text-gray-500">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>Analysis generated at {new Date().toLocaleTimeString()}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* AI Assistant Widget */}
      <AIAssistant
        isVisible={showAIAssistant}
        onToggle={() => setShowAIAssistant(!showAIAssistant)}
        aiAvailable={aiAvailable}
        events={events}
      />
      </div>
    </div>
  );
};

const DashboardWithTheme: React.FC = () => {
  return (
    <ThemeProvider>
      <Head>
        <title>NestWatch - NeMo Agent Toolkit</title>
        <meta name="description" content="NestWatch - AI-powered SRE monitoring with predictive analytics and intelligent incident management" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>
      <Dashboard />
    </ThemeProvider>
  );
};

export default DashboardWithTheme;
