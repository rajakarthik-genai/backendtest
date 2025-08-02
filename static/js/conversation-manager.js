/**
 * Frontend JavaScript for handling conversation limits (Claude-style)
 */

class ConversationManager {
    constructor() {
        this.currentConversationId = null;
        this.userId = null;
        this.remainingMessages = 100;
        this.showWarnings = true;
        this.apiBase = '/api/v1/chat';
    }

    async initialize(userId) {
        this.userId = userId;
        await this.loadOrCreateConversation();
        this.setupEventListeners();
    }

    async loadOrCreateConversation() {
        try {
            // Try to get existing conversations
            const response = await fetch(`${this.apiBase}/conversations`, {
                headers: { 
                    'Authorization': `Bearer ${this.getToken()}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                const conversations = data.data.conversations;
                
                // Find an active conversation that's not full
                const activeConv = conversations.find(conv => !conv.is_full);
                
                if (activeConv) {
                    this.currentConversationId = activeConv.conversation_id;
                    await this.updateConversationStatus();
                } else {
                    // All conversations are full, create a new one
                    await this.createNewConversation();
                }
            } else {
                // No conversations exist, create new one
                await this.createNewConversation();
            }
        } catch (error) {
            console.error('Error loading conversation:', error);
            await this.createNewConversation();
        }
    }

    async createNewConversation() {
        try {
            const response = await fetch(`${this.apiBase}/conversations/new`, {
                method: 'POST',
                headers: { 
                    'Authorization': `Bearer ${this.getToken()}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.currentConversationId = data.data.conversation_id;
                this.remainingMessages = data.data.remaining_messages;
                this.updateUI();
                this.showNotification('New conversation started', 'success');
            } else {
                throw new Error('Failed to create conversation');
            }
        } catch (error) {
            console.error('Error creating conversation:', error);
            this.showNotification('Failed to create new conversation', 'error');
        }
    }

    async updateConversationStatus() {
        try {
            const response = await fetch(
                `${this.apiBase}/conversations/${this.currentConversationId}/status`,
                { 
                    headers: { 
                        'Authorization': `Bearer ${this.getToken()}`,
                        'Content-Type': 'application/json'
                    } 
                }
            );
            
            if (response.ok) {
                const data = await response.json();
                this.remainingMessages = data.data.remaining_messages;
                this.updateUI();
                
                // Show warning if near limit
                if (data.data.warning && this.showWarnings) {
                    this.showLimitWarning(data.data.remaining_messages);
                }
            }
        } catch (error) {
            console.error('Error updating conversation status:', error);
        }
    }

    async sendMessage(message, expertMode = false) {
        try {
            const response = await fetch(`${this.apiBase}/message`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getToken()}`
                },
                body: JSON.stringify({
                    conversation_id: this.currentConversationId,
                    message: message,
                    expert_opinion: expertMode,
                    include_context: true,
                    context_window: 10
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                
                if (errorData.detail?.error === 'conversation_limit_reached') {
                    await this.handleConversationLimitReached(message);
                    return;
                }
                
                throw new Error(errorData.detail || 'Failed to send message');
            }

            // Handle JSON response (not streaming in this implementation)
            const responseData = await response.json();
            
            // Update remaining messages count
            if (responseData.remaining_messages !== undefined) {
                this.remainingMessages = responseData.remaining_messages;
                this.updateUI();
            }
            
            // Show warning if provided
            if (responseData.conversation_warning) {
                this.showLimitWarning(this.remainingMessages);
            }
            
            return responseData;

        } catch (error) {
            console.error('Error sending message:', error);
            this.showNotification('Failed to send message', 'error');
            throw error;
        }
    }

    async handleConversationLimitReached(originalMessage = null) {
        const modal = this.createLimitReachedModal(originalMessage);
        document.body.appendChild(modal);
        
        // Show modal with animation
        setTimeout(() => modal.classList.add('show'), 10);
    }

    createLimitReachedModal(originalMessage) {
        const modal = document.createElement('div');
        modal.className = 'conversation-limit-modal';
        modal.innerHTML = `
            <div class="modal-overlay"></div>
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Conversation Limit Reached</h3>
                    <button class="close-btn" onclick="this.closest('.conversation-limit-modal').remove()">×</button>
                </div>
                <div class="modal-body">
                    <div class="limit-icon">💬</div>
                    <p>You've reached the maximum number of messages (100) for this conversation.</p>
                    <p>Would you like to start a new conversation to continue?</p>
                    ${originalMessage ? `<p class="pending-message"><strong>Your message:</strong> "${originalMessage.substring(0, 100)}..."</p>` : ''}
                </div>
                <div class="modal-actions">
                    <button class="btn btn-primary" onclick="conversationManager.startNewConversationWithMessage('${this.escapeHtml(originalMessage || '')}')">
                        Start New Conversation
                    </button>
                    <button class="btn btn-secondary" onclick="this.closest('.conversation-limit-modal').remove()">
                        Cancel
                    </button>
                </div>
            </div>
        `;
        
        return modal;
    }

    async startNewConversationWithMessage(originalMessage = '') {
        // Close the modal
        const modal = document.querySelector('.conversation-limit-modal');
        if (modal) modal.remove();
        
        // Create new conversation
        await this.createNewConversation();
        
        // Send the original message if provided
        if (originalMessage && originalMessage !== 'null' && originalMessage.trim()) {
            await this.sendMessage(originalMessage);
        }
    }

    showLimitWarning(remainingMessages) {
        const warningElement = document.getElementById('limit-warning');
        if (warningElement) {
            warningElement.textContent = `${remainingMessages} messages remaining in this conversation`;
            warningElement.style.display = 'block';
            
            // Auto-hide after 5 seconds
            setTimeout(() => {
                warningElement.style.display = 'none';
            }, 5000);
        }
    }

    updateUI() {
        // Update message counter in UI
        const counterElement = document.getElementById('message-counter');
        if (counterElement) {
            counterElement.textContent = `${this.remainingMessages} messages left`;
            
            // Add warning class if low
            if (this.remainingMessages <= 10) {
                counterElement.classList.add('warning');
            } else {
                counterElement.classList.remove('warning');
            }
        }
        
        // Update progress bar if exists
        const progressBar = document.getElementById('conversation-progress');
        if (progressBar) {
            const percentage = (this.remainingMessages / 100) * 100;
            progressBar.style.width = `${percentage}%`;
            
            if (percentage <= 10) {
                progressBar.classList.add('critical');
            } else if (percentage <= 25) {
                progressBar.classList.add('warning');
            } else {
                progressBar.classList.remove('warning', 'critical');
            }
        }
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Show with animation
        setTimeout(() => notification.classList.add('show'), 10);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    displayMessage(message, isUser = false, isExpert = false) {
        const chatContainer = document.getElementById('chat-messages');
        if (!chatContainer) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'assistant-message'}`;
        
        if (isExpert) {
            messageDiv.classList.add('expert-mode');
        }
        
        messageDiv.innerHTML = `
            <div class="message-content">
                ${isExpert ? '<div class="expert-mode-indicator">Expert Analysis</div>' : ''}
                <div class="message-text">${this.escapeHtml(message)}</div>
                <div class="message-time">${new Date().toLocaleTimeString()}</div>
            </div>
        `;
        
        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    setupEventListeners() {
        // Listen for form submissions
        const chatForm = document.getElementById('chat-form');
        if (chatForm) {
            chatForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const messageInput = document.getElementById('message-input');
                const expertModeCheckbox = document.getElementById('expert-mode');
                const message = messageInput.value.trim();
                
                if (message) {
                    const isExpertMode = expertModeCheckbox ? expertModeCheckbox.checked : false;
                    
                    // Display user message
                    this.displayMessage(message, true);
                    
                    messageInput.value = '';
                    
                    try {
                        const response = await this.sendMessage(message, isExpertMode);
                        
                        // Display assistant response
                        this.displayMessage(response.message, false, response.expert_mode);
                        
                        // Show expert analysis if available
                        if (response.comprehensive_analysis) {
                            this.displayExpertAnalysis(response.comprehensive_analysis);
                        }
                        
                    } catch (error) {
                        this.displayMessage('Sorry, there was an error processing your message.', false);
                    }
                }
            });
        }
        
        // Listen for new conversation button
        const newConvButton = document.getElementById('new-conversation-btn');
        if (newConvButton) {
            newConvButton.addEventListener('click', () => {
                this.createNewConversation();
            });
        }
    }

    displayExpertAnalysis(analysis) {
        const chatContainer = document.getElementById('chat-messages');
        if (!chatContainer || !analysis) return;

        const analysisDiv = document.createElement('div');
        analysisDiv.className = 'expert-analysis-container';
        
        let expertsHtml = '';
        if (analysis.expert_analyses && analysis.expert_analyses.length > 0) {
            expertsHtml = analysis.expert_analyses.map(expert => `
                <div class="expert-analysis">
                    <h4>${expert.specialist}</h4>
                    <p>${this.escapeHtml(expert.analysis)}</p>
                    <div class="confidence">Confidence: ${(expert.confidence * 100).toFixed(0)}%</div>
                </div>
            `).join('');
        }
        
        analysisDiv.innerHTML = `
            <div class="expert-summary">
                <h3>Expert Analysis Summary</h3>
                <p>${this.escapeHtml(analysis.summary)}</p>
                <div class="overall-confidence">
                    Overall Confidence: ${(analysis.confidence_score * 100).toFixed(0)}%
                </div>
            </div>
            ${expertsHtml}
        `;
        
        chatContainer.appendChild(analysisDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    getToken() {
        // Get authentication token from localStorage or wherever it's stored
        return localStorage.getItem('auth_token') || '';
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Global instance
const conversationManager = new ConversationManager();

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const userId = document.querySelector('[data-user-id]')?.dataset.userId || 'default-user';
    conversationManager.initialize(userId);
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ConversationManager;
}
