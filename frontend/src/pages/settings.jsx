import React, { useState, useEffect } from 'react';
import { Save, Settings, Bell, Shield, Database, Wifi, RefreshCw, Download, Upload, Trash2, AlertCircle, Home } from 'lucide-react';
import apiService from '../services/api';

const SettingsPage = ({ onBackToHome = () => window.location.href = '/' }) => {
  const [settings, setSettings] = useState({
    // General Settings
    general: {
      theme: 'light',
      language: 'en',
      timezone: 'America/New_York',
      auto_refresh: true,
      refresh_interval: 5
    },
    
    // Notification Settings
    notifications: {
      email: true,
      push: true,
      workflow_completed: true,
      agent_offline: true,
      system_alerts: true,
      daily_summary: false
    },
    
    // Agent Settings
    agents: {
      auto_restart: true,
      max_retries: 3,
      timeout_seconds: 30,
      log_level: 'INFO',
      health_check_interval: 30,
      concurrent_workflows: 5
    },
    
    // API Settings
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
    
    // System Settings
    system: {
      auto_backup: true,
      backup_interval: 'daily',
      max_logs_days: 30,
      performance_monitoring: true,
      debug_mode: false,
      data_retention_days: 90,
      log_frequency: 'daily',
      memory_limit: 2048,
      cpu_limit: 80,
      cache_size: 256,
      rate_limiting: true,
      audit_logging: true,
      https_only: false,
      cors_protection: true,
      maintenance_mode: false
    }
  });

  const [loading, setLoading] = useState(false);
  const [saveStatus, setSaveStatus] = useState({ type: '', message: '' });
  const [systemStats, setSystemStats] = useState({
    disk_usage: 45,
    memory_usage: 62,
    uptime: '2 days',
    last_backup: '2025-01-15T08:00:00Z'
  });

  useEffect(() => {
    loadSettings();
    loadSystemStats();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const response = await apiService.getSystemSettings();
      if (response.success) {
        setSettings(response.settings);
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
      setSaveStatus({ type: 'error', message: 'Failed to load settings' });
    } finally {
      setLoading(false);
    }
  };

  const loadSystemStats = async () => {
    try {
      const stats = await apiService.getSystemStats();
      setSystemStats(stats);
    } catch (error) {
      console.error('Failed to load system stats:', error);
    }
  };

  const handleSettingChange = (section, key, value) => {
    setSettings(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value
      }
    }));
  };

  const handleSave = async () => {
    try {
      setLoading(true);
      setSaveStatus({ type: '', message: '' });
      
      const response = await apiService.saveSystemSettings(settings);
      
      if (response.success) {
        setSaveStatus({ type: 'success', message: 'Settings saved successfully!' });
        setTimeout(() => setSaveStatus({ type: '', message: '' }), 3000);
      } else {
        setSaveStatus({ type: 'error', message: response.error || 'Failed to save settings' });
      }
    } catch (error) {
      console.error('Failed to save settings:', error);
      setSaveStatus({ type: 'error', message: 'Failed to save settings' });
    } finally {
      setLoading(false);
    }
  };

  const handleExportSettings = async () => {
    try {
      const blob = new Blob([JSON.stringify(settings, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `plc-settings-${new Date().toISOString().split('T')[0]}.json`;
      a.click();
      URL.revokeObjectURL(url);
      setSaveStatus({ type: 'success', message: 'Settings exported successfully!' });
    } catch (error) {
      setSaveStatus({ type: 'error', message: 'Failed to export settings' });
    }
  };

  const handleImportSettings = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    try {
      const text = await file.text();
      const importedSettings = JSON.parse(text);
      setSettings(importedSettings);
      setSaveStatus({ type: 'success', message: 'Settings imported successfully!' });
    } catch (error) {
      setSaveStatus({ type: 'error', message: 'Failed to import settings. Invalid file format.' });
    }
  };

  const handleResetSettings = async () => {
    if (window.confirm('Are you sure you want to reset all settings to default? This cannot be undone.')) {
      try {
        const response = await apiService.resetSystemSettings();
        if (response.success) {
          setSettings(response.defaultSettings);
          setSaveStatus({ type: 'success', message: 'Settings reset to default values' });
        }
      } catch (error) {
        setSaveStatus({ type: 'error', message: 'Failed to reset settings' });
      }
    }
  };

  const testAPIConnection = async (apiType) => {
    try {
      setLoading(true);
      const response = await apiService.testAPIConnection(apiType, settings.api);
      
      if (response.success) {
        setSaveStatus({ type: 'success', message: `${apiType} connection successful!` });
      } else {
        setSaveStatus({ type: 'error', message: `${apiType} connection failed: ${response.error}` });
      }
    } catch (error) {
      setSaveStatus({ type: 'error', message: `Failed to test ${apiType} connection` });
    } finally {
      setLoading(false);
    }
  };

  const StatusMessage = ({ type, message }) => {
    if (!message) return null;
    
    return (
      <div className={`flex items-center gap-2 p-3 rounded-md ${
        type === 'success' ? 'bg-green-50 text-green-800 border border-green-200' :
        type === 'error' ? 'bg-red-50 text-red-800 border border-red-200' :
        'bg-blue-50 text-blue-800 border border-blue-200'
      }`}>
        <AlertCircle className="w-4 h-4" />
        <span className="text-sm">{message}</span>
      </div>
    );
  };

  if (loading && Object.keys(settings.general || {}).length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2 text-blue-500" />
          <p className="text-gray-600">Loading settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold text-gray-900">System Settings</h1>
          <p className="text-lg text-gray-600">Configure your Personal Life Coordination Agents</p>
        </div>

        {/* Status Message */}
        <StatusMessage type={saveStatus.type} message={saveStatus.message} />

        {/* Quick Actions */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="flex gap-4 flex-wrap">
            <button
              onClick={handleSave}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
              Save Settings
            </button>
            
            <button
              onClick={handleExportSettings}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              <Download className="w-4 h-4" />
              Export Settings
            </button>
            
            <label className="flex items-center gap-2 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 cursor-pointer transition-colors">
              <Upload className="w-4 h-4" />
              Import Settings
              <input
                type="file"
                accept=".json"
                onChange={handleImportSettings}
                className="hidden"
              />
            </label>
            
            <button
              onClick={handleResetSettings}
              className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              <Trash2 className="w-4 h-4" />
              Reset to Default
            </button>
            
            <button
              onClick={onBackToHome}
              className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
            >
              <Home className="w-4 h-4" />
              Back to Home
            </button>
          </div>
        </div>

        {/* System Stats */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">System Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-blue-600">{systemStats.disk_usage}%</p>
              <p className="text-sm text-gray-600">Disk Usage</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-green-600">{systemStats.memory_usage}%</p>
              <p className="text-sm text-gray-600">Memory Usage</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-purple-600">{systemStats.uptime}</p>
              <p className="text-sm text-gray-600">Uptime</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-orange-600">
                {systemStats.last_backup ? new Date(systemStats.last_backup).toLocaleDateString() : 'Never'}
              </p>
              <p className="text-sm text-gray-600">Last Backup</p>
            </div>
          </div>
        </div>

        {/* Settings Sections */}
        <div className="space-y-6">
          
          {/* General Settings */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center gap-2 mb-4">
              <Settings className="w-5 h-5 text-gray-600" />
              <h2 className="text-xl font-semibold text-gray-900">General Settings</h2>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Theme</label>
                <select 
                  value={settings.general.theme}
                  onChange={(e) => handleSettingChange('general', 'theme', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="light">Light</option>
                  <option value="dark">Dark</option>
                  <option value="auto">Auto</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Language</label>
                <select 
                  value={settings.general.language}
                  onChange={(e) => handleSettingChange('general', 'language', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="en">English</option>
                  <option value="es">Spanish</option>
                  <option value="fr">French</option>
                  <option value="de">German</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Timezone</label>
                <select 
                  value={settings.general.timezone}
                  onChange={(e) => handleSettingChange('general', 'timezone', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="America/New_York">Eastern Time</option>
                  <option value="America/Chicago">Central Time</option>
                  <option value="America/Denver">Mountain Time</option>
                  <option value="America/Los_Angeles">Pacific Time</option>
                  <option value="Europe/London">London Time</option>
                  <option value="Europe/Paris">Paris Time</option>
                  <option value="Asia/Tokyo">Tokyo Time</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Refresh Interval (seconds)</label>
                <input
                  type="number"
                  min="1"
                  max="60"
                  value={settings.general.refresh_interval}
                  onChange={(e) => handleSettingChange('general', 'refresh_interval', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div className="col-span-1 md:col-span-2">
                <div className="flex items-center justify-between">
                  <label className="text-sm text-gray-700">Auto Refresh Dashboard</label>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={settings.general.auto_refresh}
                      onChange={(e) => handleSettingChange('general', 'auto_refresh', e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
              </div>
            </div>
          </div>

          {/* Notification Settings */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center gap-2 mb-4">
              <Bell className="w-5 h-5 text-gray-600" />
              <h2 className="text-xl font-semibold text-gray-900">Notifications</h2>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(settings.notifications).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between">
                  <label className="text-sm text-gray-700 capitalize">
                    {key.replace('_', ' ')}
                  </label>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={value}
                      onChange={(e) => handleSettingChange('notifications', key, e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
              ))}
            </div>
          </div>

          {/* Agent Settings */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center gap-2 mb-4">
              <Wifi className="w-5 h-5 text-gray-600" />
              <h2 className="text-xl font-semibold text-gray-900">Agent Configuration</h2>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Max Retries</label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={settings.agents.max_retries}
                  onChange={(e) => handleSettingChange('agents', 'max_retries', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Timeout (seconds)</label>
                <input
                  type="number"
                  min="5"
                  max="300"
                  value={settings.agents.timeout_seconds}
                  onChange={(e) => handleSettingChange('agents', 'timeout_seconds', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Health Check Interval</label>
                <input
                  type="number"
                  min="10"
                  max="300"
                  value={settings.agents.health_check_interval}
                  onChange={(e) => handleSettingChange('agents', 'health_check_interval', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Log Level</label>
                <select 
                  value={settings.agents.log_level}
                  onChange={(e) => handleSettingChange('agents', 'log_level', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="DEBUG">Debug</option>
                  <option value="INFO">Info</option>
                  <option value="WARNING">Warning</option>
                  <option value="ERROR">Error</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Concurrent Workflows</label>
                <input
                  type="number"
                  min="1"
                  max="20"
                  value={settings.agents.concurrent_workflows}
                  onChange={(e) => handleSettingChange('agents', 'concurrent_workflows', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div className="flex items-center justify-between">
                <label className="text-sm text-gray-700">Auto Restart Failed Agents</label>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settings.agents.auto_restart}
                    onChange={(e) => handleSettingChange('agents', 'auto_restart', e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>
            </div>
          </div>

          {/* API Integration Settings */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center gap-2 mb-4">
              <Shield className="w-5 h-5 text-gray-600" />
              <h2 className="text-xl font-semibold text-gray-900">API Integrations</h2>
            </div>
            
            <div className="space-y-6">
              {/* OpenAI */}
              <div className="border-b pb-4">
                <h3 className="text-lg font-medium text-gray-900 mb-3">OpenAI Integration</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">OpenAI API Key</label>
                    <input
                      type="password"
                      value={settings.api.openai_key}
                      onChange={(e) => handleSettingChange('api', 'openai_key', e.target.value)}
                      placeholder="sk-..."
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">Required for AI-powered agent responses</p>
                  </div>
                  <div className="flex items-end">
                    <button
                      onClick={() => testAPIConnection('openai')}
                      className="px-4 py-2 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 transition-colors"
                    >
                      Test Connection
                    </button>
                  </div>
                </div>
              </div>
              
              {/* Google Calendar */}
              <div className="border-b pb-4">
                <h3 className="text-lg font-medium text-gray-900 mb-3">Google Calendar Integration</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="flex items-center justify-between">
                    <label className="text-sm text-gray-700">Enable Google Calendar</label>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={settings.api.google_calendar}
                        onChange={(e) => handleSettingChange('api', 'google_calendar', e.target.checked)}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Calendar ID</label>
                    <input
                      type="text"
                      value={settings.api.google_calendar_id}
                      onChange={(e) => handleSettingChange('api', 'google_calendar_id', e.target.value)}
                      placeholder="primary"
                      disabled={!settings.api.google_calendar}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                    />
                  </div>
                  <div className="flex items-end">
                    <button
                      onClick={() => testAPIConnection('google_calendar')}
                      disabled={!settings.api.google_calendar}
                      className="px-4 py-2 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 transition-colors disabled:opacity-50"
                    >
                      Test Connection
                    </button>
                  </div>
                </div>
              </div>
              
              {/* Fitbit */}
              <div className="border-b pb-4">
                <h3 className="text-lg font-medium text-gray-900 mb-3">Fitbit Integration</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="flex items-center justify-between">
                    <label className="text-sm text-gray-700">Enable Fitbit</label>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={settings.api.fitbit}
                        onChange={(e) => handleSettingChange('api', 'fitbit', e.target.checked)}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Access Token</label>
                    <input
                      type="password"
                      value={settings.api.fitbit_token}
                      onChange={(e) => handleSettingChange('api', 'fitbit_token', e.target.value)}
                      placeholder="••••••••"
                      disabled={!settings.api.fitbit}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                    />
                  </div>
                  <div className="flex items-end">
                    <button
                      onClick={() => testAPIConnection('fitbit')}
                      disabled={!settings.api.fitbit}
                      className="px-4 py-2 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 transition-colors disabled:opacity-50"
                    >
                      Test Connection
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* System Settings */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center gap-2 mb-4">
              <Database className="w-5 h-5 text-gray-600" />
              <h2 className="text-xl font-semibold text-gray-900">System Settings</h2>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Backup Interval</label>
                <select 
                  value={settings.system.backup_interval}
                  onChange={(e) => handleSettingChange('system', 'backup_interval', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Max Log Days</label>
                <input
                  type="number"
                  min="1"
                  max="365"
                  value={settings.system.max_logs_days}
                  onChange={(e) => handleSettingChange('system', 'max_logs_days', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Data Retention (days)</label>
                <input
                  type="number"
                  min="30"
                  max="365"
                  value={settings.system.data_retention_days}
                  onChange={(e) => handleSettingChange('system', 'data_retention_days', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div className="col-span-1 md:col-span-3 space-y-3">
                <div className="flex items-center justify-between">
                  <label className="text-sm text-gray-700">Auto Backup</label>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={settings.system.auto_backup}
                      onChange={(e) => handleSettingChange('system', 'auto_backup', e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
                
                <div className="flex items-center justify-between">
                  <label className="text-sm text-gray-700">Performance Monitoring</label>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={settings.system.performance_monitoring}
                      onChange={(e) => handleSettingChange('system', 'performance_monitoring', e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
                
                <div className="flex items-center justify-between">
                  <label className="text-sm text-gray-700">Debug Mode</label>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={settings.system.debug_mode}
                      onChange={(e) => handleSettingChange('system', 'debug_mode', e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
              </div>
            </div>
          </div>

          {/* Advanced Settings */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center gap-2 mb-4">
              <Settings className="w-5 h-5 text-gray-600" />
              <h2 className="text-xl font-semibold text-gray-900">Advanced Settings</h2>
            </div>
            
            <div className="space-y-4">
              {/* Performance Tuning */}
              <div className="border-b pb-4">
                <h3 className="text-lg font-medium text-gray-900 mb-3">Performance Tuning</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Memory Limit (MB)</label>
                    <input
                      type="number"
                      min="512"
                      max="8192"
                      value={settings.system.memory_limit}
                      onChange={(e) => handleSettingChange('system', 'memory_limit', parseInt(e.target.value))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">CPU Usage Limit (%)</label>
                    <input
                      type="number"
                      min="10"
                      max="100"
                      value={settings.system.cpu_limit}
                      onChange={(e) => handleSettingChange('system', 'cpu_limit', parseInt(e.target.value))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Cache Size (MB)</label>
                    <input
                      type="number"
                      min="64"
                      max="1024"
                      value={settings.system.cache_size}
                      onChange={(e) => handleSettingChange('system', 'cache_size', parseInt(e.target.value))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>

              {/* Security Settings */}
              <div className="border-b pb-4">
                <h3 className="text-lg font-medium text-gray-900 mb-3">Security Settings</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="flex items-center justify-between">
                    <label className="text-sm text-gray-700">Enable API Rate Limiting</label>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={settings.system.rate_limiting}
                        onChange={(e) => handleSettingChange('system', 'rate_limiting', e.target.checked)}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <label className="text-sm text-gray-700">Enable Audit Logging</label>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={settings.system.audit_logging}
                        onChange={(e) => handleSettingChange('system', 'audit_logging', e.target.checked)}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <label className="text-sm text-gray-700">HTTPS Only</label>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={settings.system.https_only}
                        onChange={(e) => handleSettingChange('system', 'https_only', e.target.checked)}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <label className="text-sm text-gray-700">Enable CORS Protection</label>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={settings.system.cors_protection}
                        onChange={(e) => handleSettingChange('system', 'cors_protection', e.target.checked)}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                </div>
              </div>
              
              {/* Danger Zone */}
              <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
                <div className="flex items-center gap-2 mb-2">
                  <AlertCircle className="w-5 h-5 text-yellow-600" />
                  <h3 className="text-sm font-medium text-yellow-800">Danger Zone</h3>
                </div>
                <p className="text-sm text-yellow-700 mb-3">
                  These actions can significantly impact system behavior. Use with caution.
                </p>
                <div className="flex gap-2 flex-wrap">
                  <button
                    onClick={() => {
                      if (window.confirm('Are you sure you want to clear all logs? This cannot be undone.')) {
                        apiService.clearSystemLogs();
                        setSaveStatus({ type: 'success', message: 'System logs cleared' });
                      }
                    }}
                    className="px-3 py-2 bg-yellow-100 text-yellow-800 rounded-md hover:bg-yellow-200 transition-colors text-sm"
                  >
                    Clear All Logs
                  </button>
                  
                  <button
                    onClick={() => {
                      if (window.confirm('Are you sure you want to restart all agents? This will cause temporary downtime.')) {
                        apiService.restartAllAgents();
                        setSaveStatus({ type: 'success', message: 'All agents restarting...' });
                      }
                    }}
                    className="px-3 py-2 bg-orange-100 text-orange-800 rounded-md hover:bg-orange-200 transition-colors text-sm"
                  >
                    Restart All Agents
                  </button>
                  
                  <button
                    onClick={() => {
                      if (window.confirm('Are you sure you want to reset the database? This will delete ALL data and cannot be undone.')) {
                        if (window.confirm('This is your final warning. Are you absolutely sure?')) {
                          apiService.resetDatabase();
                          setSaveStatus({ type: 'error', message: 'Database reset initiated' });
                        }
                      }
                    }}
                    className="px-3 py-2 bg-red-100 text-red-800 rounded-md hover:bg-red-200 transition-colors text-sm"
                  >
                    Reset Database
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Maintenance Mode */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center gap-2 mb-4">
              <AlertCircle className="w-5 h-5 text-gray-600" />
              <h2 className="text-xl font-semibold text-gray-900">Maintenance Mode</h2>
            </div>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <h3 className="text-sm font-medium text-gray-900">Enable Maintenance Mode</h3>
                  <p className="text-xs text-gray-500">Temporarily disable all agents for system maintenance</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settings.system.maintenance_mode}
                    onChange={(e) => {
                      if (e.target.checked) {
                        if (window.confirm('Enabling maintenance mode will stop all agents. Continue?')) {
                          handleSettingChange('system', 'maintenance_mode', true);
                        }
                      } else {
                        handleSettingChange('system', 'maintenance_mode', false);
                      }
                    }}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>
              
              {settings.system.maintenance_mode && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <AlertCircle className="w-4 h-4 text-red-600" />
                    <span className="text-sm font-medium text-red-800">Maintenance Mode Active</span>
                  </div>
                  <p className="text-xs text-red-700">
                    All agents are currently disabled. Users will see a maintenance page.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Final Save Button */}
        <div className="flex justify-between items-center">
          <div className="text-sm text-gray-500">
            Changes are saved automatically to your browser. Click "Save Settings" to persist to server.
          </div>
          <button
            onClick={handleSave}
            disabled={loading}
            className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            Save All Settings
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;