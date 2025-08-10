import React, { useState, useEffect } from 'react';
import { 
  Settings, 
  Database, 
  Key, 
  Activity, 
  RefreshCw, 
  CheckCircle, 
  AlertCircle, 
  Eye, 
  EyeOff,
  Save,
  TestTube,
  FileText,
  Trash2,
  Download,
  AlertTriangle
} from 'lucide-react';
import apiService from '../services/api';

const AgentManagement = () => {
  const [agents, setAgents] = useState({});
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [selectedTool, setSelectedTool] = useState(null);
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [configForm, setConfigForm] = useState({});
  const [showPasswords, setShowPasswords] = useState({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchAgents();
  }, []);

  const fetchAgents = async () => {
    try {
      const response = await apiService.getAllAgentsStatus();
      setAgents(response.agents);
    } catch (error) {
      console.error('Failed to fetch agents:', error);
    }
  };

  const fetchAgentDetails = async (agentName) => {
    try {
      setLoading(true);
      const response = await fetch(`http://localhost:8000/agents/${agentName}`);
      const data = await response.json();
      setSelectedAgent({ name: agentName, ...data.agent });
    } catch (error) {
      console.error('Failed to fetch agent details:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchToolDetails = async (agentName, toolName) => {
    try {
      setLoading(true);
      const response = await fetch(`http://localhost:8000/agents/${agentName}/tools/${toolName}`);
      const data = await response.json();
      setSelectedTool(data.tool);
      setConfigForm(data.tool.current_config || {});
    } catch (error) {
      console.error('Failed to fetch tool details:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateToolConfig = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `http://localhost:8000/agents/${selectedAgent.name}/tools/${selectedTool.name}/config`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ config: configForm })
        }
      );
      const data = await response.json();
      
      if (data.success) {
        alert('Configuration updated successfully!');
        setShowConfigModal(false);
        fetchToolDetails(selectedAgent.name, selectedTool.name);
      } else {
        alert('Failed to update configuration: ' + data.error);
      }
    } catch (error) {
      console.error('Failed to update tool config:', error);
      alert('Failed to update configuration');
    } finally {
      setLoading(false);
    }
  };

  const testToolConnection = async (agentName, toolName) => {
    try {
      setLoading(true);
      const response = await fetch(
        `http://localhost:8000/agents/${agentName}/tools/${toolName}/test`,
        { method: 'POST' }
      );
      const data = await response.json();
      
      if (data.success) {
        alert(`Test Results:\\n${JSON.stringify(data.test_results, null, 2)}`);
      } else {
        alert('Test failed: ' + data.error);
      }
    } catch (error) {
      console.error('Failed to test tool:', error);
    } finally {
      setLoading(false);
    }
  };

  const restartAgent = async (agentName) => {
    try {
      setLoading(true);
      const response = await fetch(
        `http://localhost:8000/agents/${agentName}/restart`,
        { method: 'POST' }
      );
      const data = await response.json();
      
      if (data.success) {
        alert(`Agent ${agentName} restarted successfully!`);
        fetchAgents();
      } else {
        alert('Failed to restart agent: ' + data.error);
      }
    } catch (error) {
      console.error('Failed to restart agent:', error);
    } finally {
      setLoading(false);
    }
  };

  const togglePasswordVisibility = (field) => {
    setShowPasswords(prev => ({
      ...prev,
      [field]: !prev[field]
    }));
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy':
      case 'active':
      case 'connected':
        return 'text-green-500';
      case 'warning':
        return 'text-yellow-500';
      case 'unreachable':
      case 'error':
        return 'text-red-500';
      default:
        return 'text-gray-500';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy':
      case 'active':
      case 'connected':
        return <CheckCircle className="w-4 h-4" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4" />;
      case 'unreachable':
      case 'error':
        return <AlertCircle className="w-4 h-4" />;
      default:
        return <AlertCircle className="w-4 h-4" />;
    }
  };

  if (!selectedAgent) {
    return (
      <div className="p-6">
        <h2 className="text-2xl font-bold mb-6">Agent Management & Configuration</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {Object.entries(agents).map(([agentKey, agent]) => (
            <div
              key={agentKey}
              className="bg-white rounded-lg shadow-lg border border-gray-200 p-6 cursor-pointer hover:shadow-xl transition-shadow"
              onClick={() => fetchAgentDetails(agentKey)}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">{agent.name}</h3>
                <div className={`flex items-center gap-1 ${getStatusColor(agent.status)}`}>
                  {getStatusIcon(agent.status)}
                  <span className="text-sm">{agent.status}</span>
                </div>
              </div>
              
              <p className="text-gray-600 text-sm mb-4">{agent.description}</p>
              
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>MCP Tools:</span>
                  <span className="font-semibold">{agent.total_tools}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Port:</span>
                  <span className="font-mono">{agent.port}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Databases:</span>
                  <span className="font-semibold">{agent.databases?.length || 0}</span>
                </div>
              </div>
              
              <div className="mt-4 flex flex-wrap gap-1">
                {agent.external_apis?.slice(0, 3).map((api) => (
                  <span
                    key={api}
                    className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded"
                  >
                    {api}
                  </span>
                ))}
                {agent.external_apis?.length > 3 && (
                  <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                    +{agent.external_apis.length - 3} more
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (selectedTool && showConfigModal) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          <div className="p-6">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-bold">
                Configure {selectedTool.name}
              </h3>
              <button
                onClick={() => setShowConfigModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ×
              </button>
            </div>

            <div className="space-y-4">
              {Object.entries(selectedTool.configuration_schema?.properties || {}).map(([field, schema]) => (
                <div key={field}>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {field.replace(/_/g, ' ').replace(/\\b\\w/g, l => l.toUpperCase())}
                    {schema.required && <span className="text-red-500 ml-1">*</span>}
                  </label>
                  
                  <div className="relative">
                    <input
                      type={showPasswords[field] ? 'text' : 'password'}
                      className="w-full px-3 py-2 pr-12 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder={schema.description}
                      value={configForm[field] || ''}
                      onChange={(e) => setConfigForm(prev => ({
                        ...prev,
                        [field]: e.target.value
                      }))}
                    />
                    
                    <button
                      type="button"
                      className="absolute right-3 top-2.5 text-gray-400 hover:text-gray-600"
                      onClick={() => togglePasswordVisibility(field)}
                    >
                      {showPasswords[field] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  
                  <p className="mt-1 text-sm text-gray-500">{schema.description}</p>
                </div>
              ))}
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowConfigModal(false)}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
                disabled={loading}
              >
                Cancel
              </button>
              <button
                onClick={updateToolConfig}
                className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 flex items-center gap-2"
                disabled={loading}
              >
                <Save className="w-4 h-4" />
                {loading ? 'Saving...' : 'Save Configuration'}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <button
            onClick={() => {
              setSelectedAgent(null);
              setSelectedTool(null);
            }}
            className="text-blue-500 hover:text-blue-700 mb-2"
          >
            ← Back to Agents
          </button>
          <h2 className="text-2xl font-bold">{selectedAgent.name} - Agent Management</h2>
          <p className="text-gray-600">{selectedAgent.description}</p>
        </div>
        
        <div className="flex items-center gap-2">
          <div className={`flex items-center gap-2 ${getStatusColor(selectedAgent.status)}`}>
            {getStatusIcon(selectedAgent.status)}
            <span>{selectedAgent.status}</span>
          </div>
          <button
            onClick={() => restartAgent(selectedAgent.name)}
            className="px-3 py-2 bg-orange-500 text-white rounded-md hover:bg-orange-600 flex items-center gap-2"
            disabled={loading}
          >
            <RefreshCw className="w-4 h-4" />
            Restart
          </button>
        </div>
      </div>

      {/* Runtime Info */}
      {selectedAgent.runtime_info && (
        <div className="bg-gray-50 rounded-lg p-4 mb-6">
          <h3 className="font-semibold mb-3">Runtime Information</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Uptime:</span>
              <div className="font-mono">{selectedAgent.runtime_info.uptime}</div>
            </div>
            <div>
              <span className="text-gray-500">Requests:</span>
              <div className="font-mono">{selectedAgent.runtime_info.requests_handled}</div>
            </div>
            <div>
              <span className="text-gray-500">Success Rate:</span>
              <div className="font-mono text-green-600">{selectedAgent.runtime_info.success_rate}</div>
            </div>
            <div>
              <span className="text-gray-500">Memory:</span>
              <div className="font-mono">{selectedAgent.runtime_info.memory_usage}</div>
            </div>
          </div>
        </div>
      )}

      {/* MCP Tools */}
      <div className="bg-white rounded-lg shadow-lg mb-6">
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Settings className="w-5 h-5" />
            MCP Tools ({selectedAgent.mcp_tools?.length || 0})
          </h3>
          
          <div className="grid gap-4">
            {selectedAgent.mcp_tools?.map((tool) => (
              <div
                key={tool.name}
                className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors cursor-pointer"
                onClick={() => fetchToolDetails(selectedAgent.name, tool.name)}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <h4 className="font-medium">{tool.name}</h4>
                    <div className={`flex items-center gap-1 ${getStatusColor(tool.status)}`}>
                      {getStatusIcon(tool.status)}
                      <span className="text-sm">{tool.status}</span>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        testToolConnection(selectedAgent.name, tool.name);
                      }}
                      className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-sm hover:bg-blue-200 flex items-center gap-1"
                      disabled={loading}
                    >
                      <TestTube className="w-3 h-3" />
                      Test
                    </button>
                    
                    {tool.requires_config && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          fetchToolDetails(selectedAgent.name, tool.name);
                          setShowConfigModal(true);
                        }}
                        className="px-2 py-1 bg-green-100 text-green-700 rounded text-sm hover:bg-green-200 flex items-center gap-1"
                      >
                        <Key className="w-3 h-3" />
                        Configure
                      </button>
                    )}
                  </div>
                </div>
                
                <p className="text-gray-600 text-sm mb-3">{tool.description}</p>
                
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-4">
                    <span className="text-gray-500">
                      Config Items: {tool.config_items?.length || 0}
                    </span>
                    <span className="text-gray-500">
                      Last Used: {new Date(tool.last_used).toLocaleTimeString()}
                    </span>
                  </div>
                  
                  {tool.requires_config && (
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      tool.config_items?.length > 0 
                        ? 'bg-yellow-100 text-yellow-800' 
                        : 'bg-green-100 text-green-800'
                    }`}>
                      {tool.config_items?.length > 0 ? 'Needs Config' : 'Configured'}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Databases */}
      <div className="bg-white rounded-lg shadow-lg mb-6">
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Database className="w-5 h-5" />
            Databases ({selectedAgent.databases?.length || 0})
          </h3>
          
          <div className="grid md:grid-cols-2 gap-4">
            {selectedAgent.databases?.map((db) => (
              <div key={db} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium">{db}</h4>
                  <div className="flex items-center gap-1 text-green-500">
                    <CheckCircle className="w-4 h-4" />
                    <span className="text-sm">Connected</span>
                  </div>
                </div>
                
                <div className="text-sm text-gray-600 space-y-1">
                  <div>Size: 45MB</div>
                  <div>Last Backup: Today 10:00 AM</div>
                </div>
                
                <div className="mt-3 flex gap-2">
                  <button className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-sm hover:bg-blue-200 flex items-center gap-1">
                    <Download className="w-3 h-3" />
                    Backup
                  </button>
                  <button className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-sm hover:bg-gray-200 flex items-center gap-1">
                    <FileText className="w-3 h-3" />
                    Logs
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* External APIs */}
      <div className="bg-white rounded-lg shadow-lg">
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5" />
            External APIs ({selectedAgent.external_apis?.length || 0})
          </h3>
          
          <div className="grid md:grid-cols-3 gap-4">
            {selectedAgent.external_apis?.map((api) => (
              <div key={api} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium">{api}</h4>
                  <div className="flex items-center gap-1 text-green-500">
                    <CheckCircle className="w-4 h-4" />
                    <span className="text-sm">Active</span>
                  </div>
                </div>
                
                <div className="text-sm text-gray-600">
                  Rate limit: 95/100 requests
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentManagement;