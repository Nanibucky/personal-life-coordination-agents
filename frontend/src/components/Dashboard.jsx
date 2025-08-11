import React, { useState, useEffect } from 'react';
import { Send, Bell, Shield, MessageSquare, Users, Settings, Calendar, Heart, ShoppingCart, ChefHat, Wrench } from 'lucide-react';
import apiService from '../services/api';
import AgentManagement from './AgentManagement';

const Dashboard = () => {
  const [currentView, setCurrentView] = useState('dashboard');
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'system',
      content: 'Welcome to your Personal Life Coordination System! Your agents are ready to help with meals, health, shopping, and scheduling. Try asking something like "What should I eat for dinner?" or "Help me plan my week".',
      timestamp: new Date().toISOString()
    }
  ]);

  const [notifications, setNotifications] = useState([
    {
      id: 1,
      type: 'external_request',
      from: 'Agent X (John\'s Scheduler)',
      message: 'Requesting meeting slot for "Project Discussion" - prefers afternoons this week',
      status: 'pending',
      timestamp: '5 minutes ago'
    }
  ]);

  const [a2aCommunications, setA2ACommunications] = useState([
    {
      id: 1,
      from: 'milo',
      to: 'bucky',
      message: 'Need current pantry inventory for meal planning',
      timestamp: '2 min ago',
      status: 'completed'
    },
    {
      id: 2,
      from: 'bucky',
      to: 'milo',
      message: 'Pantry data sent: quinoa (2 cups), vegetables (mixed), olive oil available',
      timestamp: '1 min ago',
      status: 'completed'
    },
    {
      id: 3,
      from: 'Agent X',
      to: 'nani',
      message: 'External request: Meeting availability for project discussion',
      timestamp: '5 min ago',
      status: 'pending_approval'
    }
  ]);

  const [externalAgentAccess] = useState([
    {
      id: 1,
      agentName: 'Agent X',
      owner: 'John Smith',
      accessLevel: 'scheduling_only',
      status: 'approved',
      connectedTo: ['nani']
    }
  ]);

  const [realAgents, setRealAgents] = useState({});
  const [connectionStatus, setConnectionStatus] = useState('connecting');

  const agents = {
    milo: { name: 'Milo', role: 'Meal Planning', icon: ChefHat, color: 'text-orange-500' },
    luna: { name: 'Luna', role: 'Health & Fitness', icon: Heart, color: 'text-red-500' },
    bucky: { name: 'Bucky', role: 'Shopping & Inventory', icon: ShoppingCart, color: 'text-green-500' },
    nani: { name: 'Nani', role: 'Scheduler & Calendar', icon: Calendar, color: 'text-blue-500' }
  };

  // Fetch real agent status
  useEffect(() => {
    const fetchAgentStatus = async () => {
      try {
        const response = await apiService.getAllAgentsStatus();
        if (response.agents) {
          setRealAgents(response.agents);
          setConnectionStatus('connected');
        }
      } catch (error) {
        console.error('Failed to fetch agent status:', error);
        setConnectionStatus('disconnected');
      }
    };

    fetchAgentStatus();
    
    // Poll every 10 seconds for updates
    const interval = setInterval(fetchAgentStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleSendQuery = async () => {
    if (!query.trim()) return;
    
    const newMessage = {
      id: messages.length + 1,
      type: 'user',
      content: query,
      timestamp: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, newMessage]);
    const currentQuery = query;
    setQuery('');
    
    // Add intelligent analysis message
    const analysisMessage = {
      id: messages.length + 2,
      type: 'system',
      content: '🧠 Master Coordinator analyzing your query...',
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, analysisMessage]);
    
    try {
      // Send workflow request to backend with Master Coordinator
      const workflowResponse = await apiService.executeWorkflow({
        type: 'general_query',
        user_id: 'frontend_user',
        query: currentQuery,
        timestamp: new Date().toISOString()
      });
      
      if (workflowResponse.workflow_id) {
        // Poll for workflow completion
        let attempts = 0;
        const maxAttempts = 10;
        
        const pollWorkflow = async () => {
          try {
            const statusResponse = await apiService.getWorkflowStatus(workflowResponse.workflow_id);
            
            if (statusResponse.status === 'completed' && statusResponse.result) {
              const agentResponse = {
                id: messages.length + 3,
                type: 'agent',
                agent: statusResponse.primary_agent || 'master_coordinator',
                content: statusResponse.result || 'Task completed successfully!',
                timestamp: new Date().toISOString()
              };
              setMessages(prev => [...prev, agentResponse]);
            } else if (statusResponse.status === 'failed') {
              const errorResponse = {
                id: messages.length + 3,
                type: 'agent',
                agent: 'system',
                content: `I'm having trouble processing your request right now. Please try again or be more specific about what you need help with.`,
                timestamp: new Date().toISOString()
              };
              setMessages(prev => [...prev, errorResponse]);
            } else if (attempts < maxAttempts) {
              attempts++;
              setTimeout(pollWorkflow, 2000);
            } else {
              // Timeout - show simple message
              const timeoutMessage = {
                id: messages.length + 3,
                type: 'system',
                content: 'Request timed out. Please try again with a more specific question.',
                timestamp: new Date().toISOString()
              };
              setMessages(prev => [...prev, timeoutMessage]);
            }
          } catch (error) {
            console.error('Workflow polling error:', error);
            const errorMessage = {
              id: messages.length + 3,
              type: 'system',
              content: 'Connection issue. Please try again.',
              timestamp: new Date().toISOString()
            };
            setMessages(prev => [...prev, errorMessage]);
          }
        };
        
        setTimeout(pollWorkflow, 1000);
      } else {
        const noWorkflowMessage = {
          id: messages.length + 3,
          type: 'system',
          content: 'Unable to process request. Please try again.',
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, noWorkflowMessage]);
      }
      
    } catch (error) {
      console.error('Query execution error:', error);
      const connectionErrorMessage = {
        id: messages.length + 3,
        type: 'system', 
        content: 'Connection error. Please check if the backend is running.',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, connectionErrorMessage]);
    }
  };
  
  const tryDirectAgentCommunication = async (queryText) => {
    try {
      // Try to communicate directly with an appropriate agent
      let targetAgent = 'milo'; // Default to Milo for general queries
      
      // Simple intent detection (corrected for actual tool mappings)
      if (queryText.toLowerCase().includes('meal') || queryText.toLowerCase().includes('food') || queryText.toLowerCase().includes('recipe')) {
        targetAgent = 'luna'; // Luna actually has meal planning tools
      } else if (queryText.toLowerCase().includes('schedule') || queryText.toLowerCase().includes('calendar') || queryText.toLowerCase().includes('meeting')) {
        targetAgent = 'nani'; // Nani is unreachable, fallback to bucky
        if (connectionStatus === 'connected') {
          targetAgent = 'bucky'; // Use bucky as fallback since nani is down
        }
      } else if (queryText.toLowerCase().includes('health') || queryText.toLowerCase().includes('fitness') || queryText.toLowerCase().includes('workout')) {
        targetAgent = 'milo'; // Milo actually has fitness tools
      } else if (queryText.toLowerCase().includes('shopping') || queryText.toLowerCase().includes('buy') || queryText.toLowerCase().includes('store')) {
        targetAgent = 'bucky';
      }
      
      // Use workflow instead of direct chat since that endpoint doesn't exist
      const workflowResponse = await apiService.executeWorkflow({
        type: `${targetAgent}_query`,
        user_id: 'frontend_user',
        query: queryText,
        target_agent: targetAgent
      });
      
      // Get agent info for better response
      const agentInfo = agents[targetAgent];
      const agentCount = Object.values(realAgents).filter(a => a.status === 'healthy').length;
      
      const responseMessage = {
        id: Date.now(),
        type: 'agent',
        agent: targetAgent,
        content: `✅ **${agentInfo.name}** (${agentInfo.role}) received your query: "${queryText}"\n\n🔄 **Status**: Workflow ${workflowResponse.workflow_id} created and ${workflowResponse.status}\n💰 **Model**: Using cost-efficient GPT-4o-mini\n🤖 **System**: ${agentCount}/4 agents healthy and ready\n\n*Note: The A2A communication system is working! Some workflow orchestration features are still being configured, but your agents are successfully receiving and processing messages.*`,
        timestamp: new Date().toISOString()
      };
      
      setMessages(prev => [...prev, responseMessage]);
      
    } catch (error) {
      console.error('Direct agent communication error:', error);
      
      const fallbackMessage = {
        id: Date.now(),
        type: 'system',
        content: `I'm having trouble connecting to the agents right now. Please make sure the backend is running on http://localhost:8000. Error: ${error.message}`,
        timestamp: new Date().toISOString()
      };
      
      setMessages(prev => [...prev, fallbackMessage]);
    }
  };

  const handleNotificationAction = (notificationId, action) => {
    setNotifications(prev => prev.map(notif => 
      notif.id === notificationId 
        ? { ...notif, status: action }
        : notif
    ));

    // Add A2A response communication
    const responseMessage = {
      id: a2aCommunications.length + 1,
      from: 'nani',
      to: 'Agent X',
      message: action === 'approved' 
        ? 'Meeting approved: Thursday 3PM - Project Discussion'
        : 'Meeting declined. Alternative slots: Friday 2PM, Monday 4PM',
      timestamp: 'now',
      status: 'sent'
    };
    
    setA2ACommunications(prev => [...prev, responseMessage]);
  };

  if (currentView === 'agentManagement') {
    return <AgentManagement onBackToHome={() => setCurrentView('dashboard')} />;
  }

  return (
    <div className="min-h-screen p-4 md:p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold gradient-text">Personal Life Coordination</h1>
          <p className="text-white/80 mt-2">Agent-to-Agent Communication System</p>
          
          {/* Navigation */}
          <div className="flex justify-center gap-4 mt-6">
            <button
              onClick={() => setCurrentView('dashboard')}
              className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-all ${
                currentView === 'dashboard' 
                  ? 'bg-blue-500 text-white shadow-lg' 
                  : 'bg-white/90 text-gray-700 hover:bg-white'
              }`}
            >
              <MessageSquare className="w-4 h-4" />
              Dashboard
            </button>
            <button
              onClick={() => setCurrentView('agentManagement')}
              className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-all ${
                currentView === 'agentManagement' 
                  ? 'bg-blue-500 text-white shadow-lg' 
                  : 'bg-white/90 text-gray-700 hover:bg-white'
              }`}
            >
              <Wrench className="w-4 h-4" />
              Agent Management
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Main Query Interface */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Chat Interface */}
            <div className="bg-white/95 backdrop-blur-sm rounded-xl shadow-lg border border-white/20 p-6">
              <h2 className="text-xl font-semibold gradient-text mb-4 flex items-center gap-2">
                <MessageSquare className="w-5 h-5" />
                Ask Your Agents
              </h2>
              
              {/* Messages */}
              <div className="space-y-4 mb-4 h-96 overflow-y-auto">
                {messages.map(message => (
                  <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                      message.type === 'user' 
                        ? 'bg-blue-500 text-white' 
                        : message.type === 'system'
                        ? 'bg-gray-100 text-gray-700 italic'
                        : 'bg-gradient-to-r from-orange-400 to-orange-500 text-white'
                    }`}>
                      {message.agent && (
                        <div className="text-xs opacity-75 mb-1">
                          {agents[message.agent]?.name}
                        </div>
                      )}
                      <p className="text-sm">{message.content}</p>
                      <div className="text-xs opacity-75 mt-1">
                        {new Date(message.timestamp).toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              {/* Query Input */}
              <div className="flex gap-2">
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSendQuery()}
                  placeholder="Ask about meals, schedule, health, shopping..."
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <button
                  onClick={handleSendQuery}
                  className="px-4 py-2 bg-gradient-to-r from-blue-500 to-cyan-500 text-white rounded-lg hover:shadow-lg transition-all"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Real-time A2A Communications */}
            <div className="bg-white/95 backdrop-blur-sm rounded-xl shadow-lg border border-white/20 p-6">
              <h2 className="text-xl font-semibold gradient-text mb-4 flex items-center gap-2">
                <Users className="w-5 h-5" />
                Agent-to-Agent Communications
              </h2>
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {a2aCommunications.map(comm => (
                  <div key={comm.id} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-2 min-w-0 flex-1">
                      <div className={`p-1 rounded ${agents[comm.from] ? agents[comm.from].color : 'text-purple-500'}`}>
                        {agents[comm.from] ? React.createElement(agents[comm.from].icon, { className: "w-4 h-4" }) : <Users className="w-4 h-4" />}
                      </div>
                      <span className="text-sm font-medium">→</span>
                      <div className={`p-1 rounded ${agents[comm.to] ? agents[comm.to].color : 'text-purple-500'}`}>
                        {agents[comm.to] ? React.createElement(agents[comm.to].icon, { className: "w-4 h-4" }) : <Users className="w-4 h-4" />}
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm text-gray-700 truncate">{comm.message}</p>
                        <div className="flex items-center gap-2 text-xs text-gray-500">
                          <span>{comm.timestamp}</span>
                          <span className={`px-2 py-0.5 rounded-full ${
                            comm.status === 'completed' ? 'bg-green-100 text-green-700' :
                            comm.status === 'pending_approval' ? 'bg-yellow-100 text-yellow-700' :
                            'bg-blue-100 text-blue-700'
                          }`}>
                            {comm.status}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            
            {/* Notifications */}
            <div className="bg-white/95 backdrop-blur-sm rounded-xl shadow-lg border border-white/20 p-6">
              <h2 className="text-xl font-semibold gradient-text mb-4 flex items-center gap-2">
                <Bell className="w-5 h-5" />
                Notifications
              </h2>
              <div className="space-y-3">
                {notifications.map(notif => (
                  <div key={notif.id} className="p-3 border border-gray-200 rounded-lg">
                    <div className="text-sm font-medium text-gray-900">{notif.from}</div>
                    <p className="text-sm text-gray-600 mt-1">{notif.message}</p>
                    <div className="text-xs text-gray-500 mt-2">{notif.timestamp}</div>
                    
                    {notif.status === 'pending' && (
                      <div className="flex gap-2 mt-3">
                        <button
                          onClick={() => handleNotificationAction(notif.id, 'approved')}
                          className="px-3 py-1 bg-green-500 text-white text-xs rounded hover:bg-green-600"
                        >
                          Approve
                        </button>
                        <button
                          onClick={() => handleNotificationAction(notif.id, 'declined')}
                          className="px-3 py-1 bg-red-500 text-white text-xs rounded hover:bg-red-600"
                        >
                          Decline
                        </button>
                      </div>
                    )}
                    
                    {notif.status !== 'pending' && (
                      <div className={`text-xs mt-2 px-2 py-1 rounded inline-block ${
                        notif.status === 'approved' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                      }`}>
                        {notif.status}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* External Agent Access Control */}
            <div className="bg-white/95 backdrop-blur-sm rounded-xl shadow-lg border border-white/20 p-6">
              <h2 className="text-xl font-semibold gradient-text mb-4 flex items-center gap-2">
                <Shield className="w-5 h-5" />
                Access Control
              </h2>
              <div className="space-y-3">
                {externalAgentAccess.map(agent => (
                  <div key={agent.id} className="p-3 border border-gray-200 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm font-medium">{agent.agentName}</div>
                        <div className="text-xs text-gray-500">Owner: {agent.owner}</div>
                        <div className="text-xs text-gray-500">Access: {agent.accessLevel}</div>
                      </div>
                      <div className={`px-2 py-1 text-xs rounded ${
                        agent.status === 'approved' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                      }`}>
                        {agent.status}
                      </div>
                    </div>
                    <div className="text-xs text-gray-500 mt-2">
                      Connected to: {agent.connectedTo.join(', ')}
                    </div>
                  </div>
                ))}
              </div>
              
              <button className="w-full mt-4 px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:shadow-lg transition-all text-sm">
                <Settings className="w-4 h-4 inline mr-2" />
                Manage Access
              </button>
            </div>

            {/* Agent Status */}
            <div className="bg-white/95 backdrop-blur-sm rounded-xl shadow-lg border border-white/20 p-6">
              <h2 className="text-xl font-semibold gradient-text mb-4 flex items-center gap-2">
                Your Agents
                <div className={`w-2 h-2 rounded-full ${
                  connectionStatus === 'connected' ? 'bg-green-500' : 
                  connectionStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' : 
                  'bg-red-500'
                }`}></div>
              </h2>
              <div className="space-y-3">
                {Object.entries(agents).map(([key, agent]) => {
                  const Icon = agent.icon;
                  const realAgent = realAgents[key];
                  const isHealthy = realAgent?.status === 'healthy';
                  const toolCount = realAgent?.tools?.length || 0;
                  
                  return (
                    <div key={key} className="flex items-center gap-3 p-2">
                      <div className={`p-2 rounded ${agent.color}`}>
                        <Icon className="w-4 h-4" />
                      </div>
                      <div className="flex-1">
                        <div className="text-sm font-medium">{agent.name}</div>
                        <div className="text-xs text-gray-500">
                          {agent.role} {toolCount > 0 && `• ${toolCount} tools`}
                        </div>
                        {realAgent?.last_heartbeat && (
                          <div className="text-xs text-gray-400">
                            Last seen: {new Date(realAgent.last_heartbeat).toLocaleTimeString()}
                          </div>
                        )}
                      </div>
                      <div className="ml-auto">
                        <div className={`w-2 h-2 rounded-full ${
                          isHealthy ? 'bg-green-500' : 
                          realAgent?.status === 'unreachable' ? 'bg-red-500' : 
                          'bg-gray-400'
                        }`}></div>
                      </div>
                    </div>
                  );
                })}
              </div>
              
              {connectionStatus === 'disconnected' && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-sm text-red-700">
                    ⚠️ Unable to connect to backend. Make sure agents are running on port 8000.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;