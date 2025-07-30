import React from 'react';
import { CheckCircle, AlertCircle, Activity, Calendar, Heart, ShoppingCart, ChefHat } from 'lucide-react';

const WorkflowViewer = ({ workflows, agentInfo }) => {
  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'text-green-500';
      case 'running': return 'text-blue-500';
      case 'failed': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': 
        return <CheckCircle className="w-4 h-4" />;
      case 'running': 
        return <Activity className="w-4 h-4 animate-spin" />;
      case 'failed': 
        return <AlertCircle className="w-4 h-4" />;
      default: 
        return <Activity className="w-4 h-4" />;
    }
  };

  const formatTime = (timeString) => {
    if (!timeString) return 'Unknown';
    return new Date(timeString).toLocaleTimeString();
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-900">Active Workflows</h2>
        <span className="text-sm text-gray-500">{workflows.length} workflows</span>
      </div>
      
      <div className="space-y-4">
        {workflows.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Activity className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>No active workflows</p>
            <p className="text-xs">Start a workflow to see activity here</p>
          </div>
        ) : (
          workflows.map((workflow) => (
            <div key={workflow.id} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
              {/* Workflow Header */}
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className={`flex items-center gap-1 ${getStatusColor(workflow.status)}`}>
                    {getStatusIcon(workflow.status)}
                    <h3 className="font-medium text-gray-900">{workflow.name}</h3>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    workflow.status === 'completed' ? 'bg-green-100 text-green-800' :
                    workflow.status === 'running' ? 'bg-blue-100 text-blue-800' :
                    workflow.status === 'failed' ? 'bg-red-100 text-red-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {workflow.status}
                  </span>
                </div>
                <span className="text-sm text-gray-500">
                  {Math.round(workflow.progress || 0)}% complete
                </span>
              </div>
              
              {/* Progress Bar */}
              <div className="w-full bg-gray-200 rounded-full h-2 mb-3">
                <div 
                  className={`h-2 rounded-full transition-all duration-500 ${
                    workflow.status === 'completed' ? 'bg-green-500' :
                    workflow.status === 'running' ? 'bg-blue-500' :
                    workflow.status === 'failed' ? 'bg-red-500' :
                    'bg-gray-400'
                  }`}
                  style={{ width: `${workflow.progress || 0}%` }}
                ></div>
              </div>
              
              {/* Workflow Details */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500">Agents involved:</span>
                  <div className="flex gap-1">
                    {workflow.agents?.map(agentKey => {
                      const agent = agentInfo[agentKey];
                      if (!agent) return null;
                      
                      const Icon = agent.icon;
                      return (
                        <div 
                          key={agentKey} 
                          className={`p-1 rounded ${agent.color} tooltip`}
                          title={agent.name}
                        >
                          <Icon className="w-3 h-3 text-white" />
                        </div>
                      );
                    })}
                  </div>
                </div>
                
                <div className="flex flex-col items-end text-xs text-gray-500">
                  {workflow.completedAt && (
                    <span>Completed: {formatTime(workflow.completedAt)}</span>
                  )}
                  {workflow.estimatedCompletion && !workflow.completedAt && (
                    <span>ETA: {formatTime(workflow.estimatedCompletion)}</span>
                  )}
                  {workflow.startedAt && !workflow.completedAt && !workflow.estimatedCompletion && (
                    <span>Started: {formatTime(workflow.startedAt)}</span>
                  )}
                </div>
              </div>
              
              {/* Workflow Steps (if available) */}
              {workflow.steps && workflow.steps.length > 0 && (
                <div className="mt-3 pt-3 border-t">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs text-gray-500">Steps:</span>
                  </div>
                  <div className="flex gap-1">
                    {workflow.steps.map((step, index) => (
                      <div 
                        key={index}
                        className={`w-3 h-3 rounded-full ${
                          index < (workflow.progress / 100) * workflow.steps.length ? 
                          'bg-blue-500' : 'bg-gray-300'
                        }`}
                        title={step.name || `Step ${index + 1}`}
                      ></div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default WorkflowViewer;