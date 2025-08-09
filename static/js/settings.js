// Settings page JavaScript for RAG system management
class SettingsManager {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
        this.checkSystemStatus();
        this.loadConfiguration();
        this.loadMetrics();
    }

    bindEvents() {
        // Configuration save
        const saveConfigButton = document.getElementById('saveConfigButton');
        if (saveConfigButton) {
            saveConfigButton.addEventListener('click', () => this.saveConfiguration());
        }

        // Add document
        const addDocumentButton = document.getElementById('addDocumentButton');
        if (addDocumentButton) {
            addDocumentButton.addEventListener('click', () => this.showAddDocumentModal());
        }

        // Clear logs
        const clearLogsButton = document.getElementById('clearLogsButton');
        if (clearLogsButton) {
            clearLogsButton.addEventListener('click', () => this.clearLogs());
        }
    }

    async checkSystemStatus() {
        console.log('Checking system status...');
        
        // Check API status
        try {
            const response = await fetch('/api/status');
            if (!response.ok) throw new Error('Status check failed');
            
            const statusData = await response.json();
            this.updateSystemStatus(statusData);
            
        } catch (error) {
            console.error('Error checking system status:', error);
            this.updateSystemStatusError();
        }

    }

    updateSystemStatus(statusData) {
        // Update API status
        const apiStatus = document.getElementById('apiStatus');
        if (apiStatus) {
            if (statusData.status === 'healthy') {
                apiStatus.textContent = '✅ Online';
                apiStatus.className = 'status-value online';
            } else {
                apiStatus.textContent = '❌ Error';
                apiStatus.className = 'status-value offline';
            }
        }

        // Update Milvus status
        const milvusStatus = document.getElementById('milvusStatus');
        if (milvusStatus) {
            const milvus = statusData.components.milvus;
            if (milvus.status === 'connected') {
                milvusStatus.textContent = `✅ Connected (${statusData.ml_concepts.total_concepts} concepts)`;
                milvusStatus.className = 'status-value online';
            } else {
                milvusStatus.textContent = '❌ Disconnected';
                milvusStatus.className = 'status-value offline';
            }
        }

        // Update OpenAI status
        const openaiStatus = document.getElementById('openaiStatus');
        if (openaiStatus) {
            const openai = statusData.components.openai;
            if (openai.status === 'connected') {
                openaiStatus.textContent = '✅ Connected';
                openaiStatus.className = 'status-value online';
            } else {
                openaiStatus.textContent = '❌ Not configured';
                openaiStatus.className = 'status-value offline';
            }
        }

        // Update Supabase status
        const supabaseStatus = document.getElementById('supabaseStatus');
        if (supabaseStatus) {
            const supabase = statusData.components.supabase;
            if (supabase.status === 'connected') {
                supabaseStatus.textContent = '✅ Connected';
                supabaseStatus.className = 'status-value online';
            } else {
                supabaseStatus.textContent = '❌ Not configured';
                supabaseStatus.className = 'status-value offline';
            }
        }

        // Update RAG system status
        const ragStatus = document.getElementById('ragStatus');
        if (ragStatus) {
            const rag = statusData.components.rag_system;
            if (rag.status === 'operational') {
                ragStatus.textContent = '✅ Operational';
                ragStatus.className = 'status-value online';
            } else {
                ragStatus.textContent = '⚠️ Degraded';
                ragStatus.className = 'status-value offline';
            }
        }
    }

    updateSystemStatusError() {
        const statusElements = ['apiStatus', 'milvusStatus', 'openaiStatus', 'supabaseStatus', 'ragStatus'];
        statusElements.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = '❌ Error';
                element.className = 'status-value offline';
            }
        });
    }

    async loadConfiguration() {
        try {
            const response = await fetch('/api/reranking-config');
            if (response.ok) {
                const config = await response.json();
                
                const enableReranking = document.getElementById('enableReranking');
                const rerankingModel = document.getElementById('rerankingModel');
                const searchMultiplier = document.getElementById('searchMultiplier');

                if (enableReranking) enableReranking.checked = config.enabled;
                if (rerankingModel) rerankingModel.value = config.model;
                if (searchMultiplier) searchMultiplier.value = config.multiplier;
            }
        } catch (error) {
            console.error('Error loading configuration:', error);
        }
    }

    async saveConfiguration() {
        const enableReranking = document.getElementById('enableReranking');
        const rerankingModel = document.getElementById('rerankingModel');
        const searchMultiplier = document.getElementById('searchMultiplier');

        const config = {
            enabled: enableReranking?.checked || false,
            model: rerankingModel?.value || 'gpt-3.5-turbo',
            multiplier: parseInt(searchMultiplier?.value) || 3
        };

        try {
            const response = await fetch('/api/reranking-config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });

            if (response.ok) {
                this.showMessage('Configuration saved successfully!', 'success');
                this.addLogEntry('Configuration updated');
            } else {
                this.showMessage('Failed to save configuration', 'error');
            }
        } catch (error) {
            console.error('Error saving configuration:', error);
            this.showMessage('Error saving configuration', 'error');
        }
    }

    async loadMetrics() {
        // Load performance metrics
        const metrics = {
            queriesCount: localStorage.getItem('queriesCount') || '0',
            avgResponseTime: localStorage.getItem('avgResponseTime') || 'N/A',
            documentsCount: '0',
            lastUpdated: localStorage.getItem('lastUpdated') || 'Never'
        };

        document.getElementById('queriesCount').textContent = metrics.queriesCount;
        document.getElementById('avgResponseTime').textContent = metrics.avgResponseTime;
        document.getElementById('documentsCount').textContent = metrics.documentsCount;
        document.getElementById('lastUpdated').textContent = metrics.lastUpdated;
    }

    showAddDocumentModal() {
        // For now, show a simple alert
        alert('Document upload feature coming soon!');
        this.addLogEntry('Document upload attempted');
    }

    clearLogs() {
        const logsContent = document.getElementById('systemLogs');
        if (logsContent) {
            logsContent.innerHTML = '<p class="log-entry">Logs cleared...</p>';
        }
    }

    addLogEntry(message) {
        const logsContent = document.getElementById('systemLogs');
        if (logsContent) {
            const timestamp = new Date().toLocaleTimeString();
            const logEntry = document.createElement('p');
            logEntry.className = 'log-entry';
            logEntry.textContent = `[${timestamp}] ${message}`;
            logsContent.appendChild(logEntry);
            
            // Keep only last 10 entries
            const entries = logsContent.querySelectorAll('.log-entry');
            if (entries.length > 10) {
                entries[0].remove();
            }
        }
    }

    showMessage(message, type) {
        // Create a temporary message element
        const messageEl = document.createElement('div');
        messageEl.className = `message ${type}`;
        messageEl.textContent = message;
        messageEl.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 24px;
            border-radius: 6px;
            color: white;
            background: ${type === 'success' ? '#10B981' : '#EF4444'};
            z-index: 1000;
            animation: slideIn 0.3s ease;
        `;

        document.body.appendChild(messageEl);

        setTimeout(() => {
            messageEl.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => messageEl.remove(), 300);
        }, 3000);
    }
}

// Initialize settings manager when page loads
document.addEventListener('DOMContentLoaded', () => {
    new SettingsManager();
});

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);
