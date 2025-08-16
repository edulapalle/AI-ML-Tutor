/**
 * Dashboard JavaScript - Unified AI/ML Educational Platform
 * Handles chat, authentication, stars, and learning paths
 */

class Dashboard {
    constructor() {
        this.conversationHistory = [];
        this.currentUser = null;
        this.lastHealthStatus = null;
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

            this.initModals();
            
            // Load user data and populate UI
            await this.loadUserProfile();
            await this.loadStars();
            await this.updateLearningHistory();
            await this.checkSystemHealth();
            
            // Initialize agentic features
            await this.initAgenticFeatures();
            
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
        console.log('📤 SEND MESSAGE CALLED WITH:', message);
        console.log('📤 MESSAGE TYPE:', typeof message);
        
        // Safety check for undefined/null message
        if (!message || typeof message !== 'string') {
            console.error('❌ Invalid message passed to sendMessage:', message);
            return;
        }
        
        if (!message.trim()) {
            console.warn('⚠️ Empty message after trim');
            return;
        }

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

            // Update learning history and suggested concepts
            this.updateLearningHistory();
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
            const hasUrl = citation.source_url && citation.source_url.trim() !== '';
            citationDiv.className = hasUrl ? 'citation citation-link' : 'citation citation-bookmark';
            
            const titleEl = document.createElement('div');
            titleEl.className = 'citation-title';
            titleEl.textContent = citation.title || citation.doc_id;
            
            const sourceEl = document.createElement('div');
            sourceEl.className = 'citation-source';
            const actionIcon = hasUrl ? '🔗' : '⭐';
            sourceEl.textContent = `${actionIcon} ${citation.source || 'Unknown'} (${citation.kind || 'content'})`;
            
            citationDiv.appendChild(titleEl);
            citationDiv.appendChild(sourceEl);
            
            // Make citation clickable - open URL if available, otherwise show choice popup
            citationDiv.addEventListener('click', () => {
                console.log('🔍 CITATION CLICKED:', citation);
                console.log('🔗 SOURCE URL VALUE:', `"${citation.source_url}"`);
                console.log('📊 SOURCE:', citation.source);
                console.log('📝 KIND:', citation.kind);
                
                if (citation.source_url && citation.source_url.trim() !== '') {
                    // Green citations - Open YouTube URL directly
                    console.log('✅ OPENING URL:', citation.source_url);
                    window.open(citation.source_url, '_blank');
                } else {
                    // Orange citations - Show choice popup
                    console.log('🎯 SHOWING CHOICE POPUP FOR:', citation.doc_id, citation.title);
                    this.showCitationChoicePopup(citation);
                }
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
            console.log('🌟 STARRING CONTENT:', {docId, title, note});
            const token = this.getAuthToken();
            console.log('🔑 AUTH TOKEN:', token ? 'Present' : 'Missing');
            
            const payload = {
                doc_id: docId,
                note: note || `Starred: ${title}`
            };
            console.log('📤 STAR PAYLOAD:', payload);
            
            const response = await fetch('/api/star', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });

            console.log('📥 STAR RESPONSE:', response.status, response.statusText);
            
            if (response.ok) {
                const result = await response.json();
                console.log('✅ STAR SUCCESS:', result);
                this.showNotification('Content bookmarked! ⭐');
                await this.loadStars();
            } else {
                const error = await response.text();
                console.error('❌ STAR FAILED:', response.status, error);
                throw new Error(`Failed to star content: ${response.status}`);
            }
        } catch (error) {
            console.error('⚠️ STAR ERROR:', error);
            this.showNotification('Failed to bookmark content ❌');
        }
    }

    async loadStars() {
        try {
            console.log('⭐ LOADING STARS...');
            const token = this.getAuthToken();
            console.log('🔑 AUTH TOKEN for stars:', token ? 'Present' : 'Missing');
            
            const response = await fetch('/api/stars', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            console.log('📥 STARS RESPONSE:', response.status, response.statusText);

            if (response.ok) {
                const stars = await response.json();
                console.log('✅ STARS LOADED:', stars.length, 'items:', stars);
                this.updateStarCount(stars.length);
                this.updateStarsList(stars);
                return stars;
            } else {
                const error = await response.text();
                console.error('❌ STARS LOAD FAILED:', response.status, error);
            }
        } catch (error) {
            console.error('⚠️ LOAD STARS ERROR:', error);
        }
        return [];
    }

    async deleteStar(docId) {
        try {
            console.log('🗑️ DELETING STAR:', docId);
            const token = this.getAuthToken();
            
            const response = await fetch(`/api/star/${encodeURIComponent(docId)}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            console.log('📥 DELETE RESPONSE:', response.status, response.statusText);

            if (response.ok) {
                const result = await response.json();
                console.log('✅ DELETE SUCCESS:', result);
                this.showNotification('Bookmark removed! 🗑️');
                await this.loadStars(); // Refresh the list
            } else {
                const error = await response.text();
                console.error('❌ DELETE FAILED:', response.status, error);
                throw new Error(`Failed to delete bookmark: ${response.status}`);
            }
        } catch (error) {
            console.error('⚠️ DELETE ERROR:', error);
            this.showNotification('Failed to remove bookmark ❌');
        }
    }

    async askAboutBookmark(star) {
        console.log('🎯 ASK ABOUT BOOKMARK:', star);
        
        try {
            // Try to fetch the full content for richer context
            const content = await this.fetchBookmarkContent(star.doc_id);
            console.log('📖 FETCHED CONTENT:', content);
            
            // Generate a smart query based on the bookmark and content
            let query = this.generateBookmarkQuery(star, content);
            
            console.log('💬 GENERATED QUERY:', query);
            console.log('💬 QUERY TYPE:', typeof query);
            console.log('💬 QUERY LENGTH:', query ? query.length : 'undefined/null');
            
            // Ensure query is valid
            if (!query || typeof query !== 'string' || query.trim() === '') {
                console.warn('⚠️ Invalid query generated, using fallback');
                query = `Tell me about ${star.doc_id.replace(/[_-]/g, ' ')}`;
            }
            
            console.log('💬 FINAL QUERY:', query);
            
            // Set the message in the chat input
            const messageInput = document.getElementById('message');
            if (messageInput) {
                messageInput.value = query;
                messageInput.focus();
            }
            
            // Automatically send the message
            this.sendMessage(query);
            
            // Close any open modals
            const starsModal = document.getElementById('starsModal');
            if (starsModal && starsModal.style.display === 'block') {
                starsModal.style.display = 'none';
            }
            
            // Show notification with richer info
            const title = content?.title || star.doc_id.substring(0, 30);
            this.showNotification(`Asking about: ${title}... 💬`);
            
        } catch (error) {
            console.error('⚠️ Failed to fetch bookmark content:', error);
            
            // Fallback to basic query if content fetch fails
            let query = this.generateBookmarkQuery(star, null);
            
            console.log('💬 FALLBACK QUERY:', query);
            console.log('💬 FALLBACK QUERY TYPE:', typeof query);
            
            // Ensure fallback query is valid
            if (!query || typeof query !== 'string' || query.trim() === '') {
                console.warn('⚠️ Invalid fallback query, using simple fallback');
                query = `Tell me about ${star.doc_id.replace(/[_-]/g, ' ')}`;
            }
            
            console.log('💬 FINAL FALLBACK QUERY:', query);
            
            const messageInput = document.getElementById('message');
            if (messageInput) {
                messageInput.value = query;
                messageInput.focus();
            }
            
            this.sendMessage(query);
            
            const starsModal = document.getElementById('starsModal');
            if (starsModal && starsModal.style.display === 'block') {
                starsModal.style.display = 'none';
            }
            
            this.showNotification(`Asking about: ${star.doc_id.substring(0, 30)}... 💬`);
        }
    }

    async fetchBookmarkContent(docId) {
        const token = this.getAuthToken();
        console.log('📖 FETCHING BOOKMARK CONTENT:', docId);
        
        const response = await fetch(`/api/bookmark/${encodeURIComponent(docId)}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const content = await response.json();
            console.log('✅ CONTENT FETCHED:', content);
            return content;
        } else {
            console.warn('⚠️ Content fetch failed:', response.status, response.statusText);
            return null;
        }
    }

    generateBookmarkQuery(star, content = null) {
        // Use the fetched content title if available, otherwise extract from doc_id
        let conceptName = star.doc_id;
        
        if (content && content.title) {
            conceptName = content.title;
        } else {
            // Clean up the doc_id to make it more readable
            if (conceptName.includes('__')) {
                // For structured IDs like "neural-networks__definition__v1"
                conceptName = conceptName.split('__')[0].replace(/-/g, ' ');
            } else if (conceptName.includes('-')) {
                // For hyphenated concepts
                conceptName = conceptName.replace(/-/g, ' ');
            }
            
            // Capitalize each word
            conceptName = conceptName.replace(/\b\w/g, l => l.toUpperCase());
        }
        
        // Generate contextual query based on content type and note
        if (content) {
            if (content.source === 'youtube_creator_videos') {
                // For YouTube content, ask about the video
                return `Tell me about the "${conceptName}" video. What are the key concepts covered?`;
            } else {
                // Use the same type-specific logic as viewCitationContent
                switch (content.kind.toLowerCase()) {
                    case 'definition':
                        return `What is ${conceptName}? Please provide a detailed definition and explanation.`;
                    case 'analogy':
                        return `Explain ${conceptName} using analogies and real-world comparisons to help me understand it better.`;
                    case 'example':
                        return `Give me more practical examples and use cases of ${conceptName}. Show me how it works in different scenarios.`;
                    case 'mistake':
                        return `What are common mistakes people make with ${conceptName}? How can I avoid these pitfalls?`;
                    case 'quiz':
                        return `Give me a quiz about ${conceptName}. Ask me questions to test my understanding and provide interactive learning.`;
                    case 'related':
                        return `What concepts are related to ${conceptName}? Show me how it connects to other ML/AI topics.`;
                    case 'content':
                        return `Tell me more about ${conceptName}. Provide comprehensive information and insights.`;
                    default:
                        return `Explain ${conceptName} in detail with examples and practical applications.`;
                }
            }
        } else {
            // Fallback to basic queries when no content is available
            if (star.note && star.note.toLowerCase().includes('starred:')) {
                return `Explain ${conceptName} in detail`;
            } else if (star.note) {
                return `Tell me about ${conceptName}. ${star.note}`;
            } else {
                return `What is ${conceptName}? Please explain with examples.`;
            }
        }
    }

    showCitationChoicePopup(citation) {
        // Create popup overlay
        const overlay = document.createElement('div');
        overlay.className = 'popup-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
            backdrop-filter: blur(4px);
        `;

        // Create popup content
        const popup = document.createElement('div');
        popup.className = 'citation-choice-popup';
        popup.style.cssText = `
            background: white;
            border-radius: 12px;
            padding: 2rem;
            max-width: 400px;
            width: 90%;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            text-align: center;
            animation: popupSlideIn 0.3s ease-out;
        `;

        popup.innerHTML = `
            <h3 style="margin: 0 0 1rem 0; color: #333; font-size: 1.2rem;">
                What would you like to do?
            </h3>
            <p style="margin: 0 0 2rem 0; color: #666; font-size: 0.95rem;">
                <strong>${citation.title}</strong><br/>
                <small>${citation.kind} content</small>
            </p>
            <div style="display: flex; gap: 1rem; justify-content: center;">
                <button id="viewContentBtn" style="
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border: none;
                    padding: 0.75rem 1.5rem;
                    border-radius: 8px;
                    cursor: pointer;
                    font-weight: 600;
                    transition: transform 0.2s ease;
                ">
                    📖 View Content
                </button>
                <button id="bookmarkBtn" style="
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    color: white;
                    border: none;
                    padding: 0.75rem 1.5rem;
                    border-radius: 8px;
                    cursor: pointer;
                    font-weight: 600;
                    transition: transform 0.2s ease;
                ">
                    ⭐ Bookmark
                </button>
            </div>
            <button id="cancelBtn" style="
                background: none;
                border: none;
                color: #999;
                margin-top: 1rem;
                cursor: pointer;
                font-size: 0.9rem;
            ">
                Cancel
            </button>
        `;

        // Add CSS animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes popupSlideIn {
                from {
                    opacity: 0;
                    transform: translateY(-20px) scale(0.9);
                }
                to {
                    opacity: 1;
                    transform: translateY(0) scale(1);
                }
            }
        `;
        document.head.appendChild(style);

        overlay.appendChild(popup);
        document.body.appendChild(overlay);

        // Add event listeners
        const viewContentBtn = popup.querySelector('#viewContentBtn');
        const bookmarkBtn = popup.querySelector('#bookmarkBtn');
        const cancelBtn = popup.querySelector('#cancelBtn');

        // Hover effects
        [viewContentBtn, bookmarkBtn].forEach(btn => {
            btn.addEventListener('mouseenter', () => {
                btn.style.transform = 'translateY(-2px)';
            });
            btn.addEventListener('mouseleave', () => {
                btn.style.transform = 'translateY(0)';
            });
        });

        // Button actions
        viewContentBtn.addEventListener('click', () => {
            console.log('📖 USER CHOSE: View Content');
            this.closePopup(overlay);
            this.viewCitationContent(citation);
        });

        bookmarkBtn.addEventListener('click', () => {
            console.log('⭐ USER CHOSE: Bookmark');
            this.closePopup(overlay);
            this.starContent(citation.doc_id, citation.title);
        });

        cancelBtn.addEventListener('click', () => {
            console.log('❌ USER CHOSE: Cancel');
            this.closePopup(overlay);
        });

        // Close on overlay click
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                this.closePopup(overlay);
            }
        });

        // Close on Escape key
        const escapeHandler = (e) => {
            if (e.key === 'Escape') {
                this.closePopup(overlay);
                document.removeEventListener('keydown', escapeHandler);
            }
        };
        document.addEventListener('keydown', escapeHandler);
    }

    closePopup(overlay) {
        overlay.style.animation = 'popupSlideOut 0.2s ease-in forwards';
        setTimeout(() => {
            if (overlay.parentNode) {
                overlay.parentNode.removeChild(overlay);
            }
        }, 200);

        // Add slide out animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes popupSlideOut {
                from {
                    opacity: 1;
                    transform: scale(1);
                }
                to {
                    opacity: 0;
                    transform: scale(0.9);
                }
            }
        `;
        document.head.appendChild(style);
    }

    viewCitationContent(citation) {
        console.log('📖 VIEWING CONTENT FOR:', citation);
        
        // Create a smart query to ask about this specific citation
        const conceptName = citation.title || citation.doc_id.replace(/[_-]/g, ' ');
        let query;
        
        // Generate type-specific queries based on content category
        switch (citation.kind.toLowerCase()) {
            case 'definition':
                query = `What is ${conceptName}? Please provide a detailed definition and explanation.`;
                break;
            case 'analogy':
                query = `Explain ${conceptName} using analogies and real-world comparisons to help me understand it better.`;
                break;
            case 'example':
                query = `Give me more practical examples and use cases of ${conceptName}. Show me how it works in different scenarios.`;
                break;
            case 'mistake':
                query = `What are common mistakes people make with ${conceptName}? How can I avoid these pitfalls?`;
                break;
            case 'quiz':
                query = `Give me a quiz about ${conceptName}. Ask me questions to test my understanding and provide interactive learning.`;
                break;
            case 'related':
                query = `What concepts are related to ${conceptName}? Show me how it connects to other ML/AI topics.`;
                break;
            case 'content':
                query = `Tell me more about ${conceptName}. Provide comprehensive information and insights.`;
                break;
            case 'video': // For YouTube content
                query = `Tell me about the key concepts covered in this ${conceptName} video. What are the main learning points?`;
                break;
            default:
                query = `Explain ${conceptName} in detail with examples and practical applications.`;
                break;
        }
        
        console.log('💬 GENERATED TYPE-SPECIFIC QUERY:', query);
        console.log('🏷️ CONTENT TYPE:', citation.kind);
        
        // Set the message in the chat input and send it
        const messageInput = document.getElementById('message');
        if (messageInput) {
            messageInput.value = query;
            messageInput.focus();
        }
        
        this.sendMessage(query);
        this.showNotification(`${this.getActionIcon(citation.kind)} ${conceptName}`);
    }

    getActionIcon(kind) {
        const iconMap = {
            'definition': '📚 Learning about:',
            'analogy': '🔍 Exploring analogies for:',
            'example': '💡 Getting examples of:',
            'mistake': '⚠️ Learning mistakes about:',
            'quiz': '🧠 Taking quiz on:',
            'related': '🔗 Finding related topics to:',
            'content': '📖 Reading about:',
            'video': '🎥 Watching content about:'
        };
        return iconMap[kind.toLowerCase()] || '📖 Viewing content:';
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
                starItem.style.display = 'flex';
                starItem.style.justifyContent = 'space-between';
                starItem.style.alignItems = 'center';
                starItem.style.padding = '0.5rem';
                starItem.style.marginBottom = '0.5rem';
                starItem.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
                starItem.style.borderRadius = '4px';
                
                const contentDiv = document.createElement('div');
                contentDiv.style.cursor = 'pointer';
                contentDiv.style.flex = '1';
                contentDiv.style.transition = 'all 0.2s ease';
                contentDiv.title = 'Click to ask about this concept';
                contentDiv.innerHTML = `
                    <div class="star-title" style="font-weight: 600; font-size: 0.85rem; color: #667eea;">${star.doc_id.substring(0, 30)}...</div>
                    ${star.note ? `<div class="star-note" style="color: #666; font-size: 0.8rem;">${star.note.substring(0, 50)}...</div>` : ''}
                    <div style="font-size: 0.7rem; color: #999; margin-top: 0.2rem;">💬 Click to ask about this</div>
                `;
                
                // Add hover effect
                contentDiv.addEventListener('mouseenter', () => {
                    contentDiv.style.backgroundColor = 'rgba(102, 126, 234, 0.1)';
                    contentDiv.style.borderRadius = '4px';
                });
                contentDiv.addEventListener('mouseleave', () => {
                    contentDiv.style.backgroundColor = 'transparent';
                });
                
                // Make bookmark clickable to trigger chat
                contentDiv.addEventListener('click', () => {
                    this.askAboutBookmark(star);
                });
                
                const deleteBtn = document.createElement('button');
                deleteBtn.innerHTML = '🗑️';
                deleteBtn.style.background = 'none';
                deleteBtn.style.border = 'none';
                deleteBtn.style.cursor = 'pointer';
                deleteBtn.style.fontSize = '1rem';
                deleteBtn.style.padding = '0.25rem';
                deleteBtn.title = 'Remove bookmark';
                deleteBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.deleteStar(star.doc_id);
                });
                
                starItem.appendChild(contentDiv);
                starItem.appendChild(deleteBtn);
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
                starCard.style.position = 'relative';
                starCard.style.padding = '1rem';
                starCard.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
                starCard.style.borderRadius = '8px';
                starCard.style.marginBottom = '1rem';
                starCard.style.border = '1px solid rgba(102, 126, 234, 0.2)';
                
                // Delete button (top-right corner)
                const deleteBtn = document.createElement('button');
                deleteBtn.innerHTML = '🗑️';
                deleteBtn.style.position = 'absolute';
                deleteBtn.style.top = '0.5rem';
                deleteBtn.style.right = '0.5rem';
                deleteBtn.style.background = 'rgba(255, 255, 255, 0.8)';
                deleteBtn.style.border = 'none';
                deleteBtn.style.borderRadius = '50%';
                deleteBtn.style.width = '2rem';
                deleteBtn.style.height = '2rem';
                deleteBtn.style.cursor = 'pointer';
                deleteBtn.style.fontSize = '0.9rem';
                deleteBtn.title = 'Remove bookmark';
                deleteBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.deleteStar(star.doc_id);
                });
                
                // Content
                const contentDiv = document.createElement('div');
                contentDiv.style.cursor = 'pointer';
                contentDiv.style.transition = 'all 0.2s ease';
                contentDiv.title = 'Click to ask about this concept';
                contentDiv.innerHTML = `
                    <div class="star-card-title" style="font-weight: 600; margin-bottom: 0.5rem; padding-right: 2rem; color: #667eea;">${star.doc_id}</div>
                    ${star.note ? `<div class="star-card-note" style="color: #666; margin-bottom: 0.5rem;">${star.note}</div>` : ''}
                    ${star.created_at ? `<div class="star-card-date" style="color: #999; font-size: 0.8rem;">${new Date(star.created_at).toLocaleDateString()}</div>` : ''}
                    <div style="font-size: 0.8rem; color: #667eea; margin-top: 0.5rem; font-weight: 500;">💬 Click to ask about this concept</div>
                `;
                
                // Add hover effect
                contentDiv.addEventListener('mouseenter', () => {
                    starCard.style.backgroundColor = 'rgba(102, 126, 234, 0.15)';
                    starCard.style.transform = 'translateY(-2px)';
                });
                contentDiv.addEventListener('mouseleave', () => {
                    starCard.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
                    starCard.style.transform = 'translateY(0px)';
                });
                
                // Make bookmark clickable to trigger chat
                contentDiv.addEventListener('click', () => {
                    this.askAboutBookmark(star);
                });
                
                starCard.appendChild(contentDiv);
                starCard.appendChild(deleteBtn);
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

    async updateLearningHistory() {
        try {
            const response = await fetch('/api/learning-path', {
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.displayLearningHistory(data.explored_topics || []);
            }
        } catch (error) {
            console.error('Failed to load learning history:', error);
        }
    }

    displayLearningHistory(topics) {
        const historyList = document.getElementById('historyList');
        if (!historyList) return;

        historyList.innerHTML = '';
        
        if (topics.length === 0) {
            historyList.innerHTML = '<p class="no-history">Start chatting to build your learning history!</p>';
            return;
        }

        // Show most recent topics first
        topics.slice(0, 10).forEach((topic, index) => {
            const historyItem = document.createElement('div');
            historyItem.className = 'history-item';
            
            const timeAgo = index === 0 ? 'Just now' : 
                           index === 1 ? 'A moment ago' : 
                           index < 5 ? 'Recently' : 'Earlier';
            
            historyItem.innerHTML = `
                <div class="history-icon">
                    <i class="fas fa-check-circle"></i>
                </div>
                <div class="history-content">
                    <div class="history-title">${this.escapeHtml(topic)}</div>
                    <div class="history-timestamp">${timeAgo}</div>
                </div>
            `;
            
            historyItem.addEventListener('click', () => {
                this.sendMessage(`Tell me more about ${topic}`);
            });
            
            historyList.appendChild(historyItem);
        });
    }

    updateNextConcepts(concepts) {
        const conceptsList = document.querySelector('.concepts-list');
        if (!conceptsList) return;

        conceptsList.innerHTML = '';
        
        if (!concepts || concepts.length === 0) {
            conceptsList.innerHTML = '<p style="color: #999; font-style: italic;">No suggestions yet</p>';
            return;
        }

        concepts.forEach(concept => {
            const conceptItem = document.createElement('div');
            conceptItem.className = 'concept-item';
            conceptItem.innerHTML = `<div class="concept-name">${this.escapeHtml(concept)}</div>`;
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

            // Store health status for modal updates
            this.lastHealthStatus = health;

            this.updateStatusIndicator('milvusStatus', health.milvus);
            this.updateStatusIndicator('neo4jStatus', health.neo4j);
            this.updateStatusIndicator('openaiStatus', health.openai);
        } catch (error) {
            console.error('Health check error:', error);
            
            // Store failed health status
            this.lastHealthStatus = {
                milvus: false,
                neo4j: false,
                openai: false
            };

            this.updateStatusIndicator('milvusStatus', false);
            this.updateStatusIndicator('neo4jStatus', false);
            this.updateStatusIndicator('openaiStatus', false);
        }
        
        // Update profile modal status indicators if modal exists
        this.updateProfileModalStatus();
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
        const profileBtn = document.getElementById('profileBtn');
        const starsBtn = document.getElementById('starsBtn');
        const settingsBtn = document.getElementById('settingsBtn');
        const logoutBtn = document.getElementById('logoutBtn');

        if (profileBtn) {
            profileBtn.addEventListener('click', () => this.showProfileModal());
        }

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

        // Learning History Panel - no toggle needed, always visible
    }



    initModals() {
        // Profile modal
        const profileModal = document.getElementById('profileModal');
        const closeProfileModal = document.getElementById('closeProfileModal');

        if (closeProfileModal) {
            closeProfileModal.addEventListener('click', () => this.hideProfileModal());
        }

        if (profileModal) {
            profileModal.addEventListener('click', (e) => {
                if (e.target === profileModal) {
                    this.hideProfileModal();
                }
            });
        }

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

    showProfileModal() {
        // Update modal content with current user data
        this.updateProfileModal();
        
        const modal = document.getElementById('profileModal');
        if (modal) {
            modal.classList.add('active');
        }
    }

    hideProfileModal() {
        const modal = document.getElementById('profileModal');
        if (modal) {
            modal.classList.remove('active');
        }
    }

    updateProfileModal() {
        if (!this.currentUser) return;

        // Update basic info
        const modalUsername = document.getElementById('modalUsername');
        const modalUserLevel = document.getElementById('modalUserLevel');
        const modalUserStage = document.getElementById('modalUserStage');
        const modalUserAge = document.getElementById('modalUserAge');

        if (modalUsername) modalUsername.textContent = this.currentUser.username;
        if (modalUserLevel) modalUserLevel.textContent = this.currentUser.study_level.charAt(0).toUpperCase() + this.currentUser.study_level.slice(1);
        if (modalUserStage) modalUserStage.textContent = this.currentUser.current_stage.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
        if (modalUserAge) modalUserAge.textContent = `${this.currentUser.user_age} years`;

        // Update interests
        const modalUserInterests = document.getElementById('modalUserInterests');
        if (modalUserInterests && this.currentUser.topics_of_interest) {
            modalUserInterests.innerHTML = '';
            this.currentUser.topics_of_interest.forEach(interest => {
                const tag = document.createElement('span');
                tag.className = 'interest-tag';
                tag.textContent = interest.charAt(0).toUpperCase() + interest.slice(1);
                modalUserInterests.appendChild(tag);
            });
        }

        // Update system status in modal (copy from main display)
        const modalMilvusStatus = document.getElementById('modalMilvusStatus');
        const modalNeo4jStatus = document.getElementById('modalNeo4jStatus');
        const modalOpenaiStatus = document.getElementById('modalOpenaiStatus');
        
        const mainMilvusStatus = document.getElementById('milvusStatus');
        const mainNeo4jStatus = document.getElementById('neo4jStatus');
        const mainOpenaiStatus = document.getElementById('openaiStatus');

        if (modalMilvusStatus && mainMilvusStatus) {
            modalMilvusStatus.innerHTML = mainMilvusStatus.innerHTML;
            modalMilvusStatus.className = mainMilvusStatus.className;
        }
        if (modalNeo4jStatus && mainNeo4jStatus) {
            modalNeo4jStatus.innerHTML = mainNeo4jStatus.innerHTML;
            modalNeo4jStatus.className = mainNeo4jStatus.className;
        }
        if (modalOpenaiStatus && mainOpenaiStatus) {
            modalOpenaiStatus.innerHTML = mainOpenaiStatus.innerHTML;
            modalOpenaiStatus.className = mainOpenaiStatus.className;
        }
    }

    updateProfileModalStatus() {
        // Only update if modal elements exist (modal might not be in DOM yet)
        const modalMilvusStatus = document.getElementById('modalMilvusStatus');
        const modalNeo4jStatus = document.getElementById('modalNeo4jStatus');
        const modalOpenaiStatus = document.getElementById('modalOpenaiStatus');
        
        if (!modalMilvusStatus || !modalNeo4jStatus || !modalOpenaiStatus) {
            return; // Modal not rendered yet
        }
        
        // Since main status indicators don't exist, we'll update from last health check
        // This will be called after health check, so we can fetch current status
        this.updateModalStatusIndicator('modalMilvusStatus', this.lastHealthStatus?.milvus);
        this.updateModalStatusIndicator('modalNeo4jStatus', this.lastHealthStatus?.neo4j);
        this.updateModalStatusIndicator('modalOpenaiStatus', this.lastHealthStatus?.openai);
    }

    updateModalStatusIndicator(elementId, isOnline) {
        const indicator = document.getElementById(elementId);
        if (!indicator) return;

        if (isOnline) {
            indicator.style.color = '#48bb78';
            indicator.innerHTML = '<i class="fas fa-circle"></i> Connected';
        } else {
            indicator.style.color = '#f56565';
            indicator.innerHTML = '<i class="fas fa-circle"></i> Disconnected';
        }
    }

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

    // ===== AGENTIC LEARNING FEATURES =====

    async initAgenticFeatures() {
        console.log('🤖 Initializing agentic learning features...');
        
        try {
            // Add agentic insights button to UI
            this.createAgenticDashboard();
            
            // Schedule periodic analysis
            this.scheduleAgenticAnalysis();
            
            // Load initial insights
            await this.loadAgenticInsights();
            
            console.log('✅ Agentic features initialized');
        } catch (error) {
            console.error('❌ Failed to initialize agentic features:', error);
        }
    }

    createAgenticDashboard() {
        // Add agentic insights section to the learning panel
        const learningPanel = document.getElementById('learningPanel');
        if (!learningPanel) return;

        // Check if agentic section already exists
        if (document.getElementById('agenticInsights')) return;

        const agenticSection = document.createElement('div');
        agenticSection.className = 'agentic-insights';
        agenticSection.id = 'agenticInsights';
        agenticSection.innerHTML = `
            <h4>🤖 AI Learning Coach</h4>
            <div class="agentic-controls">
                <button class="btn-agentic" onclick="dashboard.runFullAnalysis()">
                    <i class="fas fa-brain"></i> Analyze My Learning
                </button>
                <button class="btn-agentic" onclick="dashboard.getRecommendations()">
                    <i class="fas fa-route"></i> Get Path Suggestions
                </button>
            </div>
            <div class="insights-list" id="insightsList">
                <p class="no-insights">Click "Analyze My Learning" to get personalized insights!</p>
            </div>
        `;

        // Insert after next concepts
        const nextConcepts = document.getElementById('nextConcepts');
        if (nextConcepts && nextConcepts.parentNode) {
            nextConcepts.parentNode.insertBefore(agenticSection, nextConcepts.nextSibling);
        }

        // Add CSS styles for agentic features
        this.addAgenticStyles();
    }

    addAgenticStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .agentic-insights {
                margin-bottom: 2rem;
                padding: 1rem;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 12px;
                color: white;
            }

            .agentic-insights h4 {
                margin: 0 0 1rem 0;
                color: white;
                font-size: 1rem;
                font-weight: 600;
            }

            .agentic-controls {
                display: flex;
                gap: 0.5rem;
                margin-bottom: 1rem;
                flex-wrap: wrap;
            }

            .btn-agentic {
                background: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.3);
                color: white;
                padding: 0.5rem 1rem;
                border-radius: 8px;
                font-size: 0.8rem;
                cursor: pointer;
                transition: all 0.3s ease;
                flex: 1;
                min-width: 120px;
            }

            .btn-agentic:hover {
                background: rgba(255, 255, 255, 0.3);
                transform: translateY(-1px);
            }

            .btn-agentic i {
                margin-right: 0.5rem;
            }

            .insights-list {
                max-height: 200px;
                overflow-y: auto;
            }

            .insight-item {
                background: rgba(255, 255, 255, 0.1);
                padding: 0.75rem;
                border-radius: 8px;
                margin-bottom: 0.5rem;
                border-left: 3px solid #ffd700;
            }

            .insight-type {
                font-weight: 600;
                font-size: 0.8rem;
                text-transform: uppercase;
                color: #ffd700;
                margin-bottom: 0.25rem;
            }

            .insight-suggestion {
                font-size: 0.9rem;
                line-height: 1.4;
            }

            .insight-confidence {
                font-size: 0.7rem;
                opacity: 0.8;
                margin-top: 0.25rem;
            }

            .no-insights {
                text-align: center;
                font-style: italic;
                opacity: 0.8;
                margin: 0;
                font-size: 0.9rem;
            }

            .analysis-loading {
                text-align: center;
                padding: 1rem;
            }

            .loading-spinner {
                display: inline-block;
                width: 16px;
                height: 16px;
                border: 2px solid rgba(255,255,255,0.3);
                border-radius: 50%;
                border-top-color: white;
                animation: spin 1s ease-in-out infinite;
                margin-right: 0.5rem;
            }

            @keyframes spin {
                to { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
    }

    scheduleAgenticAnalysis() {
        // Run analysis every 10 interactions
        let interactionCount = 0;
        const originalSendMessage = this.sendMessage.bind(this);
        
        this.sendMessage = async function(message) {
            const result = await originalSendMessage(message);
            interactionCount++;
            
            // Trigger analysis every 10 interactions
            if (interactionCount % 10 === 0) {
                console.log('🤖 Triggering scheduled agentic analysis');
                setTimeout(() => this.loadAgenticInsights(), 2000); // Delay to not interfere with chat
            }
            
            return result;
        }.bind(this);
    }

    async loadAgenticInsights() {
        try {
            const response = await fetch('/api/agentic/insights/' + this.currentUser.id, {
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.displayInsights(data.insights);
            }
        } catch (error) {
            console.error('Failed to load agentic insights:', error);
        }
    }

    displayInsights(insights) {
        const insightsList = document.getElementById('insightsList');
        if (!insightsList) return;

        if (!insights || insights.length === 0) {
            insightsList.innerHTML = '<p class="no-insights">No insights available yet. Keep learning!</p>';
            return;
        }

        const insightsHtml = insights.slice(0, 3).map(insight => `
            <div class="insight-item">
                <div class="insight-type">${insight.type.replace('_', ' ')}</div>
                <div class="insight-suggestion">${insight.action_suggestion}</div>
                <div class="insight-confidence">Confidence: ${Math.round(insight.confidence * 100)}%</div>
            </div>
        `).join('');

        insightsList.innerHTML = insightsHtml;
    }

    async runFullAnalysis() {
        console.log('🤖 Running full agentic analysis...');
        
        const insightsList = document.getElementById('insightsList');
        if (insightsList) {
            insightsList.innerHTML = `
                <div class="analysis-loading">
                    <div class="loading-spinner"></div>
                    Analyzing your learning patterns...
                </div>
            `;
        }

        try {
            const response = await fetch('/api/agentic/analyze', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const analysis = await response.json();
                this.displayFullAnalysis(analysis);
                this.showNotification('🤖 Learning analysis complete!');
            } else {
                throw new Error('Analysis failed');
            }
        } catch (error) {
            console.error('Failed to run full analysis:', error);
            this.showNotification('❌ Analysis failed. Please try again.', 'error');
            
            if (insightsList) {
                insightsList.innerHTML = '<p class="no-insights">Analysis failed. Please try again.</p>';
            }
        }
    }

    displayFullAnalysis(analysis) {
        const insightsList = document.getElementById('insightsList');
        if (!insightsList) return;

        const synthesis = analysis.synthesis || {};
        const insights = analysis.comprehension_insights || [];
        const recommendations = analysis.learning_path_recommendations || [];

        let html = '';

        // Show key insights
        if (synthesis.key_insights) {
            html += `
                <div class="insight-item">
                    <div class="insight-type">Key Insights</div>
                    <div class="insight-suggestion">${synthesis.key_insights.join('. ')}</div>
                </div>
            `;
        }

        // Show next steps
        if (synthesis.next_steps) {
            html += `
                <div class="insight-item">
                    <div class="insight-type">Recommended Actions</div>
                    <div class="insight-suggestion">${synthesis.next_steps}</div>
                </div>
            `;
        }

        // Show top comprehension insight
        if (insights.length > 0) {
            const topInsight = insights[0];
            html += `
                <div class="insight-item">
                    <div class="insight-type">${topInsight.insight_type.replace('_', ' ')}</div>
                    <div class="insight-suggestion">${topInsight.action_suggestion}</div>
                    <div class="insight-confidence">Confidence: ${Math.round(topInsight.confidence * 100)}%</div>
                </div>
            `;
        }

        if (html) {
            insightsList.innerHTML = html;
        } else {
            insightsList.innerHTML = '<p class="no-insights">Analysis complete. Keep learning to build insights!</p>';
        }
    }

    async getRecommendations() {
        console.log('🤖 Getting learning path recommendations...');
        
        try {
            const response = await fetch('/api/agentic/recommendations', {
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.displayRecommendations(data.recommendations);
                this.showNotification('🤖 New learning recommendations ready!');
            } else {
                throw new Error('Failed to get recommendations');
            }
        } catch (error) {
            console.error('Failed to get recommendations:', error);
            this.showNotification('❌ Failed to get recommendations. Please try again.', 'error');
        }
    }

    displayRecommendations(recommendations) {
        if (!recommendations || recommendations.length === 0) {
            this.showNotification('No new recommendations at this time', 'info');
            return;
        }

        // Update the next concepts section with AI recommendations
        const conceptsList = document.querySelector('.concepts-list');
        if (conceptsList) {
            const aiRecs = recommendations.slice(0, 2); // Top 2 recommendations
            
            const recHtml = aiRecs.map(rec => `
                <div class="concept-item ai-recommended" title="${rec.reasoning}">
                    <div class="concept-name">🤖 ${rec.next_topics[0] || 'AI Suggestion'}</div>
                    <div class="concept-reasoning">${rec.reasoning.substring(0, 60)}...</div>
                </div>
            `).join('');

            // Prepend AI recommendations
            conceptsList.innerHTML = recHtml + conceptsList.innerHTML;
        }

        // Show in insights panel too
        const insightsList = document.getElementById('insightsList');
        if (insightsList) {
            const recHtml = recommendations.slice(0, 2).map(rec => `
                <div class="insight-item">
                    <div class="insight-type">Path Recommendation</div>
                    <div class="insight-suggestion">Next: ${rec.next_topics.join(', ')}</div>
                    <div class="insight-confidence">Reasoning: ${rec.reasoning}</div>
                </div>
            `).join('');

            insightsList.innerHTML = recHtml;
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new Dashboard();
});
