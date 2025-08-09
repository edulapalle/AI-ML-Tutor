// Chat application JavaScript with authentication support
class ChatApp {
    constructor() {
        this.conversationHistory = [];
        this.isLoading = false;
        this.userData = window.userData || {};
        this.init();
    }

    init() {
        // Check authentication first
        if (!this.checkAuthentication()) {
            return; // Will redirect to login
        }
        
        this.bindEvents();
        this.loadSettings();
        this.checkHealth();
        this.autoResizeTextarea();
        this.initUserMenu();
        this.initQuickActions();

        this.loadUserProfile();
    }

    bindEvents() {
        // Send message
        const sendButton = document.getElementById('sendButton');
        const messageInput = document.getElementById('messageInput');
        
        sendButton.addEventListener('click', () => this.sendMessage());
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Clear chat
        const clearButton = document.getElementById('clearButton');
        if (clearButton) {
            clearButton.addEventListener('click', () => this.clearChat());
        }



        // Logout button
        const logoutButton = document.getElementById('logoutButton');
        if (logoutButton) {
            logoutButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.logout();
            });
        }


    }

    initUserMenu() {
        const userMenuButton = document.getElementById('userMenuButton');
        const userDropdown = document.getElementById('userDropdown');
        
        if (userMenuButton && userDropdown) {
            userMenuButton.addEventListener('click', () => {
                userDropdown.classList.toggle('show');
            });

            // Close dropdown when clicking outside
            document.addEventListener('click', (e) => {
                if (!userMenuButton.contains(e.target) && !userDropdown.contains(e.target)) {
                    userDropdown.classList.remove('show');
                }
            });
        }
    }

    initQuickActions() {
        const quickActions = document.querySelectorAll('.quick-action');
        quickActions.forEach(button => {
            button.addEventListener('click', () => {
                const question = button.dataset.question;
                if (question) {
                    document.getElementById('messageInput').value = question;
                    this.sendMessage();
                }
            });
        });
    }



    autoResizeTextarea() {
        const textarea = document.getElementById('messageInput');
        if (textarea) {
            textarea.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = Math.min(this.scrollHeight, 120) + 'px';
            });
        }
    }

    async sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const message = messageInput.value.trim();
        
        if (!message || this.isLoading) return;

        // Add user message to chat
        this.addMessageToChat('user', message);
        messageInput.value = '';
        messageInput.style.height = 'auto';

        // Show typing indicator
        this.showTypingIndicator();

        try {
            // Get authentication token
            const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
            
            const headers = {
                'Content-Type': 'application/json',
            };

            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }

            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({
                    message: message,
                    conversation_history: this.conversationHistory
                })
            });

            if (response.status === 401) {
                // Token expired or invalid, redirect to login
                window.location.href = '/login';
                return;
            }

            const data = await response.json();
            
            if (response.ok) {
                // Add assistant response to chat
                this.addMessageToChat('assistant', data.response);
                
                // Update sources
                this.updateSources(data.sources);
            } else {
                this.addMessageToChat('assistant', `Error: ${data.detail || 'Failed to get response'}`);
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.addMessageToChat('assistant', 'Sorry, I encountered an error. Please try again.');
        } finally {
            this.hideTypingIndicator();
        }
    }

    addMessageToChat(role, content) {
        const chatMessages = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        if (role === 'user') {
            messageContent.innerHTML = `
                <div class="message-header">
                    <i class="fas fa-user"></i>
                    <span class="message-author">${this.userData.username || 'You'}</span>
                </div>
                <div class="message-text">${this.escapeHtml(content)}</div>
            `;
        } else if (role === 'assistant') {
            messageContent.innerHTML = `
                <div class="message-header">
                    <i class="fas fa-robot"></i>
                    <span class="message-author">AI Assistant</span>
                </div>
                <div class="message-text">${this.formatResponse(content)}</div>
            `;
        } else {
            messageContent.innerHTML = `
                <i class="fas fa-info-circle"></i>
                ${this.escapeHtml(content)}
            `;
        }
        
        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Add to conversation history
        this.conversationHistory.push({
            role: role,
            content: content
        });
        
        // Limit conversation history
        if (this.conversationHistory.length > 20) {
            this.conversationHistory = this.conversationHistory.slice(-20);
        }
    }

    formatResponse(content) {
        // Convert markdown-like formatting to HTML
        let formatted = this.escapeHtml(content);
        
        // Convert **bold** to <strong>bold</strong>
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Convert *italic* to <em>italic</em>
        formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        // Convert line breaks to <br>
        formatted = formatted.replace(/\n/g, '<br>');
        
        return formatted;
    }

    showTypingIndicator() {
        const chatMessages = document.getElementById('chatMessages');
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message assistant typing-indicator';
        typingDiv.id = 'typingIndicator';
        
        typingDiv.innerHTML = `
            <div class="message-content">
                <div class="typing-dots">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
        
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    updateSources(sources) {
        const sourcesList = document.getElementById('sourcesList');
        if (!sourcesList) return;

        if (!sources || sources.length === 0) {
            sourcesList.innerHTML = '<p class="no-sources">No sources found for current query</p>';
            return;
        }

        sourcesList.innerHTML = sources.map(source => `
            <div class="source-item">
                <h4>${this.escapeHtml(source.metadata?.[0]?.channel_name || 'Unknown Source')}</h4>
                <p>${this.escapeHtml(source.text.substring(0, 150))}...</p>
                ${source.score ? `<span class="score">Score: ${source.score.toFixed(3)}</span>` : ''}
            </div>
        `).join('');
    }

    clearChat() {
        const chatMessages = document.getElementById('chatMessages');
        const systemMessage = chatMessages.querySelector('.message.system');
        
        chatMessages.innerHTML = '';
        if (systemMessage) {
            chatMessages.appendChild(systemMessage);
        }
        
        this.conversationHistory = [];
    }

    showVoiceModal() {
        const voiceModal = document.getElementById('voiceModal');
        if (voiceModal) {
            voiceModal.style.display = 'flex';
        }
    }

    hideVoiceModal() {
        const voiceModal = document.getElementById('voiceModal');
        if (voiceModal) {
            voiceModal.style.display = 'none';
        }
    }

    checkAuthentication() {
        // Check if user has valid token
        const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
        
        if (!token) {
            console.log('No authentication token found, redirecting to login');
            window.location.href = '/login';
            return false;
        }
        
        // Store token for API requests
        this.authToken = token;
        return true;
    }

    async loadUserProfile() {
        try {
            const response = await fetch('/api/auth/profile', {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const userData = await response.json();
                this.userData = userData;
                this.updateUserDisplay(userData);
            } else if (response.status === 401) {
                // Token is invalid, redirect to login
                this.logout();
            } else {
                console.error('Failed to load user profile');
            }
        } catch (error) {
            console.error('Error loading user profile:', error);
        }
    }

    updateUserDisplay(userData) {
        // Update user information in the UI
        
        // Update header user information
        const welcomeUsername = document.getElementById('welcomeUsername');
        const headerUsername = document.getElementById('headerUsername');
        const userLevelInfo = document.getElementById('userLevelInfo');
        
        if (welcomeUsername) welcomeUsername.textContent = userData.username;
        if (headerUsername) headerUsername.textContent = userData.username;
        
        // Format and display user level and stage information
        if (userLevelInfo) {
            const studyLevel = userData.study_level ? userData.study_level.charAt(0).toUpperCase() + userData.study_level.slice(1) : 'Unknown';
            const currentStage = userData.current_stage ? userData.current_stage.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'Unknown';
            userLevelInfo.textContent = `Level: ${studyLevel} | Stage: ${currentStage}`;
        }

        // Update sidebar elements (if they exist)
        const usernameEl = document.querySelector('.username');
        const userLevelEl = document.querySelector('.user-level');
        const currentStageEl = document.querySelector('.current-stage');

        if (usernameEl) usernameEl.textContent = userData.username;
        if (userLevelEl) userLevelEl.textContent = userData.study_level;
        if (currentStageEl) currentStageEl.textContent = userData.current_stage;

        // Update interests
        const interestsList = document.querySelector('.interests-list');
        if (interestsList && userData.topics_of_interest) {
            interestsList.innerHTML = '';
            userData.topics_of_interest.forEach(interest => {
                const tag = document.createElement('span');
                tag.className = 'interest-tag';
                tag.textContent = interest;
                interestsList.appendChild(tag);
            });
        }

        // Update goals
        const goalsList = document.querySelector('.goals-list');
        if (goalsList && userData.current_goals) {
            goalsList.innerHTML = '';
            userData.current_goals.forEach(goal => {
                const goalItem = document.createElement('div');
                goalItem.className = 'goal-item';
                goalItem.textContent = goal;
                goalsList.appendChild(goalItem);
            });
        }
    }

    async logout() {
        try {
            const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
            
            if (token) {
                await fetch('/api/auth/logout', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
            }
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            // Clear local storage and redirect
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user_info');
            sessionStorage.removeItem('auth_token');
            sessionStorage.removeItem('user_info');
            
            window.location.href = '/login';
        }
    }

    loadSettings() {
        // Load any saved settings from localStorage
        const savedApiKey = localStorage.getItem('openai_api_key');
        if (savedApiKey) {
            const apiKeyInput = document.getElementById('openaiKey');
            if (apiKeyInput) {
                apiKeyInput.value = savedApiKey;
            }
        }
    }

    async checkHealth() {
        try {
            const response = await fetch('/api/health');
            const data = await response.json();
            
            const apiStatus = document.getElementById('apiStatus');
            const milvusStatus = document.getElementById('milvusStatus');
            
            if (apiStatus) {
                apiStatus.textContent = data.status === 'healthy' ? 'Healthy' : 'Error';
                apiStatus.className = `status-value ${data.status === 'healthy' ? 'healthy' : 'error'}`;
            }
            
            if (milvusStatus) {
                milvusStatus.textContent = data.milvus_status === 'connected' ? 'Connected' : 'Disconnected';
                milvusStatus.className = `status-value ${data.milvus_status === 'connected' ? 'healthy' : 'error'}`;
            }
        } catch (error) {
            console.error('Health check failed:', error);
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the chat application
document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
}); 