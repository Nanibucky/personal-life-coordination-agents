import React, { useState, useEffect } from 'react';
import { Calendar, Heart, ShoppingCart, ChefHat, Settings, Play, Pause, RotateCcw } from 'lucide-react';
import AgentCard from '../components/AgentCard';
import apiService from '../services/api';

const AgentsPage = () => {
  const [agents, setAgents] = useState({
    nani: { status: 'healthy', lastUpdate: '2 minutes ago', tasks: 12 },
    luna: { status: 'healthy', lastUpdate: '1 minute ago', tasks: 8 },
    bucky: { status: 'healthy', lastUpdate: '30 seconds ago', tasks: 5 },
    milo: { status: 'healthy', lastUpdate: '1 minute ago', tasks: 3 }
  });

  const [selectedAgent, setSelectedAgent] = useState('nani');
  const [agentTools, setAgentTools] = useState([]);
  const [toolResults, setToolResults] = useState({});

  const agentInfo = {
    nani: { 
      name: 'Nani', 
      role: 'Scheduler & Calendar', 
      icon: Calendar, 
      color: 'bg-blue-500',
      description: 'Optimizes your schedule and manages calendar events',
      capabilities: ['Calendar Management', 'Time Optimization', 'Meeting Coordination', 'Focus Time Blocking']
    },
    luna: { 
      name: 'Luna', 
      role: 'Health & Fitness', 
      icon: Heart, 
      color: 'bg-red-500',
      description: 'Tracks health metrics and plans workouts',
      capabilities: ['Fitness Tracking', 'Health Analysis', 'Workout Planning', 'Recovery Monitoring']
    },
    bucky: { 
      name: 'Bucky', 
      role: 'Shopping & Inventory', 
      icon: ShoppingCart, 
      color: 'bg-green-500',
      description: 'Manages pantry inventory and optimizes shopping',
      capabilities: ['Pantry Tracking', 'Price Comparison', 'Shopping Optimization', 'Deal Finding']
    },
    milo: { 
      name: 'Milo', 
      role: 'Meal Planning', 
      icon: ChefHat, 
      color: 'bg-orange-500',
      description: 'Creates meal plans and analyzes nutrition',
      capabilities: ['Recipe Discovery', 'Nutrition Analysis', 'Meal Planning', 'Dietary Management']
    }
  };

  useEffect(() => {
    loadAgentTools(selectedAgent);
  }, [selectedAgent]);

  const loadAgentTools = async (agentName) => {
    try {
      const tools = await apiService.getAgentTools(agentName);
      setAgentTools(tools.tools || []);
    } catch (error) {
      console.error('Failed to load agent tools:', error);
      // Mock tools for demo
      setAgentTools([
        {
          name: 'mock_tool',
          description: 'Demo tool for testing',
          parameters: { type: 'object', properties: { action: { type: 'string' } } }
        }
      ]);
    }
  };

  const executeTool = async (toolName, parameters = {}) => {
    try {
      const result = await apiService.executeAgentTool(selectedAgent, toolName, parameters);
      setToolResults(prev => ({
        ...prev,
        [toolName]: result
      }));
    } catch (error) {
      console.error('Tool execution failed:', error);
      setToolResults(prev => ({
        ...prev,
        [toolName]: { success: false, error: error.message }
      }));
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold text-gray-900">Agent Management</h1>
          <p className="text-lg text-gray-600">Monitor and control individual AI agents</p>
        </div>

        {/* Agent Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {Object.entries(agentInfo).map(([key, agent]) => (
            <div 
              key={key}
              className={`cursor-pointer transition-all ${
                selectedAgent === key ? 'ring-2 ring-blue-500' : ''
              }`}
              onClick={() => setSelectedAgent(key)}
            >
              <AgentCard 
                agent={agent} 
                agentKey={key} 
                status={agents[key]} 
              />
            </div>
          ))}
        </div>

        {/* Selected Agent Details */}
        {selectedAgent && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Agent Details */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className={`p-3 rounded-lg ${agentInfo[selectedAgent].color}`}>
                    {React.createElement(agentInfo[selectedAgent].icon, { className: "w-6 h-6 text-white" })}
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      {agentInfo[selectedAgent].name}
                    </h3>
                    <p className="text-sm text-gray-600">
                      {agentInfo[selectedAgent].role}
                    </p>
                  </div>
                </div>

                <p className="text-sm text-gray-700 mb-4">
                  {agentInfo[selectedAgent].description}
                </p>

                <div className="space-y-3">
                  <h4 className="text-sm font-medium text-gray-900">Capabilities</h4>
                  <ul className="space-y-1">
                    {agentInfo[selectedAgent].capabilities.map((capability, index) => (
                      <li key={index} className="flex items-center gap-2 text-sm text-gray-600">
                        <div className="w-1.5 h-1.5 bg-gray-400 rounded-full"></div>
                        {capability}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Agent Controls */}
                <div className="mt-6 space-y-2">
                  <h4 className="text-sm font-medium text-gray-900">Controls</h4>
                  <div className="flex gap-2">
                    <button className="flex items-center gap-1 px-3 py-1 bg-green-100 text-green-700 rounded text-sm hover:bg-green-200">
                      <Play className="w-3 h-3" />
                      Start
                    </button>
                    <button className="flex items-center gap-1 px-3 py-1 bg-yellow-100 text-yellow-700 rounded text-sm hover:bg-yellow-200">
                      <Pause className="w-3 h-3" />
                      Pause
                    </button>
                    <button className="flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-700 rounded text-sm hover:bg-blue-200">
                      <RotateCcw className="w-3 h-3" />
                      Restart
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Agent Tools */}
            <div className="lg:col-span-2">
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Available Tools</h3>
                
                <div className="space-y-4">
                  {agentTools.map((tool, index) => (
                    <div key={index} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium text-gray-900">{tool.name}</h4>
                        <button 
                          onClick={() => executeTool(tool.name, { action: 'test' })}
                          className="px-3 py-1 bg-blue-100 text-blue-700 rounded text-sm hover:bg-blue-200"
                        >
                          Execute
                        </button>
                      </div>
                      
                      <p className="text-sm text-gray-600 mb-3">{tool.description}</p>
                      
                      {/* Tool Result */}
                      {toolResults[tool.name] && (
                        <div className={`mt-3 p-3 rounded text-sm ${
                          toolResults[tool.name].success ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
                        }`}>
                          <strong>Result:</strong>
                          <pre className="mt-1 text-xs whitespace-pre-wrap">
                            {JSON.stringify(toolResults[tool.name], null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  ))}
                  
                  {agentTools.length === 0 && (
                    <div className="text-center py-8 text-gray-500">
                      <Settings className="w-12 h-12 mx-auto mb-2 opacity-50" />
                      <p>No tools available</p>
                      <p className="text-xs">Agent may be offline or tools not loaded</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AgentsPage;