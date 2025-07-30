// Complete API service for communicating with the backend
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
    this.timeout = 10000; // 10 seconds
  }

  async request(endpoint, options = {}) {
    const url = endpoint.startsWith('http') ? endpoint : `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      timeout: this.timeout,
      ...options,
    };

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        ...config,
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        const errorText = await response.text().catch(() => 'Unknown error');
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }
      
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      } else {
        return await response.text();
      }
    } catch (error) {
      clearTimeout(timeoutId);
      if (error.name === 'AbortError') {
        throw new Error('Request timeout');
      }
      console.error(`API request failed: ${error.message}`);
      throw error;
    }
  }

  // ============================================================================
  // SYSTEM & GATEWAY APIs
  // ============================================================================

  // Gateway health check
  async getSystemHealth() {
    try {
      return await this.request('/health');
    } catch (error) {
      return { status: 'error', error: error.message };
    }
  }

  // Get system metrics
  async getSystemMetrics() {
    try {
      return await this.request('/api/v1/metrics');
    } catch (error) {
      return {
        totalWorkflows: 0,
        successRate: 0,
        avgResponseTime: 0,
        agentCoordinations: 0,
        error: error.message
      };
    }
  }

  // Get system statistics
  async getSystemStats() {
    try {
      return await this.request('/api/v1/system/stats');
    } catch (error) {
      return {
        disk_usage: 0,
        memory_usage: 0,
        uptime: '0 days',
        last_backup: null,
        error: error.message
      };
    }
  }

  // ============================================================================
  // AGENT APIs
  // ============================================================================

  // Get specific agent status
  async getAgentStatus(agentName) {
    try {
      return await this.request(`/api/v1/agents/${agentName}/status`);
    } catch (error) {
      // Fallback: try direct agent connection
      return await this.getAgentStatusDirect(agentName);
    }
  }

  // Get agent status directly from agent
  async getAgentStatusDirect(agentName) {
    const agentPorts = {
      nani: 8001,
      luna: 8004,
      bucky: 8002,
      milo: 8003
    };
    
    const port = agentPorts[agentName];
    if (!port) {
      throw new Error(`Unknown agent: ${agentName}`);
    }

    try {
      return await this.request(`http://localhost:${port}/health`);
    } catch (error) {
      return {
        status: 'offline',
        agent: agentName,
        error: error.message,
        timestamp: new Date().toISOString()
      };
    }
  }

  // Get all agents status
  async getAllAgentsStatus() {
    const agents = ['nani', 'luna', 'bucky', 'milo'];
    const statusPromises = agents.map(agent => 
      this.getAgentStatus(agent).catch(error => ({
        agent,
        status: 'error',
        error: error.message
      }))
    );
    
    const results = await Promise.all(statusPromises);
    
    // Convert array to object
    const agentStatuses = {};
    results.forEach((result, index) => {
      agentStatuses[agents[index]] = result;
    });
    
    return agentStatuses;
  }

  // Get agent tools
  async getAgentTools(agentName) {
    const agentPorts = {
      nani: 8001,
      luna: 8004,
      bucky: 8002,
      milo: 8003
    };
    
    const port = agentPorts[agentName];
    if (!port) {
      throw new Error(`Unknown agent: ${agentName}`);
    }

    try {
      return await this.request(`http://localhost:${port}/tools`);
    } catch (error) {
      // Return mock tools for demo
      return {
        tools: [
          {
            name: 'mock_tool',
            description: `Mock tool for ${agentName} (agent offline)`,
            parameters: { 
              type: 'object', 
              properties: { 
                action: { type: 'string', enum: ['test', 'demo'] } 
              } 
            },
            returns: { type: 'object' }
          }
        ]
      };
    }
  }

  // Execute agent tool
  async executeAgentTool(agentName, toolName, parameters) {
    const agentPorts = {
      nani: 8001,
      luna: 8004,
      bucky: 8002,
      milo: 8003
    };
    
    const port = agentPorts[agentName];
    if (!port) {
      throw new Error(`Unknown agent: ${agentName}`);
    }

    try {
      return await this.request(`http://localhost:${port}/execute/${toolName}`, {
        method: 'POST',
        body: JSON.stringify({
          parameters,
          context: {
            user_id: 'demo_user',
            session_id: `session_${Date.now()}`,
            permissions: ['read', 'write'],
            timestamp: new Date().toISOString()
          }
        }),
      });
    } catch (error) {
      // Return mock response for demo
      return {
        success: false,
        error: `Agent ${agentName} offline: ${error.message}`,
        result: null,
        execution_time: 0,
        mock: true
      };
    }
  }

  // ============================================================================
  // WORKFLOW APIs
  // ============================================================================

  // Execute workflow
  async executeWorkflow(workflowData) {
    try {
      return await this.request('/api/v1/workflow', {
        method: 'POST',
        body: JSON.stringify({
          ...workflowData,
          timestamp: new Date().toISOString(),
          user_id: 'demo_user'
        }),
      });
    } catch (error) {
      // Return mock workflow for demo
      return {
        workflow_id: `wf_${Date.now()}`,
        status: 'initiated',
        message: `Workflow started (mock): ${error.message}`,
        mock: true
      };
    }
  }

  // Get workflow status
  async getWorkflowStatus(workflowId) {
    try {
      return await this.request(`/api/v1/workflow/${workflowId}/status`);
    } catch (error) {
      return {
        workflow_id: workflowId,
        status: 'unknown',
        error: error.message
      };
    }
  }

  // Get all workflows
  async getAllWorkflows() {
    try {
      return await this.request('/api/v1/workflows');
    } catch (error) {
      return {
        workflows: [],
        error: error.message
      };
    }
  }

  // Cancel workflow
  async cancelWorkflow(workflowId) {
    try {
      return await this.request(`/api/v1/workflow/${workflowId}/cancel`, {
        method: 'POST'
      });
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  // ============================================================================
  // SETTINGS APIs
  // ============================================================================

  // Get system settings
  async getSystemSettings() {
    try {
      return await this.request('/api/v1/settings');
    } catch (error) {
      // Return default settings structure
      return {
        success: true,
        settings: {
          general: {
            theme: 'light',
            language: 'en',
            timezone: 'America/New_York',
            auto_refresh: true,
            refresh_interval: 5
          },
          notifications: {
            email: true,
            push: true,
            workflow_completed: true,
            agent_offline: true,
            system_alerts: true,
            daily_summary: false
          },
          agents: {
            auto_restart: true,
            max_retries: 3,
            timeout_seconds: 30,
            log_level: 'INFO',
            health_check_interval: 30,
            concurrent_workflows: 5
          },
          api: {
            openai_key: '',
            google_calendar: false,
            google_calendar_id: '',
            fitbit: false,
            fitbit_token: '',
            spoonacular: false,
            spoonacular_key: ''
          },
          system: {
            auto_backup: true,
            backup_interval: 'daily',
            max_logs_days: 30,
            performance_monitoring: true,
            debug_mode: false,
            data_retention_days: 90
          }
        }
      };
    }
  }

  // Save system settings
  async saveSystemSettings(settings) {
    try {
      return await this.request('/api/v1/settings', {
        method: 'POST',
        body: JSON.stringify({
          settings,
          timestamp: new Date().toISOString()
        })
      });
    } catch (error) {
      // Mock successful save for demo
      console.warn('Settings save failed, using local storage:', error.message);
      localStorage.setItem('plc_settings', JSON.stringify(settings));
      return {
        success: true,
        message: 'Settings saved locally (backend offline)'
      };
    }
  }

  // Reset system settings
  async resetSystemSettings() {
    try {
      return await this.request('/api/v1/settings/reset', {
        method: 'POST'
      });
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  // Test API connection
  async testAPIConnection(apiType, apiSettings) {
    try {
      return await this.request('/api/v1/settings/test-connection', {
        method: 'POST',
        body: JSON.stringify({
          api_type: apiType,
          settings: apiSettings
        })
      });
    } catch (error) {
      // Mock test for demo
      const mockResults = {
        openai: { success: false, error: 'OpenAI API key not configured' },
        google_calendar: { success: false, error: 'Google Calendar not configured' },
        fitbit: { success: false, error: 'Fitbit token not configured' }
      };
      
      return mockResults[apiType] || { success: false, error: error.message };
    }
  }

  // ============================================================================
  // SYSTEM MANAGEMENT APIs
  // ============================================================================

  // Clear system logs
  async clearSystemLogs() {
    try {
      return await this.request('/api/v1/system/logs/clear', {
        method: 'POST'
      });
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  // Restart all agents
  async restartAllAgents() {
    try {
      return await this.request('/api/v1/agents/restart-all', {
        method: 'POST'
      });
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  // Restart specific agent
  async restartAgent(agentName) {
    try {
      return await this.request(`/api/v1/agents/${agentName}/restart`, {
        method: 'POST'
      });
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  // Reset database (dangerous operation)
  async resetDatabase() {
    try {
      return await this.request('/api/v1/system/database/reset', {
        method: 'POST',
        headers: {
          'X-Confirm-Reset': 'true'
        }
      });
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  // ============================================================================
  // A2A COMMUNICATION APIs
  // ============================================================================

  // Send A2A message
  async sendA2AMessage(fromAgent, toAgent, intent, payload) {
    try {
      return await this.request('/api/v1/a2a/send', {
        method: 'POST',
        body: JSON.stringify({
          from_agent: fromAgent,
          to_agent: toAgent,
          intent,
          payload,
          timestamp: new Date().toISOString(),
          correlation_id: `corr_${Date.now()}`
        })
      });
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  // Get A2A communication history
  async getA2ACommunications(limit = 50) {
    try {
      return await this.request(`/api/v1/a2a/history?limit=${limit}`);
    } catch (error) {
      return {
        communications: [],
        error: error.message
      };
    }
  }

  // ============================================================================
  // MONITORING & ANALYTICS APIs
  // ============================================================================

  // Get performance metrics
  async getPerformanceMetrics(timeRange = '24h') {
    try {
      return await this.request(`/api/v1/metrics/performance?range=${timeRange}`);
    } catch (error) {
      return {
        metrics: [],
        error: error.message
      };
    }
  }

  // Get system logs
  async getSystemLogs(level = 'INFO', limit = 100) {
    try {
      return await this.request(`/api/v1/logs?level=${level}&limit=${limit}`);
    } catch (error) {
      return {
        logs: [],
        error: error.message
      };
    }
  }

  // Export data
  async exportData(dataType = 'all') {
    try {
      const response = await fetch(`${this.baseURL}/api/v1/export/${dataType}`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error(`Export failed: ${response.status}`);
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `plc-export-${dataType}-${new Date().toISOString().split('T')[0]}.json`;
      a.click();
      window.URL.revokeObjectURL(url);
      
      return { success: true, message: 'Export completed' };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  // ============================================================================
  // UTILITY METHODS
  // ============================================================================

  // Check if backend is available
  async checkBackendAvailability() {
    try {
      const response = await this.getSystemHealth();
      return response.status === 'healthy';
    } catch (error) {
      return false;
    }
  }

  // Get connection status
  getConnectionStatus() {
    return {
      baseURL: this.baseURL,
      timeout: this.timeout,
      timestamp: new Date().toISOString()
    };
  }

  // Set timeout
  setTimeout(timeout) {
    this.timeout = timeout;
  }

  // Set base URL
  setBaseURL(url) {
    this.baseURL = url;
  }
}

// Create singleton instance
const apiService = new ApiService();

export default apiService;