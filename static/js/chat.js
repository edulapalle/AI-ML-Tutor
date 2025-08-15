// Chat application JavaScript with authentication support
class ChatApp {
    constructor() {
        this.conversationHistory = [];
        this.isLoading = false;
        this.userData = window.userData || {};
        this.currentQuizSession = null; // Track active quiz session
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
        this.loadLearningHistory();
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
                    // Check if this is a quiz request
                    if (question.toLowerCase().includes('quiz')) {
                        this.startQuiz();
                    } else {
                        document.getElementById('messageInput').value = question;
                        this.sendMessage();
                    }
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
                
                // Refresh learning history to show new explored topics
                this.loadLearningHistory();
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

    // Function removed - replaced with learning history functionality
    
    async loadLearningHistory() {
        try {
            const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
            if (!token) return;

            const response = await fetch('/api/learning-path', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.displayLearningHistory(data);
                console.log(`📚 Loaded learning history: ${data.explored_topics?.length || 0} topics explored`);
            }
        } catch (error) {
            console.error('❌ Failed to load learning history:', error);
        }
    }
    
    displayLearningHistory(historyData) {
        const learningHistorySection = document.getElementById('learningHistorySection');
        const learningHistoryList = document.getElementById('learningHistoryList');
        
        if (!learningHistorySection || !learningHistoryList) {
            return;
        }
        
        // Clear existing content
        learningHistoryList.innerHTML = '';
        
        // Display explored topics from history
        if (historyData.explored_topics && historyData.explored_topics.length > 0) {
            historyData.explored_topics.forEach((topic, index) => {
                const historyItem = this.createHistoryItem(topic, index);
                learningHistoryList.appendChild(historyItem);
            });
        } else {
            // Show empty state
            learningHistoryList.innerHTML = `
                <div class="no-history">
                    <i class="fas fa-lightbulb" style="color: #a0aec0; margin-right: 0.5rem;"></i>
                    Start chatting to build your learning history!
                </div>
            `;
        }
    }
    
    createHistoryItem(topic, index) {
        const historyItem = document.createElement('div');
        historyItem.className = 'learning-history-item';
        historyItem.onclick = () => this.askAboutConcept(topic);
        
        // Create a relative timestamp (this is simplified - in real implementation you'd use actual timestamps)
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
        
        return historyItem;
    }

    askAboutConcept(concept) {
        const conceptName = typeof concept === 'string' ? concept : (concept.name || concept.title || String(concept));
        const message = `Tell me more about ${conceptName}`;
        
        // Set the message in the input field
        const messageInput = document.getElementById('messageInput');
        if (messageInput) {
            messageInput.value = message;
        }
        
        // Send the message automatically
        this.sendMessage();
        
        console.log(`🎯 Asking about concept: ${conceptName}`);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Helper method to add HTML quiz content to chat
    addQuizToChat(htmlContent) {
        const chatMessages = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant quiz-message';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.innerHTML = htmlContent;
        
        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // ================================= QUIZ FUNCTIONALITY =================================
    
    async startQuiz() {
        console.log('🎯 Starting quiz...');
        
        try {
            // Show quiz loading message
            this.addMessageToChat('assistant', '🎯 Starting a quiz for you! Please wait...');
            
            // Request a quiz (default: machine learning, beginner, 5 questions)
            const response = await fetch('/api/quiz/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.userData.access_token}`
                },
                body: JSON.stringify({
                    topic: 'machine learning',
                    difficulty: 'beginner',
                    num_questions: 5
                })
            });

            if (response.ok) {
                const quizData = await response.json();
                this.currentQuizSession = quizData;
                this.displayQuizQuestion(quizData);
                console.log('✅ Quiz started successfully');
            } else {
                throw new Error(`Failed to start quiz: ${response.status}`);
            }
        } catch (error) {
            console.error('❌ Quiz start error:', error);
            this.addMessageToChat('assistant', '❌ Sorry, I couldn\'t start a quiz right now. Please try again later.');
        }
    }

    displayQuizQuestion(quizData) {
        const question = quizData.question;
        
        // Create quiz message with options
        let quizHtml = `
            <div class="quiz-container">
                <h4>🎯 Quiz Question ${quizData.progress}</h4>
                <p class="quiz-question"><strong>${question.question}</strong></p>
                <div class="quiz-options">
        `;
        
        question.options.forEach((option, index) => {
            quizHtml += `
                <button class="quiz-option" data-session-id="${quizData.session_id}" data-answer="${index}">
                    ${String.fromCharCode(65 + index)}. ${option}
                </button>
            `;
        });
        
        quizHtml += `
                </div>
                <p class="quiz-score">Score: ${quizData.score} | Progress: ${quizData.progress}</p>
            </div>
        `;
        
        // Add to chat
        this.addQuizToChat(quizHtml);
        
        // Bind click events to options
        setTimeout(() => {
            const options = document.querySelectorAll('.quiz-option');
            options.forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const sessionId = e.target.dataset.sessionId;
                    const answer = parseInt(e.target.dataset.answer);
                    this.submitQuizAnswer(sessionId, answer);
                });
            });
        }, 100);
    }

    async submitQuizAnswer(sessionId, answer) {
        console.log(`📝 Submitting quiz answer: ${answer} for session ${sessionId}`);
        
        try {
            // Disable all option buttons
            const options = document.querySelectorAll('.quiz-option');
            options.forEach(btn => {
                btn.disabled = true;
                if (parseInt(btn.dataset.answer) === answer) {
                    btn.classList.add('selected');
                }
            });
            
            const response = await fetch('/api/quiz/answer', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.userData.access_token}`
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    answer: answer
                })
            });

            if (response.ok) {
                const result = await response.json();
                this.handleQuizAnswerResult(result);
            } else {
                throw new Error(`Failed to submit answer: ${response.status}`);
            }
        } catch (error) {
            console.error('❌ Quiz answer error:', error);
            this.addMessageToChat('assistant', '❌ Sorry, I couldn\'t process your answer. Please try again.');
        }
    }

    handleQuizAnswerResult(result) {
        // Create comprehensive feedback message that clearly separates previous question from next
        const statusIcon = result.is_correct ? '✅' : '❌';
        const statusText = result.is_correct ? 'Correct!' : 'Incorrect.';
        
        const feedbackHtml = `
            <div class="quiz-feedback ${result.is_correct ? 'correct' : 'incorrect'}">
                <div class="feedback-header">
                    <strong>${statusIcon} ${statusText}</strong>
                </div>
                <div class="feedback-explanation">
                    ${result.feedback || 'No explanation provided.'}
                </div>
                <div class="feedback-score">
                    Score: ${result.score} | Progress: ${result.progress}
                </div>
            </div>
        `;
        
        this.addQuizToChat(feedbackHtml);
        
        if (result.completed) {
            // Quiz completed
            const completionHtml = `
                <div class="quiz-completion">
                    <h3>🎉 Quiz Completed!</h3>
                    <p><strong>Final Score: ${result.score}/${result.progress.split('/')[1]}</strong></p>
                    <p>Great job! ${result.score === parseInt(result.progress.split('/')[1]) ? 'Perfect score!' : 'Keep practicing to improve!'}</p>
                </div>
            `;
            this.addQuizToChat(completionHtml);
            this.currentQuizSession = null;
        } else if (result.question) {
            // Add clear separator before next question
            setTimeout(() => {
                const separatorHtml = `
                    <div class="quiz-separator">
                        <hr style="margin: 20px 0; border: 2px solid #ff9800;">
                        <p style="text-align: center; font-weight: bold; color: #ff9800;">Next Question</p>
                    </div>
                `;
                this.addQuizToChat(separatorHtml);
                
                // Display next question after separator
                setTimeout(() => {
                    this.displayQuizQuestion(result);
                }, 500);
            }, 2000); // Longer pause for user to read feedback
        }
    }


}

// Initialize the chat application
document.addEventListener('DOMContentLoaded', () => {
    window.chatApp = new ChatApp();
}); 