import { useState, useEffect } from 'react';
import api from '../../api';

const AnalyticsDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedTimePeriod, setSelectedTimePeriod] = useState(30); // days

  useEffect(() => {
    fetchAnalyticsData();
  }, [selectedTimePeriod]);

  const fetchAnalyticsData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Fetch comprehensive analytics insights with selected time period
      const response = await api.get(`/analytics/insights?days=${selectedTimePeriod}`);
      setDashboardData(response.data);
    } catch (err) {
      console.error('Analytics fetch error:', err);
      
      if (err.response?.status === 400 && err.response?.data?.error === 'insufficient_data') {
        setError({
          type: 'insufficient_data',
          message: err.response.data.message,
          suggestions: err.response.data.suggestions || []
        });
      } else {
        setError({
          type: 'api_error',
          message: 'Failed to load analytics data. Please try again.',
          details: err.response?.data?.message || err.message
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const renderLoadingState = () => (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-6xl mx-auto">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold text-gray-700">Analyzing Your Data...</h2>
          <p className="text-gray-500 mt-2">This may take a few moments</p>
        </div>
      </div>
    </div>
  );

  const renderErrorState = () => (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-xl shadow-lg p-8 text-center">
          {error.type === 'insufficient_data' ? (
            <>
              <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-gray-800 mb-4">More Data Needed</h2>
              <p className="text-gray-600 mb-6">{error.message}</p>
              
              <div className="bg-blue-50 rounded-lg p-6 mb-6">
                <h3 className="font-semibold text-blue-800 mb-3">To get started with analytics:</h3>
                <ul className="text-left text-blue-700 space-y-2">
                  {error.suggestions.map((suggestion, index) => (
                    <li key={index} className="flex items-start">
                      <span className="text-blue-500 mr-2">•</span>
                      {suggestion}
                    </li>
                  ))}
                </ul>
              </div>
              
              <button
                onClick={fetchAnalyticsData}
                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Check Again
              </button>
            </>
          ) : (
            <>
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-gray-800 mb-4">Unable to Load Analytics</h2>
              <p className="text-gray-600 mb-6">{error.message}</p>
              
              <button
                onClick={fetchAnalyticsData}
                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Try Again
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );

  const renderDataQualityIndicator = () => {
    if (!dashboardData?.summary?.data_quality_score) return null;
    
    const score = dashboardData.summary.data_quality_score;
    const percentage = Math.round(score * 100);
    
    let colorClass = 'text-red-600 bg-red-100';
    if (score >= 0.7) colorClass = 'text-green-600 bg-green-100';
    else if (score >= 0.4) colorClass = 'text-yellow-600 bg-yellow-100';
    
    return (
      <div className="bg-white rounded-xl shadow p-6 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-800">Data Quality</h3>
            <p className="text-gray-600 text-sm">Based on completeness and consistency</p>
          </div>
          <div className={`px-4 py-2 rounded-full ${colorClass} font-semibold`}>
            {percentage}%
          </div>
        </div>
      </div>
    );
  };

  const renderTimePeriodSelector = () => (
    <div className="bg-white rounded-xl shadow p-4 mb-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-800">Analysis Time Period</h3>
        <div className="flex space-x-2">
          {[
            { days: 7, label: '1 Week' },
            { days: 30, label: '1 Month' },
            { days: 90, label: '3 Months' }
          ].map(period => (
            <button
              key={period.days}
              onClick={() => setSelectedTimePeriod(period.days)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                selectedTimePeriod === period.days
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {period.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );

  const renderTabNavigation = () => (
    <div className="bg-white rounded-xl shadow mb-6">
      <div className="flex border-b">
        {[
          { id: 'overview', label: 'Overview', icon: '📊' },
          { id: 'trends', label: 'Trends', icon: '📈' },
          { id: 'predictions', label: 'Predictions', icon: '🔮' },
          { id: 'insights', label: 'Insights', icon: '💡' }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 px-6 py-4 text-center font-medium transition-colors ${
              activeTab === tab.id
                ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
            }`}
          >
            <span className="mr-2">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>
    </div>
  );

  const renderOverviewTab = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
      <div className="bg-white rounded-xl shadow p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-gray-600 text-sm">Weight Trends</p>
            <p className="text-2xl font-bold text-gray-800">
              {dashboardData.summary.has_weight_trends ? '✓' : '⏳'}
            </p>
          </div>
          <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
            <span className="text-2xl">⚖️</span>
          </div>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          {dashboardData.summary.has_weight_trends ? 'Available' : 'Need more data'}
        </p>
      </div>

      <div className="bg-white rounded-xl shadow p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-gray-600 text-sm">Nutrition Analysis</p>
            <p className="text-2xl font-bold text-gray-800">
              {dashboardData.summary.has_macro_trends ? '✓' : '⏳'}
            </p>
          </div>
          <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
            <span className="text-2xl">🥗</span>
          </div>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          {dashboardData.summary.has_macro_trends ? 'Available' : 'Need more data'}
        </p>
      </div>

      <div className="bg-white rounded-xl shadow p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-gray-600 text-sm">Performance Predictions</p>
            <p className="text-2xl font-bold text-gray-800">
              {dashboardData.summary.has_predictions ? '✓' : '⏳'}
            </p>
          </div>
          <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
            <span className="text-2xl">🎯</span>
          </div>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          {dashboardData.summary.has_predictions ? 'Available' : 'Need more data'}
        </p>
      </div>

      <div className="bg-white rounded-xl shadow p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-gray-600 text-sm">Recommendations</p>
            <p className="text-2xl font-bold text-gray-800">
              {dashboardData.summary.has_recommendations ? '✓' : '⏳'}
            </p>
          </div>
          <div className="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center">
            <span className="text-2xl">💡</span>
          </div>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          {dashboardData.summary.has_recommendations ? 'Available' : 'Need more data'}
        </p>
      </div>
    </div>
  );

  const renderTrendsTab = () => (
    <div className="space-y-6">
      {dashboardData.trends.weight && (
        <div className="bg-white rounded-xl shadow p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-gray-800">Weight Trends</h3>
            <span className="text-sm text-gray-500">
              {selectedTimePeriod === 7 ? '1 Week' : 
               selectedTimePeriod === 30 ? '1 Month' : '3 Months'} Analysis
            </span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-blue-600">
                {dashboardData.trends.weight.trend_direction === 'increasing' ? '↗️' : 
                 dashboardData.trends.weight.trend_direction === 'decreasing' ? '↘️' : '➡️'}
              </p>
              <p className="text-sm text-gray-600">Direction</p>
              <p className="font-medium capitalize">{dashboardData.trends.weight.trend_direction}</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-green-600">
                {Math.abs(dashboardData.trends.weight.rate_of_change).toFixed(2)}
              </p>
              <p className="text-sm text-gray-600">Rate (lbs/week)</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-purple-600">
                {Math.round(dashboardData.trends.weight.confidence_level * 100)}%
              </p>
              <p className="text-sm text-gray-600">Confidence</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-orange-600">
                {dashboardData.trends.weight.data_points || 0}
              </p>
              <p className="text-sm text-gray-600">Data Points</p>
            </div>
          </div>
          
          {/* Progress Projection for Requirement 4.2 */}
          {dashboardData.trends.weight.rate_of_change && (
            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <h4 className="font-semibold text-blue-800 mb-2">Progress Projection</h4>
              <p className="text-blue-700 text-sm">
                At current rate ({Math.abs(dashboardData.trends.weight.rate_of_change).toFixed(2)} lbs/week), 
                you could {dashboardData.trends.weight.trend_direction === 'increasing' ? 'gain' : 'lose'} approximately{' '}
                <span className="font-semibold">
                  {Math.abs(dashboardData.trends.weight.rate_of_change * 4).toFixed(1)} lbs
                </span> over the next month.
              </p>
            </div>
          )}
        </div>
      )}

      {Object.keys(dashboardData.trends.macros).length > 0 && (
        <div className="bg-white rounded-xl shadow p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Nutrition Trends</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(dashboardData.trends.macros).map(([macro, data]) => (
              <div key={macro} className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-lg font-bold text-gray-800 capitalize">{macro}</p>
                <p className="text-sm text-gray-600">
                  {data.trend_direction === 'increasing' ? '↗️' : 
                   data.trend_direction === 'decreasing' ? '↘️' : '➡️'}
                  {data.trend_direction}
                </p>
                <p className="text-xs text-gray-500">
                  {Math.round(data.confidence_level * 100)}% confidence
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  const renderPredictionsTab = () => (
    <div className="space-y-6">
      {dashboardData.predictions.performance && (
        <div className="bg-white rounded-xl shadow p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Performance Forecast</h3>
          <div className="bg-blue-50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium">Predicted Performance</span>
              <span className="text-sm text-blue-600">
                {Math.round(dashboardData.predictions.performance.confidence_score * 100)}% confidence
              </span>
            </div>
            <p className="text-gray-700">
              Based on your recent patterns, your next workout performance is expected to be{' '}
              <span className="font-semibold">
                {dashboardData.predictions.performance.predicted_performance?.performance_level || 'optimal'}
              </span>
            </p>
          </div>
        </div>
      )}

      {dashboardData.predictions.nutrition && (
        <div className="bg-white rounded-xl shadow p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Nutrition Recommendations</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <p className="text-lg font-bold text-green-700">
                {Math.round(dashboardData.predictions.nutrition.target_calories)}
              </p>
              <p className="text-sm text-gray-600">Calories</p>
            </div>
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <p className="text-lg font-bold text-blue-700">
                {Math.round(dashboardData.predictions.nutrition.target_protein)}g
              </p>
              <p className="text-sm text-gray-600">Protein</p>
            </div>
            <div className="text-center p-4 bg-yellow-50 rounded-lg">
              <p className="text-lg font-bold text-yellow-700">
                {Math.round(dashboardData.predictions.nutrition.target_carbs)}g
              </p>
              <p className="text-sm text-gray-600">Carbs</p>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <p className="text-lg font-bold text-purple-700">
                {Math.round(dashboardData.predictions.nutrition.target_fat)}g
              </p>
              <p className="text-sm text-gray-600">Fat</p>
            </div>
          </div>
          {dashboardData.predictions.nutrition.rationale && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-700">{dashboardData.predictions.nutrition.rationale}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );

  const renderInsightsTab = () => (
    <div className="space-y-6">
      {/* Intervention Strategies for Requirement 4.3 */}
      {dashboardData.interventions && dashboardData.interventions.length > 0 && (
        <div className="bg-white rounded-xl shadow p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">🚨 Intervention Strategies</h3>
          <div className="space-y-4">
            {dashboardData.interventions.map((intervention, index) => (
              <div key={index} className="p-4 bg-orange-50 border-l-4 border-orange-400 rounded-r-lg">
                <div className="flex items-start">
                  <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center mr-3 flex-shrink-0">
                    <span className="text-sm">⚠️</span>
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold text-orange-800 mb-1">
                      {intervention.issue_type || 'Trend Alert'}
                    </h4>
                    <p className="text-orange-700 text-sm mb-2">
                      {intervention.description || intervention.message}
                    </p>
                    {intervention.suggestions && intervention.suggestions.length > 0 && (
                      <div className="mt-2">
                        <p className="text-xs text-orange-600 font-medium mb-1">Suggested Actions:</p>
                        <ul className="text-xs text-orange-700 space-y-1">
                          {intervention.suggestions.map((suggestion, idx) => (
                            <li key={idx} className="flex items-start">
                              <span className="mr-1">•</span>
                              {suggestion}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {dashboardData.insights && dashboardData.insights.length > 0 ? (
        dashboardData.insights.map((insight, index) => (
          <div key={index} className="bg-white rounded-xl shadow p-6">
            <div className="flex items-start">
              <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center mr-4 flex-shrink-0">
                <span className="text-xl">💡</span>
              </div>
              <div className="flex-1">
                <h4 className="font-semibold text-gray-800 mb-2">{insight.title || 'Insight'}</h4>
                <p className="text-gray-700 mb-3">{insight.description || insight.message}</p>
                {insight.confidence_score && (
                  <div className="flex items-center">
                    <span className="text-sm text-gray-500 mr-2">Confidence:</span>
                    <div className="flex-1 bg-gray-200 rounded-full h-2 mr-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full" 
                        style={{ width: `${insight.confidence_score * 100}%` }}
                      ></div>
                    </div>
                    <span className="text-sm text-gray-600">
                      {Math.round(insight.confidence_score * 100)}%
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))
      ) : (
        <div className="bg-white rounded-xl shadow p-8 text-center">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-2xl">🔍</span>
          </div>
          <h3 className="text-lg font-semibold text-gray-800 mb-2">No Insights Yet</h3>
          <p className="text-gray-600">
            Keep logging your data consistently to unlock personalized insights and recommendations.
          </p>
        </div>
      )}
    </div>
  );

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return renderOverviewTab();
      case 'trends':
        return renderTrendsTab();
      case 'predictions':
        return renderPredictionsTab();
      case 'insights':
        return renderInsightsTab();
      default:
        return renderOverviewTab();
    }
  };

  if (loading) return renderLoadingState();
  if (error) return renderErrorState();

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Analytics Dashboard</h1>
          <p className="text-gray-600">
            Insights from your fitness journey • Last updated: {' '}
            {dashboardData?.generated_at ? 
              new Date(dashboardData.generated_at).toLocaleString() : 
              'Just now'
            }
          </p>
        </div>

        {renderDataQualityIndicator()}
        {renderTimePeriodSelector()}
        {renderTabNavigation()}
        {renderTabContent()}

        <div className="mt-8 text-center">
          <button
            onClick={fetchAnalyticsData}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Refresh Analytics
          </button>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;