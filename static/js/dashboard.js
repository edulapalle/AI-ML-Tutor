/**
 * Dashboard JavaScript - Unified AI/ML Educational Platform
 * Handles chat, authentication, stars, and learning paths
 */

class Dashboard {
    constructor() {
        this.conversationHistory = [];
        this.currentUser = null;
        this.settings = {
            audience: 'kid',
            useGraph: true,
            autoScroll: true
        };
        
        this.init();
    }

    async init() {
        try {
            // Check authentication first
            const isAuthenticated = await this.checkAuth();
            if (!isAuthenticated) {
                console.log('Not authenticated, redirecting to login');
                this.redirectToLogin();
                return;
            }
            
            // Initialize UI components
            this.initEventListeners();
            this.initQuickActions();
            this.initModals();
            
            // Load user data and populate UI
            await this.loadUserProfile();
            await this.loadStars();
            await this.checkSystemHealth();
            
            console.log('Dashboard initialized successfully');
        } catch (error) {
            console.error('Dashboard initialization failed:', error);
            this.redirectToLogin();
        }
    }

    // ===== AUTHENTICATION =====
    
    async checkAuth() {
        const token = this.getAuthToken();
        if (!token) {
            console.log('No auth token found');
            return false;
        }

        try {
            const response = await fetch('/api/auth/profile', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                console.log('Authentication failed:', response.status);
                this.removeAuthToken();
                return false;
            }

            this.currentUser = await response.json();
            console.log('User authenticated:', this.currentUser.username);
            return true;
        } catch (error) {
            console.error('Auth check error:', error);
            this.removeAuthToken();
            return false;
        }
    }

    getAuthToken() {
        return localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
    }

    removeAuthToken() {
        localStorage.removeItem('auth_token');
        sessionStorage.removeItem('auth_token');
    }

    redirectToLogin() {
        window.location.href = '/login';
    }

    async logout() {
        try {
            const token = this.getAuthToken();
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
            this.removeAuthToken();
            this.redirectToLogin();
        }
    }

    // ===== USER PROFILE =====

    async loadUserProfile() {
        if (!this.currentUser) return;

        // Update settings based on user age
        if (this.currentUser.user_age < 13) {
            this.settings.audience = 'kid';
        } else if (this.currentUser.user_age < 18) {
            this.settings.audience = 'teen';
        } else {
            this.settings.audience = 'adult';
        }

        // Update audience select in settings
        const audienceSelect = document.getElementById('audienceSelect');
        if (audienceSelect) {
            audienceSelect.value = this.settings.audience;
        }

        // Update UI with user data
        this.updateUserDisplay();
    }

    updateUserDisplay() {
        if (!this.currentUser) return;

        // Update header
        const username = document.querySelector('.username');
        const userLevel = document.querySelector('.user-level');
        if (username) username.textContent = this.currentUser.username;
        if (userLevel) userLevel.textContent = this.currentUser.study_level.charAt(0).toUpperCase() + this.currentUser.study_level.slice(1);

        // Update welcome message
        const welcomeMessage = document.getElementById('welcomeMessage');
        if (welcomeMessage) welcomeMessage.textContent = `Welcome back, ${this.currentUser.username}! 👋`;

        // Update profile card
        const userLevelEl = document.getElementById('userLevel');
        const userStageEl = document.getElementById('userStage');
        const userAgeEl = document.getElementById('userAge');

        if (userLevelEl) userLevelEl.textContent = this.currentUser.study_level.charAt(0).toUpperCase() + this.currentUser.study_level.slice(1);
        if (userStageEl) userStageEl.textContent = this.currentUser.current_stage.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
        if (userAgeEl) userAgeEl.textContent = `${this.currentUser.user_age} years`;

        // Update interests
        const userInterests = document.getElementById('userInterests');
        if (userInterests && this.currentUser.topics_of_interest) {
            userInterests.innerHTML = '';
            this.currentUser.topics_of_interest.forEach(interest => {
                const tag = document.createElement('span');
                tag.className = 'interest-tag';
                tag.textContent = interest.charAt(0).toUpperCase() + interest.slice(1);
                userInterests.appendChild(tag);
            });
        }
    }

    // ===== CHAT FUNCTIONALITY =====

    async sendMessage(message) {
        if (!message.trim()) return;

        try {
            this.showLoadingOverlay();
            this.addMessageToChat('user', message);
            this.showTypingIndicator();

            const token = this.getAuthToken();
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    message: message,
                    conversation_history: this.conversationHistory.slice(-10), // Last 10 messages
                    audience: this.settings.audience,
                    use_graph: this.settings.useGraph
                })
            });

            this.hideTypingIndicator();

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Chat request failed');
            }

            const data = await response.json();
            
            // Add assistant response
            this.addMessageToChat('assistant', data.answer, {
                citations: data.citations,
                next_concepts: data.next_concepts,
                intent: data.intent,
                latency: data.latency_ms
            });

            // Update conversation history
            this.conversationHistory.push(
                { role: 'user', content: message },
                { role: 'assistant', content: data.answer }
            );

            // Update learning panel with next concepts
            this.updateNextConcepts(data.next_concepts);

        } catch (error) {
            this.hideTypingIndicator();
            this.addMessageToChat('assistant', `❌ Sorry, I encountered an error: ${error.message}`);
            console.error('Chat error:', error);
        } finally {
            this.hideLoadingOverlay();
        }
    }

    addMessageToChat(role, content, metadata = {}) {
        const chatMessages = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = role === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.innerHTML = this.formatMessage(content);

        // Add citations if present
        if (metadata.citations && metadata.citations.length > 0) {
            const citationsDiv = this.createCitationsElement(metadata.citations);
            messageContent.appendChild(citationsDiv);
        }

        // Add next concepts if present
        if (metadata.next_concepts && metadata.next_concepts.length > 0) {
            const conceptsDiv = this.createNextConceptsElement(metadata.next_concepts);
            messageContent.appendChild(conceptsDiv);
        }

        // Add message actions for assistant messages
        if (role === 'assistant') {
            const actionsDiv = this.createMessageActions(content, metadata);
            messageContent.appendChild(actionsDiv);
        }

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);

        if (this.settings.autoScroll) {
            this.scrollToBottom();
        }
    }

    formatMessage(content) {
        // Convert markdown-like formatting to HTML
        let formatted = this.escapeHtml(content);
        
        // Convert **bold** to <strong>
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Convert *italic* to <em>
        formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        // Convert line breaks to <br>
        formatted = formatted.replace(/\n/g, '<br>');
        
        return formatted;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    createCitationsElement(citations) {
        const citationsDiv = document.createElement('div');
        citationsDiv.className = 'citations';
        
        const title = document.createElement('h4');
        title.textContent = '📚 Sources:';
        citationsDiv.appendChild(title);

        citations.forEach(citation => {
            const citationDiv = document.createElement('div');
            citationDiv.className = 'citation';
            
            const titleEl = document.createElement('div');
            titleEl.className = 'citation-title';
            titleEl.textContent = citation.title || citation.doc_id;
            
            const sourceEl = document.createElement('div');
            sourceEl.className = 'citation-source';
            sourceEl.textContent = `${citation.source || 'Unknown'} (${citation.kind || 'content'})`;
            
            citationDiv.appendChild(titleEl);
            citationDiv.appendChild(sourceEl);
            
            // Make citation clickable to star it
            citationDiv.addEventListener('click', () => {
                this.starContent(citation.doc_id, citation.title);
            });
            
            citationsDiv.appendChild(citationDiv);
        });

        return citationsDiv;
    }

    createNextConceptsElement(concepts) {
        const conceptsDiv = document.createElement('div');
        conceptsDiv.className = 'next-concepts-inline';
        
        const title = document.createElement('h4');
        title.textContent = '🎯 What to learn next:';
        conceptsDiv.appendChild(title);

        const tagsDiv = document.createElement('div');
        tagsDiv.className = 'concept-tags';

        concepts.forEach(concept => {
            const tag = document.createElement('span');
            tag.className = 'concept-tag';
            tag.textContent = concept;
            tag.addEventListener('click', () => {
                this.sendMessage(`Tell me about ${concept}`);
            });
            tagsDiv.appendChild(tag);
        });

        conceptsDiv.appendChild(tagsDiv);
        return conceptsDiv;
    }

    createMessageActions(content, metadata) {
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'message-actions';

        // Star action
        const starBtn = document.createElement('button');
        starBtn.className = 'message-action';
        starBtn.innerHTML = '<i class="fas fa-star"></i>';
        starBtn.title = 'Bookmark this response';
        starBtn.addEventListener('click', () => {
            const title = `Response about ${this.conversationHistory[this.conversationHistory.length - 2]?.content?.substring(0, 50) || 'concept'}...`;
            this.starContent('chat-response-' + Date.now(), title, content);
        });

        // Copy action
        const copyBtn = document.createElement('button');
        copyBtn.className = 'message-action';
        copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
        copyBtn.title = 'Copy response';
        copyBtn.addEventListener('click', () => {
            navigator.clipboard.writeText(content).then(() => {
                this.showNotification('Response copied to clipboard!');
            });
        });

        actionsDiv.appendChild(starBtn);
        actionsDiv.appendChild(copyBtn);
        return actionsDiv;
    }

    showTypingIndicator() {
        const chatMessages = document.getElementById('chatMessages');
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message assistant typing-indicator';
        typingDiv.id = 'typingIndicator';
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = '<i class="fas fa-robot"></i>';
        
        const content = document.createElement('div');
        content.className = 'message-content';
        content.innerHTML = `
            <div class="typing-dots">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        
        typingDiv.appendChild(avatar);
        typingDiv.appendChild(content);
        chatMessages.appendChild(typingDiv);
        
        if (this.settings.autoScroll) {
            this.scrollToBottom();
        }
    }

    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    scrollToBottom() {
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    clearChat() {
        const chatMessages = document.getElementById('chatMessages');
        // Keep only the welcome message
        const welcomeMessage = chatMessages.querySelector('.welcome-message');
        chatMessages.innerHTML = '';
        if (welcomeMessage) {
            chatMessages.appendChild(welcomeMessage);
        }
        this.conversationHistory = [];
    }

    // ===== STARS/BOOKMARKS =====

    async starContent(docId, title, note = '') {
        try {
            const token = this.getAuthToken();
            const response = await fetch('/api/star', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    doc_id: docId,
                    note: note || `Starred: ${title}`
                })
            });

            if (response.ok) {
                this.showNotification('Content bookmarked! ⭐');
                await this.loadStars();
            } else {
                throw new Error('Failed to star content');
            }
        } catch (error) {
            console.error('Star error:', error);
            this.showNotification('Failed to bookmark content ❌');
        }
    }

    async loadStars() {
        try {
            const token = this.getAuthToken();
            const response = await fetch('/api/stars', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const stars = await response.json();
                this.updateStarCount(stars.length);
                this.updateStarsList(stars);
                return stars;
            }
        } catch (error) {
            console.error('Load stars error:', error);
        }
        return [];
    }

    updateStarCount(count) {
        const starCount = document.querySelector('.star-count');
        if (starCount) {
            starCount.textContent = count;
            starCount.style.display = count > 0 ? 'block' : 'none';
        }
    }

    updateStarsList(stars) {
        // Update sidebar stars
        const starsList = document.querySelector('.stars-list');
        if (starsList) {
            starsList.innerHTML = '';
            
            if (stars.length === 0) {
                starsList.innerHTML = '<p style="color: #999; font-style: italic;">No bookmarks yet</p>';
                return;
            }

            stars.slice(0, 3).forEach(star => {
                const starItem = document.createElement('div');
                starItem.className = 'star-item';
                starItem.innerHTML = `
                    <div class="star-title">${star.doc_id.substring(0, 30)}...</div>
                    ${star.note ? `<div class="star-note">${star.note.substring(0, 50)}...</div>` : ''}
                `;
                starsList.appendChild(starItem);
            });

            if (stars.length > 3) {
                const moreItem = document.createElement('div');
                moreItem.className = 'star-item';
                moreItem.style.textAlign = 'center';
                moreItem.style.color = '#667eea';
                moreItem.style.cursor = 'pointer';
                moreItem.textContent = `+${stars.length - 3} more...`;
                moreItem.addEventListener('click', () => this.showStarsModal());
                starsList.appendChild(moreItem);
            }
        }

        // Update modal stars grid
        const starsGrid = document.getElementById('starsGrid');
        if (starsGrid) {
            starsGrid.innerHTML = '';
            
            if (stars.length === 0) {
                starsGrid.innerHTML = '<p style="color: #999; text-align: center;">No bookmarks yet. Star some content to see it here!</p>';
                return;
            }

            stars.forEach(star => {
                const starCard = document.createElement('div');
                starCard.className = 'star-card';
                starCard.innerHTML = `
                    <div class="star-card-title">${star.doc_id}</div>
                    ${star.note ? `<div class="star-card-note">${star.note}</div>` : ''}
                    ${star.created_at ? `<div class="star-card-date">${new Date(star.created_at).toLocaleDateString()}</div>` : ''}
                `;
                starsGrid.appendChild(starCard);
            });
        }
    }

    // ===== LEARNING PATHS =====

    async getNextConcepts(concept) {
        try {
            const response = await fetch(`/api/next?concept=${encodeURIComponent(concept)}&limit=3`);
            if (response.ok) {
                const data = await response.json();
                return data.next_concepts || [];
            }
        } catch (error) {
            console.error('Get next concepts error:', error);
        }
        return [];
    }

    updateNextConcepts(concepts) {
        const conceptsList = document.querySelector('.concepts-list');
        if (!conceptsList) return;

        conceptsList.innerHTML = '';
        
        if (concepts.length === 0) {
            conceptsList.innerHTML = '<p style="color: #999; font-style: italic;">No suggestions yet</p>';
            return;
        }

        concepts.forEach(concept => {
            const conceptItem = document.createElement('div');
            conceptItem.className = 'concept-item';
            conceptItem.innerHTML = `<div class="concept-name">${concept}</div>`;
            conceptItem.addEventListener('click', () => {
                this.sendMessage(`Tell me about ${concept}`);
            });
            conceptsList.appendChild(conceptItem);
        });
    }

    // ===== SYSTEM HEALTH =====

    async checkSystemHealth() {
        try {
            const response = await fetch('/api/health');
            const health = await response.json();

            this.updateStatusIndicator('milvusStatus', health.milvus);
            this.updateStatusIndicator('neo4jStatus', health.neo4j);
            this.updateStatusIndicator('openaiStatus', health.openai);
        } catch (error) {
            console.error('Health check error:', error);
            this.updateStatusIndicator('milvusStatus', false);
            this.updateStatusIndicator('neo4jStatus', false);
            this.updateStatusIndicator('openaiStatus', false);
        }
    }

    updateStatusIndicator(elementId, isOnline) {
        const indicator = document.getElementById(elementId);
        if (!indicator) return;

        indicator.className = `status-indicator ${isOnline ? 'online' : 'offline'}`;
        indicator.innerHTML = `<i class="fas fa-circle"></i> ${isOnline ? 'Online' : 'Offline'}`;
    }

    // ===== EVENT LISTENERS =====

    initEventListeners() {
        // Chat input
        const chatInput = document.getElementById('chatInput');
        const sendBtn = document.getElementById('sendBtn');

        if (chatInput) {
            // Auto-resize textarea
            chatInput.addEventListener('input', () => {
                chatInput.style.height = 'auto';
                chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
            });

            // Send on Enter (but allow Shift+Enter for new lines)
            chatInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.handleSendMessage();
                }
            });
        }

        if (sendBtn) {
            sendBtn.addEventListener('click', () => this.handleSendMessage());
        }

        // Header buttons
        const starsBtn = document.getElementById('starsBtn');
        const settingsBtn = document.getElementById('settingsBtn');
        const logoutBtn = document.getElementById('logoutBtn');

        if (starsBtn) {
            starsBtn.addEventListener('click', () => this.showStarsModal());
        }

        if (settingsBtn) {
            settingsBtn.addEventListener('click', () => this.showSettingsModal());
        }

        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => this.logout());
        }

        // Chat controls
        const clearChatBtn = document.getElementById('clearChatBtn');
        const exportChatBtn = document.getElementById('exportChatBtn');

        if (clearChatBtn) {
            clearChatBtn.addEventListener('click', () => {
                if (confirm('Clear all chat messages?')) {
                    this.clearChat();
                }
            });
        }

        if (exportChatBtn) {
            exportChatBtn.addEventListener('click', () => this.exportChat());
        }

        // Learning panel toggle
        const panelToggle = document.getElementById('panelToggle');
        const learningPanel = document.getElementById('learningPanel');

        if (panelToggle && learningPanel) {
            panelToggle.addEventListener('click', () => {
                learningPanel.classList.toggle('collapsed');
            });
        }
    }

    initQuickActions() {
        const quickActions = document.querySelectorAll('.quick-action');
        quickActions.forEach(action => {
            action.addEventListener('click', () => {
                const question = action.getAttribute('data-question');
                if (question) {
                    const chatInput = document.getElementById('chatInput');
                    if (chatInput) {
                        chatInput.value = question;
                        chatInput.focus();
                    }
                }
            });
        });
    }

    initModals() {
        // Stars modal
        const starsModal = document.getElementById('starsModal');
        const closeStarsModal = document.getElementById('closeStarsModal');

        if (closeStarsModal) {
            closeStarsModal.addEventListener('click', () => this.hideStarsModal());
        }

        if (starsModal) {
            starsModal.addEventListener('click', (e) => {
                if (e.target === starsModal) {
                    this.hideStarsModal();
                }
            });
        }

        // Settings modal
        const settingsModal = document.getElementById('settingsModal');
        const closeSettingsModal = document.getElementById('closeSettingsModal');

        if (closeSettingsModal) {
            closeSettingsModal.addEventListener('click', () => this.hideSettingsModal());
        }

        if (settingsModal) {
            settingsModal.addEventListener('click', (e) => {
                if (e.target === settingsModal) {
                    this.hideSettingsModal();
                }
            });
        }

        // Settings controls
        const audienceSelect = document.getElementById('audienceSelect');
        const useGraphToggle = document.getElementById('useGraphToggle');
        const autoScrollToggle = document.getElementById('autoScrollToggle');

        if (audienceSelect) {
            audienceSelect.addEventListener('change', (e) => {
                this.settings.audience = e.target.value;
            });
        }

        if (useGraphToggle) {
            useGraphToggle.addEventListener('change', (e) => {
                this.settings.useGraph = e.target.checked;
            });
        }

        if (autoScrollToggle) {
            autoScrollToggle.addEventListener('change', (e) => {
                this.settings.autoScroll = e.target.checked;
            });
        }
    }

    // ===== MODAL METHODS =====

    showStarsModal() {
        const modal = document.getElementById('starsModal');
        if (modal) {
            modal.classList.add('active');
        }
    }

    hideStarsModal() {
        const modal = document.getElementById('starsModal');
        if (modal) {
            modal.classList.remove('active');
        }
    }

    showSettingsModal() {
        const modal = document.getElementById('settingsModal');
        if (modal) {
            modal.classList.add('active');
        }
    }

    hideSettingsModal() {
        const modal = document.getElementById('settingsModal');
        if (modal) {
            modal.classList.remove('active');
        }
    }

    showLoadingOverlay() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.add('active');
        }
    }

    hideLoadingOverlay() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.remove('active');
        }
    }

    // ===== UTILITY METHODS =====

    handleSendMessage() {
        const chatInput = document.getElementById('chatInput');
        if (!chatInput) return;

        const message = chatInput.value.trim();
        if (message) {
            this.sendMessage(message);
            chatInput.value = '';
            chatInput.style.height = 'auto';
        }
    }

    exportChat() {
        const messages = Array.from(document.querySelectorAll('.message')).map(msg => {
            const role = msg.classList.contains('user') ? 'User' : 'Assistant';
            const content = msg.querySelector('.message-content').textContent.trim();
            return `${role}: ${content}`;
        });

        const chatContent = messages.join('\n\n');
        const blob = new Blob([chatContent], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `chat-export-${new Date().toISOString().split('T')[0]}.txt`;
        a.click();
        
        URL.revokeObjectURL(url);
        this.showNotification('Chat exported successfully! 📥');
    }

    showNotification(message, type = 'success') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            background: ${type === 'success' ? '#4caf50' : '#f44336'};
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            z-index: 3000;
            transform: translateX(100%);
            transition: transform 0.3s ease;
        `;

        document.body.appendChild(notification);

        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);

        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new Dashboard();
});
