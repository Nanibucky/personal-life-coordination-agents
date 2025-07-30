import React, { useState, useEffect } from 'react';
import { Calendar, Heart, ShoppingCart, ChefHat, Activity, Clock, CheckCircle, AlertCircle, TrendingUp } from 'lucide-react';

const Dashboard = () => {
  const [agents, setAgents] = useState({
    nani: { status: 'healthy', lastUpdate: '2 minutes ago', tasks: 12 },
    luna: { status: 'healthy', lastUpdate: '1 minute ago', tasks: 8 },
    bucky: { status: 'healthy', lastUpdate: '30 seconds ago', tasks: 5 },
    milo: { status: 'healthy', lastUpdate: '1 minute ago', tasks: 3 }
  });

  const [workflows, setWorkflows] = useState([
    {
      id: 'wf_001',
      name: 'Weekly Meal Planning',
      status: 'completed',
      progress: 100,
      agents: ['milo', 'bucky', 'nani'],
      completedAt: '2025-07-23T10:30:00Z'
    },
    {
      id: 'wf_002', 
      name: 'Fitness Schedule Optimization',
      status: 'running',
      progress: 75,
      agents: ['luna', 'nani'],
      estimatedCompletion: '2025-07-23T11:15:00Z'
    }
  ]);

  const [systemMetrics, setSystemMetrics] = useState({
    totalWorkflows: 24,
    successRate: 96.8,
    avgResponseTime: 1.2,
    agentCoordinations: 156
  });

  const agentInfo = {
    nani: { 
      name: 'Nani', 
      role: 'Scheduler & Calendar', 
      icon: Calendar, 
      color: 'bg-blue-500',
      description: 'Optimizes your schedule and manages calendar events'
    },
    luna: { 
      name: 'Luna', 
      role: 'Health & Fitness', 
      icon: Heart, 
      color: 'bg-red-500',
      description: 'Tracks health metrics and plans workouts'
    },
    bucky: { 
      name: 'Bucky', 
      role: 'Shopping & Inventory', 
      icon: ShoppingCart, 
      color: 'bg-green-500',
      description: 'Manages pantry inventory and optimizes shopping'
    },
    milo: { 
      name: 'Milo', 
      role: 'Meal Planning', 
      icon: ChefHat, 
      color: 'bg-orange-500',
      description: 'Creates meal plans and analyzes nutrition'
    }
  };

  const executeWorkflow = async (workflowType) => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/workflow', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          type: workflowType,
          fitness_goals: ['weight_loss', 'strength'],
          dietary_preferences: ['vegetarian'],
          user_id: 'demo_user'
        })
      });
      
      const result = await response.json();
      
      // Update workflows with new execution
      const newWorkflow = {
        id: result.workflow_id || `wf_${Date.now()}`,
        name: workflowType === 'meal_planning' ? 'Meal Planning Workflow' : 'Fitness Scheduling',
        status: 'running',
        progress: 0,
        agents: workflowType === 'meal_planning' ? ['milo', 'bucky', 'nani', 'luna'] : ['luna', 'nani'],
        startedAt: new Date().toISOString()
      };
      
      setWorkflows(prev => [newWorkflow, ...prev]);
    } catch (error) {
      console.error('Workflow execution failed:', error);
      
      // Still add workflow for demo purposes
      const newWorkflow = {
        id: `wf_${Date.now()}`,
        name: workflowType === 'meal_planning' ? 'Meal Planning Workflow' : 'Fitness Scheduling',
        status: 'running',
        progress: 0,
        agents: workflowType === 'meal_planning' ? ['milo', 'bucky', 'nani', 'luna'] : ['luna', 'nani'],
        startedAt: new Date().toISOString()
      };
      
      setWorkflows(prev => [newWorkflow, ...prev]);
    }
  };

  useEffect(() => {
    // Simulate real-time updates
    const interval = setInterval(() => {
      setWorkflows(prev => prev.map(wf => {
        if (wf.status === 'running' && wf.progress < 100) {
          const newProgress = Math.min(wf.progress + Math.random() * 15, 100);
          return {
            ...wf,
            progress: newProgress,
            status: newProgress === 100 ? 'completed' : 'running'
          };
        }
        return wf;
      }));

      // Update system metrics
      setSystemMetrics(prev => ({
        ...prev,
        agentCoordinations: prev.agentCoordinations + Math.floor(Math.random() * 3)
      }));
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return 'text-green-500';
      case 'running': return 'text-blue-500';
      case 'completed': return 'text-green-500';
      case 'failed': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy':
      case 'completed': 
        return <CheckCircle className="w-4 h-4" />;
      case 'running': 
        return <Activity className="w-4 h-4 animate-spin" />;
      case 'failed': 
        return <AlertCircle className="w-4 h-4" />;
      default: 
        return <Clock className="w-4 h-4" />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold text-gray-900">Personal Life Coordination</h1>
          <p className="text-lg text-gray-600">AI Agents Working Together for Optimal Life Management</p>
        </div>

        {/* System Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg p-6 shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Workflows</p>
                <p className="text-2xl font-bold text-blue-600">{systemMetrics.totalWorkflows}</p>
              </div>
              <TrendingUp className="w-8 h-8 text-blue-500" />
            </div>
          </div>
          
          <div className="bg-white rounded-lg p-6 shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Success Rate</p>
                <p className="text-2xl font-bold text-green-600">{systemMetrics.successRate}%</p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-500" />
            </div>
          </div>
          
          <div className="bg-white rounded-lg p-6 shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Avg Response Time</p>
                <p className="text-2xl font-bold text-orange-600">{systemMetrics.avgResponseTime}s</p>
              </div>
              <Clock className="w-8 h-8 text-orange-500" />
            </div>
          </div>
          
          <div className="bg-white rounded-lg p-6 shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Agent Coordinations</p>
                <p className="text-2xl font-bold text-purple-600">{systemMetrics.agentCoordinations}</p>
              </div>
              <Activity className="w-8 h-8 text-purple-500" />
            </div>
          </div>
        </div>

        {/* Agent Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {Object.entries(agentInfo).map(([key, agent]) => {
            const Icon = agent.icon;
            const status = agents[key];
            
            return (
              <div key={key} className="bg-white rounded-lg shadow-sm border overflow-hidden">
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
                </div>
              </div>
            );
          })}
        </div>

        {/* Workflow Controls */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Execute Workflows</h2>
          <div className="flex gap-4 flex-wrap">
            <button 
              onClick={() => executeWorkflow('meal_planning')}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
            >
              <ChefHat className="w-4 h-4" />
              Plan Weekly Meals
            </button>
            
            <button 
              onClick={() => executeWorkflow('fitness_scheduling')}
              className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2"
            >
              <Heart className="w-4 h-4" />
              Optimize Fitness Schedule
            </button>
            
            <button 
              onClick={() => executeWorkflow('shopping_optimization')}
              className="px-6 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors flex items-center gap-2"
            >
              <ShoppingCart className="w-4 h-4" />
              Optimize Shopping Routes
            </button>
          </div>
        </div>

        {/* Active Workflows */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Active Workflows</h2>
          <div className="space-y-4">
            {workflows.map((workflow) => (
              <div key={workflow.id} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className={`flex items-center gap-1 ${getStatusColor(workflow.status)}`}>
                      {getStatusIcon(workflow.status)}
                      <h3 className="font-medium text-gray-900">{workflow.name}</h3>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      workflow.status === 'completed' ? 'bg-green-100 text-green-800' :
                      workflow.status === 'running' ? 'bg-blue-100 text-blue-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {workflow.status}
                    </span>
                  </div>
                  <span className="text-sm text-gray-500">
                    {Math.round(workflow.progress)}% complete
                  </span>
                </div>
                
                <div className="w-full bg-gray-200 rounded-full h-2 mb-3">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${workflow.progress}%` }}
                  ></div>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-500">Agents involved:</span>
                    {workflow.agents.map(agentKey => {
                      const agent = agentInfo[agentKey];
                      const Icon = agent.icon;
                      return (
                        <div key={agentKey} className={`p-1 rounded ${agent.color}`}>
                          <Icon className="w-3 h-3 text-white" />
                        </div>
                      );
                    })}
                  </div>
                  <span className="text-xs text-gray-500">
                    {workflow.completedAt ? 
                      `Completed: ${new Date(workflow.completedAt).toLocaleTimeString()}` :
                      workflow.estimatedCompletion ? 
                        `ETA: ${new Date(workflow.estimatedCompletion).toLocaleTimeString()}` :
                        `Started: ${new Date(workflow.startedAt).toLocaleTimeString()}`
                    }
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* A2A Communication Log */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Agent Communications</h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1">
                  <div className="p-1 rounded bg-orange-500">
                    <ChefHat className="w-3 h-3 text-white" />
                  </div>
                  <span className="text-sm">→</span>
                  <div className="p-1 rounded bg-green-500">
                    <ShoppingCart className="w-3 h-3 text-white" />
                  </div>
                </div>
                <span className="text-sm text-gray-700">Milo requested pantry inventory from Bucky</span>
              </div>
              <span className="text-xs text-gray-500">2 min ago</span>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1">
                  <div className="p-1 rounded bg-red-500">
                    <Heart className="w-3 h-3 text-white" />
                  </div>
                  <span className="text-sm">→</span>
                  <div className="p-1 rounded bg-blue-500">
                    <Calendar className="w-3 h-3 text-white" />
                  </div>
                </div>
                <span className="text-sm text-gray-700">Luna provided optimal workout times to Nani</span>
              </div>
              <span className="text-xs text-gray-500">5 min ago</span>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1">
                  <div className="p-1 rounded bg-blue-500">
                    <Calendar className="w-3 h-3 text-white" />
                  </div>
                  <span className="text-sm">→</span>
                  <div className="p-1 rounded bg-green-500">
                    <ShoppingCart className="w-3 h-3 text-white" />
                  </div>
                </div>
                <span className="text-sm text-gray-700">Nani scheduled shopping trip optimization with Bucky</span>
              </div>
              <span className="text-xs text-gray-500">8 min ago</span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center text-sm text-gray-500">
          <p>Personal Life Coordination Agents v1.0 - Powered by MCP & A2A Protocols</p>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;