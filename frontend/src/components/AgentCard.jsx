import React from 'react';
import { CheckCircle, AlertCircle, Activity, Clock } from 'lucide-react';

const AgentCard = ({ agent, agentKey, status }) => {
  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return 'text-green-500';
      case 'running': return 'text-blue-500';
      case 'warning': return 'text-yellow-500';
      case 'failed': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy': 
        return <CheckCircle className="w-4 h-4" />;
      case 'running': 
        return <Activity className="w-4 h-4 animate-spin" />;
      case 'warning': 
        return <AlertCircle className="w-4 h-4" />;
      case 'failed': 
        return <AlertCircle className="w-4 h-4" />;
      default: 
        return <Clock className="w-4 h-4" />;
    }
  };

  const Icon = agent.icon;
  
  return (
    <div className="bg-white rounded-lg shadow-sm border overflow-hidden hover:shadow-md transition-shadow">
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div className={`p-3 rounded-lg ${agent.color}`}>
            <Icon className="w-6 h-6 text-white" />
          </div>
          <div className={`flex items-center gap-1 ${getStatusColor(status.status)}`}>
            {getStatusIcon(status.status)}
            <span className="text-sm font-medium capitalize">{status.status}</span>
          </div>
        </div>
        
        <h3 className="text-lg font-semibold text-gray-900 mb-1">{agent.name}</h3>
        <p className="text-sm text-gray-600 mb-3">{agent.role}</p>
        <p className="text-xs text-gray-500 mb-4">{agent.description}</p>
        
        <div className="flex justify-between items-center text-xs text-gray-500">
          <span>Tasks: {status.tasks}</span>
          <span>Updated: {status.lastUpdate}</span>
        </div>
        
        {/* Status indicator bar */}
        <div className="mt-3 w-full bg-gray-200 rounded-full h-1">
          <div 
            className={`h-1 rounded-full transition-all duration-300 ${
              status.status === 'healthy' ? 'bg-green-500' :
              status.status === 'running' ? 'bg-blue-500' :
              status.status === 'warning' ? 'bg-yellow-500' :
              'bg-red-500'
            }`}
            style={{ width: status.status === 'healthy' ? '100%' : '60%' }}
          ></div>
        </div>
      </div>
    </div>
  );
};

export default AgentCard;