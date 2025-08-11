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
  Download,
  AlertTriangle,
  Home
} from 'lucide-react';
import apiService from '../services/api';

const AgentManagement = ({ onBackToHome = () => window.location.reload() }) => {
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

  const openConfigModal = async (agentName, toolName) => {
    try {
      setLoading(true);
      
      // Use our direct configuration approach with proper schema
      const defaultConfig = getDefaultConfigForTool(toolName);
      const schema = getSchemaForTool(toolName);
      
      // Debug logging
      console.log('openConfigModal - toolName:', toolName);
      console.log('openConfigModal - defaultConfig:', defaultConfig);
      console.log('openConfigModal - schema:', schema);
      
      // Try to load existing configuration from the backend
      let existingConfig = {};
      try {
        const response = await fetch(`http://localhost:8000/agents/${agentName}/tools/${toolName}/config`);
        const data = await response.json();
        if (data.success && data.config) {
          existingConfig = data.config;
        }
      } catch (e) {
        console.log('Using default config due to:', e.message);
      }
      
      // Merge existing config with defaults, prioritizing existing values
      const mergedConfig = { ...defaultConfig, ...existingConfig };
      
      setSelectedTool({
        name: toolName,
        agent: agentName,
        description: `Configure ${toolName} tool settings`,
        config: mergedConfig,
        schema: schema
      });
      
      setConfigForm(mergedConfig);
      setShowConfigModal(true);
    } catch (error) {
      console.error('Failed to load tool configuration:', error);
      // Fallback to default configuration
      setSelectedTool({
        name: toolName,
        agent: agentName,
        description: `Configure ${toolName} tool settings`,
        config: getDefaultConfigForTool(toolName),
        schema: getSchemaForTool(toolName)
      });
      setConfigForm(getDefaultConfigForTool(toolName));
      setShowConfigModal(true);
    } finally {
      setLoading(false);
    }
  };

  const getDefaultConfigForTool = (toolName) => {
    const configs = {
      // ============ NANI SCHEDULER TOOLS ============
      calendar_manager: {
        google_client_id: '162356676608-79dcp2841e6tndjjbn1373bq1tv0p3ud.apps.googleusercontent.com',
        google_client_secret: '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',
        redirect_uri: 'http://localhost:8000/auth/google/callback',
        user_email: 'pyayalat@gmail.com'
      },
      scheduling_optimizer: {
        openai_api_key: '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',
        optimization_algorithm: 'genetic',
        max_optimization_time: 30
      },
      time_tracker: {
        storage_type: 'local',
        auto_backup: true,
        backup_frequency: 'daily'
      },
      focus_blocker: {
        block_social_media: true,
        block_news_sites: false,
        custom_blocked_sites: '',
        focus_duration: 25
      },
      timezone_handler: {
        primary_timezone: 'America/New_York',
        secondary_timezones: '',
        auto_detect_timezone: true
      },

      // ============ BUCKY SHOPPING TOOLS ============
      deal_finder: {
        groupon_api_key: '',
        honey_account: '',
        rakuten_api_key: '',
        ibotta_api_key: '',
        max_deals_per_search: 20
      },
      price_comparator: {
        kroger_api_key: '',
        walmart_api_key: '',
        target_api_key: '',
        costco_api_key: '',
        whole_foods_api_key: '',
        price_threshold: 10
      },
      shopping_optimizer: {
        openai_api_key: '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',
        preferred_stores: 'Kroger, Walmart, Target',
        max_travel_distance: 10,
        budget_optimization: true
      },
      pantry_tracker: {
        storage_type: 'local',
        expiration_alerts: true,
        alert_days_before: 3,
        barcode_scanner_api: ''
      },

      // ============ LUNA HEALTH TOOLS ============
      fitness_tracker: {
        fitbit_client_id: '',
        fitbit_client_secret: '',
        apple_health_enabled: false,
        garmin_api_key: '',
        strava_client_id: '',
        strava_client_secret: '',
        sync_frequency: 'daily'
      },
      health_analyzer: {
        openai_api_key: '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',
        health_data_retention: 365,
        enable_ai_insights: true,
        privacy_mode: 'balanced'
      },
      workout_planner: {
        openai_api_key: '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',
        default_workout_duration: 45,
        fitness_level: 'intermediate',
        preferred_workout_types: 'strength, cardio, yoga'
      },
      recovery_monitor: {
        track_sleep: true,
        track_hrv: true,
        track_stress: true,
        recovery_notifications: true
      },

      // ============ MILO NUTRITION TOOLS ============
      nutrition_analyzer: {
        openai_api_key: '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',
        usda_api_key: '',
        nutritionix_app_id: '',
        nutritionix_api_key: '',
        daily_calorie_target: 2000
      },
      meal_planner: {
        openai_api_key: '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',
        spoonacular_api_key: '',
        dietary_restrictions: '',
        meal_prep_days: 7,
        budget_per_meal: 10
      },
      recipe_engine: {
        openai_api_key: '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',
        recipe_api_key: '',
        cuisine_preferences: '',
        difficulty_level: 'medium',
        cooking_time_limit: 60
      }
    };
    return configs[toolName] || {};
  };

  const getSchemaForTool = (toolName) => {
    const schemas = {
      // ============ NANI SCHEDULER TOOLS ============
      calendar_manager: {
        google_client_id: { type: 'string', label: 'Google Client ID', required: true, placeholder: 'Your Google OAuth Client ID' },
        google_client_secret: { type: 'password', label: 'Google Client Secret', required: true, placeholder: 'Your Google OAuth Client Secret' },
        redirect_uri: { type: 'string', label: 'Redirect URI', required: true, default: 'http://localhost:8000/auth/google/callback' },
        user_email: { type: 'email', label: 'User Email', required: false, placeholder: 'Your Google account email' }
      },
      scheduling_optimizer: {
        openai_api_key: { type: 'password', label: 'OpenAI API Key', required: true, placeholder: 'sk-...' },
        optimization_algorithm: { type: 'select', label: 'Optimization Algorithm', options: ['genetic', 'greedy', 'dynamic_programming'], default: 'genetic' },
        max_optimization_time: { type: 'number', label: 'Max Optimization Time (seconds)', default: 30, min: 5, max: 300 }
      },
      time_tracker: {
        storage_type: { type: 'select', label: 'Storage Type', options: ['local', 'cloud'], default: 'local' },
        auto_backup: { type: 'boolean', label: 'Auto Backup', default: true },
        backup_frequency: { type: 'select', label: 'Backup Frequency', options: ['hourly', 'daily', 'weekly'], default: 'daily' }
      },
      focus_blocker: {
        block_social_media: { type: 'boolean', label: 'Block Social Media', default: true },
        block_news_sites: { type: 'boolean', label: 'Block News Sites', default: false },
        custom_blocked_sites: { type: 'string', label: 'Custom Blocked Sites (comma-separated)', placeholder: 'example.com, another-site.com' },
        focus_duration: { type: 'number', label: 'Default Focus Duration (minutes)', default: 25, min: 5, max: 180 }
      },
      timezone_handler: {
        primary_timezone: { type: 'string', label: 'Primary Timezone', required: true, placeholder: 'America/New_York', default: 'America/New_York' },
        secondary_timezones: { type: 'string', label: 'Secondary Timezones (comma-separated)', placeholder: 'Europe/London, Asia/Tokyo' },
        auto_detect_timezone: { type: 'boolean', label: 'Auto Detect Timezone', default: true }
      },

      // ============ BUCKY SHOPPING TOOLS ============
      deal_finder: {
        groupon_api_key: { type: 'password', label: 'Groupon API Key', required: false, placeholder: 'Your Groupon API key' },
        honey_account: { type: 'string', label: 'Honey Account Email', required: false, placeholder: 'your@email.com' },
        rakuten_api_key: { type: 'password', label: 'Rakuten API Key', required: false, placeholder: 'Your Rakuten API key' },
        ibotta_api_key: { type: 'password', label: 'Ibotta API Key', required: false, placeholder: 'Your Ibotta API key' },
        max_deals_per_search: { type: 'number', label: 'Max Deals Per Search', default: 20, min: 5, max: 100 }
      },
      price_comparator: {
        kroger_api_key: { type: 'password', label: 'Kroger API Key', required: false, placeholder: 'Your Kroger API key' },
        walmart_api_key: { type: 'password', label: 'Walmart API Key', required: false, placeholder: 'Your Walmart API key' },
        target_api_key: { type: 'password', label: 'Target API Key', required: false, placeholder: 'Your Target API key' },
        costco_api_key: { type: 'password', label: 'Costco API Key', required: false, placeholder: 'Your Costco API key' },
        whole_foods_api_key: { type: 'password', label: 'Whole Foods API Key', required: false, placeholder: 'Your Whole Foods API key' },
        price_threshold: { type: 'number', label: 'Price Alert Threshold (%)', default: 10, min: 1, max: 50 }
      },
      shopping_optimizer: {
        openai_api_key: { type: 'password', label: 'OpenAI API Key', required: true, placeholder: 'sk-...' },
        preferred_stores: { type: 'string', label: 'Preferred Stores (comma-separated)', placeholder: 'Kroger, Walmart, Target' },
        max_travel_distance: { type: 'number', label: 'Max Travel Distance (miles)', default: 10, min: 1, max: 50 },
        budget_optimization: { type: 'boolean', label: 'Enable Budget Optimization', default: true }
      },
      pantry_tracker: {
        storage_type: { type: 'select', label: 'Storage Type', options: ['local', 'cloud'], default: 'local' },
        expiration_alerts: { type: 'boolean', label: 'Expiration Alerts', default: true },
        alert_days_before: { type: 'number', label: 'Alert Days Before Expiration', default: 3, min: 1, max: 30 },
        barcode_scanner_api: { type: 'password', label: 'Barcode Scanner API Key', required: false, placeholder: 'Your barcode API key' }
      },

      // ============ LUNA HEALTH TOOLS ============
      fitness_tracker: {
        fitbit_client_id: { type: 'string', label: 'Fitbit Client ID', required: false, placeholder: 'Your Fitbit Client ID' },
        fitbit_client_secret: { type: 'password', label: 'Fitbit Client Secret', required: false, placeholder: 'Your Fitbit Client Secret' },
        apple_health_enabled: { type: 'boolean', label: 'Apple Health Integration', default: false },
        garmin_api_key: { type: 'password', label: 'Garmin API Key', required: false, placeholder: 'Your Garmin API key' },
        strava_client_id: { type: 'string', label: 'Strava Client ID', required: false, placeholder: 'Your Strava Client ID' },
        strava_client_secret: { type: 'password', label: 'Strava Client Secret', required: false, placeholder: 'Your Strava Client Secret' },
        sync_frequency: { type: 'select', label: 'Data Sync Frequency', options: ['realtime', 'hourly', 'daily'], default: 'daily' }
      },
      health_analyzer: {
        openai_api_key: { type: 'password', label: 'OpenAI API Key', required: true, placeholder: 'sk-...' },
        health_data_retention: { type: 'number', label: 'Health Data Retention (days)', default: 365, min: 30, max: 1825 },
        enable_ai_insights: { type: 'boolean', label: 'Enable AI Health Insights', default: true },
        privacy_mode: { type: 'select', label: 'Privacy Mode', options: ['strict', 'balanced', 'open'], default: 'balanced' }
      },
      workout_planner: {
        openai_api_key: { type: 'password', label: 'OpenAI API Key', required: true, placeholder: 'sk-...' },
        default_workout_duration: { type: 'number', label: 'Default Workout Duration (minutes)', default: 45, min: 15, max: 180 },
        fitness_level: { type: 'select', label: 'Default Fitness Level', options: ['beginner', 'intermediate', 'advanced'], default: 'intermediate' },
        preferred_workout_types: { type: 'string', label: 'Preferred Workout Types (comma-separated)', placeholder: 'strength, cardio, yoga' }
      },
      recovery_monitor: {
        track_sleep: { type: 'boolean', label: 'Track Sleep Patterns', default: true },
        track_hrv: { type: 'boolean', label: 'Track Heart Rate Variability', default: true },
        track_stress: { type: 'boolean', label: 'Track Stress Levels', default: true },
        recovery_notifications: { type: 'boolean', label: 'Recovery Notifications', default: true }
      },

      // ============ MILO NUTRITION TOOLS ============
      nutrition_analyzer: {
        openai_api_key: { type: 'password', label: 'OpenAI API Key', required: true, placeholder: 'sk-...' },
        usda_api_key: { type: 'password', label: 'USDA FoodData API Key', required: false, placeholder: 'Your USDA API key' },
        nutritionix_app_id: { type: 'string', label: 'Nutritionix App ID', required: false, placeholder: 'Your Nutritionix App ID' },
        nutritionix_api_key: { type: 'password', label: 'Nutritionix API Key', required: false, placeholder: 'Your Nutritionix API key' },
        daily_calorie_target: { type: 'number', label: 'Daily Calorie Target', default: 2000, min: 1000, max: 5000 }
      },
      meal_planner: {
        openai_api_key: { type: 'password', label: 'OpenAI API Key', required: true, placeholder: 'sk-...' },
        spoonacular_api_key: { type: 'password', label: 'Spoonacular API Key', required: false, placeholder: 'Your Spoonacular API key' },
        dietary_restrictions: { type: 'string', label: 'Dietary Restrictions (comma-separated)', placeholder: 'vegetarian, gluten-free, dairy-free' },
        meal_prep_days: { type: 'number', label: 'Meal Prep Days', default: 7, min: 1, max: 14 },
        budget_per_meal: { type: 'number', label: 'Budget Per Meal ($)', default: 10, min: 1, max: 100 }
      },
      recipe_engine: {
        openai_api_key: { type: 'password', label: 'OpenAI API Key', required: true, placeholder: 'sk-...' },
        recipe_api_key: { type: 'password', label: 'Recipe API Key', required: false, placeholder: 'Your recipe API key' },
        cuisine_preferences: { type: 'string', label: 'Cuisine Preferences (comma-separated)', placeholder: 'italian, asian, mexican' },
        difficulty_level: { type: 'select', label: 'Recipe Difficulty Level', options: ['easy', 'medium', 'hard', 'any'], default: 'medium' },
        cooking_time_limit: { type: 'number', label: 'Cooking Time Limit (minutes)', default: 60, min: 10, max: 300 }
      }
    };
    return schemas[toolName] || {};
  };

  const renderConfigurationForm = () => {
    if (!selectedTool?.name) return null;
    
    const schema = selectedTool.schema || {};
    
    // Debug logging
    console.log('renderConfigurationForm - selectedTool:', selectedTool);
    console.log('renderConfigurationForm - schema:', schema);
    console.log('renderConfigurationForm - schema entries:', Object.entries(schema));
    
    if (Object.keys(schema).length === 0) {
      return (
        <div className="space-y-4">
          <h3 className="font-semibold text-gray-800">Configuration Settings</h3>
          <p className="text-red-500">No configuration schema found for {selectedTool.name}</p>
        </div>
      );
    }
    
    return (
      <div className="space-y-4">
        <h3 className="font-semibold text-gray-800">Configuration Settings</h3>
        
        {Object.entries(schema).map(([key, field]) => (
          <div key={key} className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              {field.label}
              {field.required && <span className="text-red-500 ml-1">*</span>}
            </label>
            
            {field.type === 'select' ? (
              <select
                value={configForm[key] || field.default || ''}
                onChange={(e) => setConfigForm(prev => ({ ...prev, [key]: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Select...</option>
                {field.options?.map(option => (
                  <option key={option} value={option}>{option}</option>
                ))}
              </select>
            ) : field.type === 'boolean' ? (
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={configForm[key] !== undefined ? configForm[key] : field.default}
                  onChange={(e) => setConfigForm(prev => ({ ...prev, [key]: e.target.checked }))}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <span className="text-sm text-gray-600">Enable</span>
              </label>
            ) : field.type === 'number' ? (
              <input
                type="number"
                min={field.min}
                max={field.max}
                value={configForm[key] || field.default || ''}
                onChange={(e) => setConfigForm(prev => ({ ...prev, [key]: parseInt(e.target.value) || '' }))}
                placeholder={field.placeholder}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            ) : (
              <input
                type={field.type === 'password' ? 'password' : field.type === 'email' ? 'email' : 'text'}
                value={configForm[key] || ''}
                onChange={(e) => setConfigForm(prev => ({ ...prev, [key]: e.target.value }))}
                placeholder={field.placeholder}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            )}
            
            {field.type === 'password' && configForm[key] && (
              <div className="flex items-center gap-2 text-sm text-green-600">
                <CheckCircle className="w-4 h-4" />
                API key configured
              </div>
            )}
          </div>
        ))}
        
        {selectedTool.name === 'calendar_manager' && (
          <div className="bg-amber-50 p-4 rounded-lg">
            <h4 className="font-medium text-amber-800 mb-2">Setup Instructions:</h4>
            <ol className="text-sm text-amber-700 space-y-1">
              <li>1. Go to <a href="https://console.developers.google.com/" target="_blank" rel="noreferrer" className="underline">Google Cloud Console</a></li>
              <li>2. Enable the Google Calendar API</li>
              <li>3. Create OAuth 2.0 credentials</li>
              <li>4. Add {window.location.origin}/auth/google/callback as authorized redirect URI</li>
              <li>5. Copy the Client ID and Secret here</li>
            </ol>
          </div>
        )}
      </div>
    );
  };

  const validateConfiguration = (config, schema) => {
    const errors = [];
    
    for (const [key, field] of Object.entries(schema)) {
      const value = config[key];
      
      // Check required fields
      if (field.required && (!value || value.toString().trim() === '')) {
        errors.push(`${field.label} is required`);
        continue;
      }
      
      if (value && value.toString().trim() !== '') {
        // Validate specific field types
        if (field.type === 'email' && !value.includes('@')) {
          errors.push(`${field.label} must be a valid email address`);
        }
        
        if (field.type === 'password' && key.includes('openai_api_key') && !value.startsWith('sk-')) {
          errors.push(`${field.label} must start with 'sk-'`);
        }
        
        if (field.type === 'number') {
          const num = parseInt(value);
          if (isNaN(num)) {
            errors.push(`${field.label} must be a valid number`);
          } else {
            if (field.min && num < field.min) {
              errors.push(`${field.label} must be at least ${field.min}`);
            }
            if (field.max && num > field.max) {
              errors.push(`${field.label} must be at most ${field.max}`);
            }
          }
        }
        
        if (key === 'google_client_id' && !value.includes('.apps.googleusercontent.com')) {
          errors.push(`${field.label} must be a valid Google OAuth Client ID ending in '.apps.googleusercontent.com'`);
        }
        
        if (key === 'google_client_secret' && !value.startsWith('GOCSPX-')) {
          errors.push(`${field.label} must be a valid Google OAuth Client Secret starting with 'GOCSPX-'`);
        }
      }
    }
    
    return errors;
  };

  const saveConfiguration = async () => {
    if (!selectedTool) return;
    
    // Validate configuration before saving
    const errors = validateConfiguration(configForm, selectedTool.schema);
    if (errors.length > 0) {
      alert(`Configuration validation failed:\n\n${errors.join('\n')}`);
      return;
    }
    
    try {
      setLoading(true);
      console.log('Saving configuration for:', selectedTool.agent, selectedTool.name);
      console.log('Configuration data:', configForm);
      
      const response = await fetch(
        `http://localhost:8000/agents/${selectedTool.agent}/tools/${selectedTool.name}/config`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ config: configForm })
        }
      );
      
      const data = await response.json();
      console.log('Save response:', data);
      
      if (data.success) {
        alert('✅ Configuration saved successfully!');
        setShowConfigModal(false);
        // Refresh agent data to show updated configuration
        fetchAgents();
      } else {
        alert(`❌ Failed to save configuration:\n${data.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Failed to save configuration:', error);
      alert(`❌ Failed to save configuration:\n${error.message}\n\nCheck console for details.`);
    } finally {
      setLoading(false);
    }
  };

  const testConfiguration = async () => {
    if (!selectedTool) return;
    
    // Validate configuration before testing
    const errors = validateConfiguration(configForm, selectedTool.schema);
    if (errors.length > 0) {
      alert(`Configuration validation failed:\n\n${errors.join('\n')}\n\nPlease fix these issues before testing.`);
      return;
    }
    
    try {
      setLoading(true);
      console.log('Testing configuration for:', selectedTool.agent, selectedTool.name);
      console.log('Configuration data:', configForm);
      
      const response = await fetch(
        `http://localhost:8000/agents/${selectedTool.agent}/tools/${selectedTool.name}/test`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ config: configForm })
        }
      );
      
      const data = await response.json();
      console.log('Test response:', data);
      
      if (data.success) {
        const resultsText = Object.entries(data.test_results)
          .map(([key, value]) => `• ${key}: ${value}`)
          .join('\n');
        alert(`✅ Configuration Test Successful!\n\n${resultsText}`);
      } else {
        alert(`❌ Configuration Test Failed:\n\n${data.error}`);
      }
    } catch (error) {
      console.error('Failed to test configuration:', error);
      alert(`❌ Failed to test configuration:\n${error.message}\n\nCheck console for details.`);
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
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold">Agent Management & Configuration</h2>
          <button
            onClick={onBackToHome}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 flex items-center gap-2 transition-colors"
          >
            <Home className="w-4 h-4" />
            Back to Home
          </button>
        </div>
        
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
          <button
            onClick={onBackToHome}
            className="px-3 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 flex items-center gap-2"
          >
            <Home className="w-4 h-4" />
            Home
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
                    
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        openConfigModal(selectedAgent.name, tool.name);
                      }}
                      className="px-2 py-1 bg-green-100 text-green-700 rounded text-sm hover:bg-green-200 flex items-center gap-1"
                    >
                      <Key className="w-3 h-3" />
                      Configure
                    </button>
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

      {/* Configuration Modal */}
      {showConfigModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold">Configure {selectedTool?.name}</h2>
              <button
                onClick={() => setShowConfigModal(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                <AlertTriangle className="w-6 h-6" />
              </button>
            </div>

            {selectedTool && (
              <div className="space-y-6">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h3 className="font-semibold text-blue-800 mb-2">{selectedTool.name}</h3>
                  <p className="text-blue-700 text-sm">{selectedTool.description}</p>
                </div>

                {/* API Configuration */}
                {renderConfigurationForm()}

                {/* Action Buttons */}
                <div className="flex justify-end gap-3 pt-4 border-t">
                  <button
                    onClick={() => {
                      console.log('Cancel clicked');
                      setShowConfigModal(false);
                    }}
                    className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => {
                      console.log('Save clicked - configForm:', configForm);
                      saveConfiguration();
                    }}
                    disabled={loading}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
                  >
                    {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                    Save Configuration
                  </button>
                  <button
                    onClick={() => {
                      console.log('Test clicked - configForm:', configForm);
                      testConfiguration();
                    }}
                    disabled={loading}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
                  >
                    <TestTube className="w-4 h-4" />
                    Test
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentManagement;