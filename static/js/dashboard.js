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
            
            // Make citation clickable - open URL if available, otherwise bookmark
            citationDiv.addEventListener('click', () => {
                console.log('🔍 CITATION CLICKED:', citation); // Debug info
                console.log('🔗 SOURCE URL VALUE:', `"${citation.source_url}"`); // Debug info
                console.log('📊 SOURCE:', citation.source); // Debug info
                console.log('📝 KIND:', citation.kind); // Debug info
                
                // Debug info logged to console
                
                if (citation.source_url && citation.source_url.trim() !== '') {
                    // Open the actual source URL in a new tab
                    console.log('✅ OPENING URL:', citation.source_url);
                    window.open(citation.source_url, '_blank');
                } else {
                    // No URL available, bookmark the content instead
                    console.log('⭐ BOOKMARKING CONTENT:', citation.doc_id, citation.title);
                    this.starContent(citation.doc_id, citation.title);
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
            } else if (content.kind === 'definition') {
                return `What is ${conceptName}? Please provide a detailed definition and explanation.`;
            } else if (content.kind === 'analogy') {
                return `Explain ${conceptName} using analogies and examples.`;
            } else if (content.kind === 'example') {
                return `Show me practical examples of ${conceptName}.`;
            } else {
                return `Explain ${conceptName} in detail with examples.`;
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
