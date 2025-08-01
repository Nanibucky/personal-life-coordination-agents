// Complete API service for communicating with the LangChain backend
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

  // Get all agents status
  async getAllAgentsStatus() {
    try {
      return await this.request('/agents');
    } catch (error) {
      return {
        agents: {},
        total_agents: 0,
        error: error.message
      };
    }
  }

  // ============================================================================
  // AGENT APIs
  // ============================================================================

  // Chat directly with a specific agent
  async chatWithAgent(agentName, message, context = null) {
    try {
      const response = await this.request(`/agents/${agentName}/chat`, {
        method: 'POST',
        body: JSON.stringify({
          agent_name: agentName,
          message: message,
          context: context
        })
      });
      return response;
    } catch (error) {
      return {
        agent_name: agentName,
        response: `Error: ${error.message}`,
        tools_used: [],
        execution_time: 0
      };
    }
  }

  // Get specific agent status
  async getAgentStatusDirect(agentName) {
    try {
      const allAgents = await this.getAllAgentsStatus();
      return allAgents.agents[agentName] || { error: 'Agent not found' };
    } catch (error) {
      return { error: error.message };
    }
  }

  // ============================================================================
  // WORKFLOW APIs
  // ============================================================================

  // Execute a workflow
  async executeWorkflow(workflowData) {
    try {
      return await this.request('/workflow', {
        method: 'POST',
        body: JSON.stringify(workflowData)
      });
    } catch (error) {
      return {
        workflow_id: `wf_${Date.now()}`,
        status: 'failed',
        message: `Error: ${error.message}`,
        agents_involved: [],
        estimated_duration: 0
      };
    }
  }

  // Get workflow status
  async getWorkflowStatus(workflowId) {
    try {
      return await this.request(`/workflows/${workflowId}`);
    } catch (error) {
      return { error: error.message };
    }
  }

  // Get all workflows
  async getAllWorkflows() {
    try {
      return await this.request('/workflows');
    } catch (error) {
      return {
        active_workflows: {},
        total_count: 0,
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
      return await this.request('/a2a/message', {
        method: 'POST',
        body: JSON.stringify({
          from_agent: fromAgent,
          to_agent: toAgent,
          intent: intent,
          payload: payload,
          session_id: `session_${Date.now()}`
        })
      });
    } catch (error) {
      return {
        success: false,
        error: error.message,
        message_id: null
      };
    }
  }

  // Broadcast A2A message
  async broadcastA2AMessage(fromAgent, intent, payload) {
    try {
      return await this.request('/a2a/broadcast', {
        method: 'POST',
        body: JSON.stringify({
          from_agent: fromAgent,
          intent: intent,
          payload: payload,
          session_id: `session_${Date.now()}`
        })
      });
    } catch (error) {
      return {
        responses: [],
        total_agents: 0,
        error: error.message
      };
    }
  }

  // Get A2A message history
  async getA2ACommunications(limit = 50) {
    try {
      return await this.request(`/a2a/history?limit=${limit}`);
    } catch (error) {
      return {
        messages: [],
        total_messages: 0,
        error: error.message
      };
    }
  }

  // Clear A2A message history
  async clearA2AHistory() {
    try {
      return await this.request('/a2a/history', {
        method: 'DELETE'
      });
    } catch (error) {
      return { error: error.message };
    }
  }

  // ============================================================================
  // SYSTEM MANAGEMENT APIs
  // ============================================================================

  // Get system settings
  async getSystemSettings() {
    try {
      const response = await this.request('/api/v1/system/settings');
      return response;
    } catch (error) {
      return {
        success: false,
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
            spoonacular_key: '',
            kroger: false,
            kroger_key: ''
          },
          system: {
            auto_backup: true,
            backup_interval: 'daily',
            max_logs_days: 30,
            performance_monitoring: true,
            debug_mode: false,
            data_retention_days: 90
          }
        },
        error: error.message
      };
    }
  }

  // Save system settings
  async saveSystemSettings(settings) {
    try {
      const response = await this.request('/api/v1/system/settings', {
        method: 'PUT',
        body: JSON.stringify(settings)
      });
      return response;
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  // Reset system settings
  async resetSystemSettings() {
    try {
      const response = await this.request('/api/v1/system/settings/reset', {
        method: 'POST'
      });
      return response;
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  // Test API connection
  async testAPIConnection(apiType, apiSettings) {
    try {
      const response = await this.request('/api/v1/system/test-connection', {
        method: 'POST',
        body: JSON.stringify({
          type: apiType,
          settings: apiSettings
        })
      });
      return response;
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  // Clear system logs
  async clearSystemLogs() {
    try {
      const response = await this.request('/api/v1/system/logs/clear', {
        method: 'DELETE'
      });
      return response;
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  // Restart all agents
  async restartAllAgents() {
    try {
      const response = await this.request('/api/v1/system/restart-agents', {
        method: 'POST'
      });
      return response;
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  // Restart specific agent
  async restartAgent(agentName) {
    try {
      const response = await this.request(`/api/v1/system/restart-agent/${agentName}`, {
        method: 'POST'
      });
      return response;
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  // Reset database
  async resetDatabase() {
    try {
      const response = await this.request('/api/v1/system/reset-database', {
        method: 'POST'
      });
      return response;
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  // Get system statistics
  async getSystemStats() {
    try {
      const response = await this.request('/api/v1/system/stats');
      return response;
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
  // UTILITY METHODS
  // ============================================================================

  // Check backend availability
  async checkBackendAvailability() {
    try {
      const health = await this.getSystemHealth();
      return health.status === 'healthy';
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