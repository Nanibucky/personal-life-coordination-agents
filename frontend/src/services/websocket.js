// WebSocket service for real-time communication with agents
class WebSocketService {
    constructor() {
      this.ws = null;
      this.reconnectAttempts = 0;
      this.maxReconnectAttempts = 5;
      this.reconnectInterval = 1000;
      this.listeners = new Map();
      this.isConnected = false;
    }
  
    connect(url = 'ws://localhost:8000/ws') {
      try {
        this.ws = new WebSocket(url);
        
        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.isConnected = true;
          this.reconnectAttempts = 0;
          this.emit('connected');
        };
  
        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };
  
        this.ws.onclose = () => {
          console.log('WebSocket disconnected');
          this.isConnected = false;
          this.emit('disconnected');
          this.attemptReconnect();
        };
  
        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.emit('error', error);
        };
  
      } catch (error) {
        console.error('Failed to connect WebSocket:', error);
        this.attemptReconnect();
      }
    }
  
    disconnect() {
      if (this.ws) {
        this.ws.close();
        this.ws = null;
        this.isConnected = false;
      }
    }
  
    attemptReconnect() {
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++;
        console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
        
        setTimeout(() => {
          this.connect();
        }, this.reconnectInterval * this.reconnectAttempts);
      } else {
        console.error('Max reconnection attempts reached');
        this.emit('maxReconnectAttemptsReached');
      }
    }
  
    send(data) {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify(data));
      } else {
        console.warn('WebSocket not connected, message not sent:', data);
      }
    }
  
    handleMessage(data) {
      const { type, payload } = data;
      
      switch (type) {
        case 'agent_status_update':
          this.emit('agentStatusUpdate', payload);
          break;
        case 'workflow_progress':
          this.emit('workflowProgress', payload);
          break;
        case 'a2a_communication':
          this.emit('a2aCommunication', payload);
          break;
        case 'system_metrics':
          this.emit('systemMetrics', payload);
          break;
        case 'error':
          this.emit('error', payload);
          break;
        default:
          console.log('Unknown message type:', type, payload);
      }
    }
  
    // Event emitter methods
    on(event, callback) {
      if (!this.listeners.has(event)) {
        this.listeners.set(event, []);
      }
      this.listeners.get(event).push(callback);
    }
  
    off(event, callback) {
      if (this.listeners.has(event)) {
        const callbacks = this.listeners.get(event);
        const index = callbacks.indexOf(callback);
        if (index > -1) {
          callbacks.splice(index, 1);
        }
      }
    }
  
    emit(event, data) {
      if (this.listeners.has(event)) {
        this.listeners.get(event).forEach(callback => {
          try {
            callback(data);
          } catch (error) {
            console.error('Error in event listener:', error);
          }
        });
      }
    }
  
    // Specific methods for agent communication
    subscribeToAgent(agentName) {
      this.send({
        type: 'subscribe',
        payload: { agent: agentName }
      });
    }
  
    unsubscribeFromAgent(agentName) {
      this.send({
        type: 'unsubscribe',
        payload: { agent: agentName }
      });
    }
  
    requestAgentStatus(agentName) {
      this.send({
        type: 'get_agent_status',
        payload: { agent: agentName }
      });
    }
  
    executeWorkflow(workflowData) {
      this.send({
        type: 'execute_workflow',
        payload: workflowData
      });
    }
  
    getConnectionStatus() {
      return {
        connected: this.isConnected,
        reconnectAttempts: this.reconnectAttempts,
        maxReconnectAttempts: this.maxReconnectAttempts
      };
    }
  }
  
  // Create singleton instance
  const webSocketService = new WebSocketService();
  
  export default webSocketService;