// Chat Management
class ChatManager {
    constructor() {
        this.chatHistory = [];
        this.isTyping = false;
        this.init();
    }

    init() {
        this.bindEvents();
        this.initializeChat();
    }

    bindEvents() {
        const chatInput = document.getElementById('chat-input');
        const sendButton = document.getElementById('send-message');

        if (chatInput) {
            chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });

            chatInput.addEventListener('input', () => {
                this.handleTyping();
            });
        }

        if (sendButton) {
            sendButton.addEventListener('click', () => {
                this.sendMessage();
            });
        }
    }

    initializeChat() {
        this.addWelcomeMessage();
    }

    addWelcomeMessage() {
        const welcomeMessage = {
            id: Date.now(),
            type: 'agent',
            content: `Hello! I'm your AI Medical Assistant. I can help you with:

• Analyzing your health data and symptoms
• Providing medical information and insights
• Answering questions about your conditions
• Explaining test results and reports
• Offering general health advice

How can I assist you today?`,
            timestamp: new Date()
        };

        this.addMessageToChat(welcomeMessage);
    }

    async sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();

        if (!message) return;

        // Clear input
        input.value = '';

        // Add user message to chat
        const userMessage = {
            id: Date.now(),
            type: 'user',
            content: message,
            timestamp: new Date()
        };

        this.addMessageToChat(userMessage);
        this.chatHistory.push(userMessage);

        // Show typing indicator
        this.showTypingIndicator();

        try {
            // Get AI response using OpenAI format
            const response = await window.apiService.chatWithAgent(message, {
                chat_history: this.chatHistory.slice(-10), // Last 10 messages for context
                user_profile: window.authManager?.getCurrentUser()
            });

            // Hide typing indicator
            this.hideTypingIndicator();

            // Handle OpenAI response format
            let aiContent = '';
            if (response.choices && response.choices.length > 0) {
                aiContent = response.choices[0].message?.content || 'I apologize, but I couldn\'t generate a response.';
            } else if (response.message) {
                aiContent = response.message;
            } else if (response.response) {
                aiContent = response.response;
            } else {
                aiContent = 'I apologize, but I encountered an issue processing your request.';
            }

            // Add agent response to chat
            const agentMessage = {
                id: Date.now() + 1,
                type: 'agent',
                content: aiContent,
                timestamp: new Date(),
                metadata: {
                    model: response.model,
                    usage: response.usage,
                    response_time: response.response_time
                }
            };

            this.addMessageToChat(agentMessage);
            this.chatHistory.push(agentMessage);

            // Handle special response types (if any)
            if (response.attachments) {
                this.handleAttachments(response.attachments);
            }

            if (response.suggestions) {
                this.showSuggestions(response.suggestions);
            }

        } catch (error) {
            this.hideTypingIndicator();
            
            const errorMessage = {
                id: Date.now() + 1,
                type: 'agent',
                content: 'I apologize, but I\'m currently unable to process your request. Please try again later or contact support if the issue persists.',
                timestamp: new Date(),
                isError: true
            };

            this.addMessageToChat(errorMessage);
            console.error('Chat error:', error);
        }
    }

    addMessageToChat(message) {
        const messagesContainer = document.getElementById('chat-messages');
        if (!messagesContainer) return;

        const messageElement = document.createElement('div');
        messageElement.className = `chat-message ${message.type}-message`;
        messageElement.setAttribute('data-message-id', message.id);

        const timestamp = message.timestamp.toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
        });

        const avatarIcon = message.type === 'user' ? 'fas fa-user' : 'fas fa-robot';
        const senderName = message.type === 'user' ? 'You' : 'Medical AI';

        messageElement.innerHTML = `
            <div class="message-avatar">
                <i class="${avatarIcon}"></i>
            </div>
            <div class="message-content">
                <div class="message-header">
                    <span class="sender-name">${senderName}</span>
                    <span class="message-time">${timestamp}</span>
                </div>
                <div class="message-text">${this.formatMessageContent(message.content)}</div>
                ${message.metadata ? this.renderMetadata(message.metadata) : ''}
            </div>
        `;

        if (message.isError) {
            messageElement.classList.add('error-message');
        }

        messagesContainer.appendChild(messageElement);
        this.scrollToBottom();
    }

    formatMessageContent(content) {
        // Convert markdown-like formatting to HTML
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>')
            .replace(/•/g, '•'); // Ensure bullet points are preserved
    }

    renderMetadata(metadata) {
        if (!metadata) return '';

        let metadataHtml = '<div class="message-metadata">';

        if (metadata.confidence) {
            metadataHtml += `<div class="confidence-score">Confidence: ${Math.round(metadata.confidence * 100)}%</div>`;
        }

        if (metadata.sources && metadata.sources.length > 0) {
            metadataHtml += '<div class="sources"><strong>Sources:</strong><ul>';
            metadata.sources.forEach(source => {
                metadataHtml += `<li><a href="${source.url}" target="_blank">${source.title}</a></li>`;
            });
            metadataHtml += '</ul></div>';
        }

        if (metadata.related_conditions) {
            metadataHtml += '<div class="related-conditions"><strong>Related Conditions:</strong> ';
            metadataHtml += metadata.related_conditions.join(', ');
            metadataHtml += '</div>';
        }

        metadataHtml += '</div>';
        return metadataHtml;
    }

    showTypingIndicator() {
        const messagesContainer = document.getElementById('chat-messages');
        if (!messagesContainer) return;

        // Remove existing typing indicator
        this.hideTypingIndicator();

        const typingElement = document.createElement('div');
        typingElement.className = 'chat-message agent-message typing-indicator';
        typingElement.id = 'typing-indicator';
        typingElement.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <div class="typing-animation">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;

        messagesContainer.appendChild(typingElement);
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    handleAttachments(attachments) {
        attachments.forEach(attachment => {
            const attachmentMessage = {
                id: Date.now() + Math.random(),
                type: 'agent',
                content: this.renderAttachment(attachment),
                timestamp: new Date(),
                isAttachment: true
            };

            this.addMessageToChat(attachmentMessage);
        });
    }

    renderAttachment(attachment) {
        switch (attachment.type) {
            case 'chart':
                return this.renderChart(attachment.data);
            case 'image':
                return `<img src="${attachment.url}" alt="${attachment.description}" class="chat-image">`;
            case 'document':
                return `<div class="chat-document">
                    <i class="fas fa-file-alt"></i>
                    <a href="${attachment.url}" target="_blank">${attachment.name}</a>
                </div>`;
            default:
                return `<div class="chat-attachment">${attachment.content}</div>`;
        }
    }

    renderChart(chartData) {
        const chartId = `chart-${Date.now()}`;
        return `<div class="chat-chart">
            <canvas id="${chartId}" width="400" height="200"></canvas>
            <script>
                // Chart rendering would go here
                console.log('Rendering chart:', ${JSON.stringify(chartData)});
            </script>
        </div>`;
    }

    showSuggestions(suggestions) {
        const messagesContainer = document.getElementById('chat-messages');
        if (!messagesContainer) return;

        const suggestionsElement = document.createElement('div');
        suggestionsElement.className = 'chat-suggestions';
        suggestionsElement.innerHTML = `
            <div class="suggestions-header">Suggested questions:</div>
            <div class="suggestions-list">
                ${suggestions.map(suggestion => 
                    `<button class="suggestion-btn" onclick="window.chatManager.selectSuggestion('${suggestion}')">${suggestion}</button>`
                ).join('')}
            </div>
        `;

        messagesContainer.appendChild(suggestionsElement);
        this.scrollToBottom();
    }

    selectSuggestion(suggestion) {
        const input = document.getElementById('chat-input');
        if (input) {
            input.value = suggestion;
            this.sendMessage();
        }

        // Remove suggestions after selection
        const suggestions = document.querySelector('.chat-suggestions');
        if (suggestions) {
            suggestions.remove();
        }
    }

    handleTyping() {
        // Could implement typing indicators for real-time chat
        if (!this.isTyping) {
            this.isTyping = true;
            setTimeout(() => {
                this.isTyping = false;
            }, 1000);
        }
    }

    scrollToBottom() {
        const messagesContainer = document.getElementById('chat-messages');
        if (messagesContainer) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    }

    clearChat() {
        const messagesContainer = document.getElementById('chat-messages');
        if (messagesContainer) {
            messagesContainer.innerHTML = '';
        }
        this.chatHistory = [];
        this.initializeChat();
    }

    exportChat() {
        const chatData = {
            messages: this.chatHistory,
            exported_at: new Date().toISOString(),
            user: window.authManager?.getCurrentUser()?.name || 'Unknown'
        };

        const blob = new Blob([JSON.stringify(chatData, null, 2)], { 
            type: 'application/json' 
        });
        
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `meditwin-chat-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    // Quick action methods for common medical queries
    async askAboutSymptoms(symptoms) {
        const query = `I'm experiencing the following symptoms: ${symptoms.join(', ')}. What could this indicate and what should I do?`;
        
        const input = document.getElementById('chat-input');
        if (input) {
            input.value = query;
            this.sendMessage();
        }
    }

    async askAboutMedication(medication) {
        const query = `Can you tell me about ${medication}? Including its uses, side effects, and interactions.`;
        
        const input = document.getElementById('chat-input');
        if (input) {
            input.value = query;
            this.sendMessage();
        }
    }

    async requestHealthSummary() {
        const query = "Can you provide a summary of my current health status based on my medical data?";
        
        const input = document.getElementById('chat-input');
        if (input) {
            input.value = query;
            this.sendMessage();
        }
    }

    // Expert Opinion Features
    async requestExpertOpinion() {
        const chatHistory = this.chatHistory.slice(-5); // Last 5 messages for context
        const symptoms = this.extractSymptomsFromHistory(chatHistory);
        
        const expertData = {
            caseDescription: this.generateCaseDescription(chatHistory),
            symptoms: symptoms,
            specialty: this.suggestSpecialty(symptoms),
            urgency: this.assessUrgency(symptoms),
            medicalHistory: 'Available in chat history'
        };

        try {
            const response = await window.apiService.requestExpertOpinion(expertData);
            
            const expertMessage = {
                id: Date.now(),
                type: 'agent',
                content: `🩺 **Expert Opinion Requested**\n\nI've forwarded your case to a ${expertData.specialty} specialist. You should receive a professional medical opinion within 24-48 hours.\n\n**Case Summary:**\n${expertData.caseDescription}\n\n**Request ID:** ${response.request_id || 'Pending'}`,
                timestamp: new Date(),
                metadata: {
                    type: 'expert_opinion_request',
                    request_id: response.request_id,
                    specialty: expertData.specialty
                }
            };

            this.addMessageToChat(expertMessage);
            this.chatHistory.push(expertMessage);
            
        } catch (error) {
            console.error('Expert opinion request failed:', error);
            const errorMessage = {
                id: Date.now(),
                type: 'agent',
                content: 'I apologize, but I was unable to submit your expert opinion request at this time. Please try again later.',
                timestamp: new Date(),
                isError: true
            };
            this.addMessageToChat(errorMessage);
        }
    }

    extractSymptomsFromHistory(history) {
        const symptoms = [];
        const symptomKeywords = ['pain', 'ache', 'hurt', 'fever', 'nausea', 'dizzy', 'tired', 'cough', 'headache', 'chest', 'stomach', 'back'];
        
        history.forEach(message => {
            if (message.type === 'user') {
                symptomKeywords.forEach(keyword => {
                    if (message.content.toLowerCase().includes(keyword)) {
                        symptoms.push(keyword);
                    }
                });
            }
        });
        
        return [...new Set(symptoms)]; // Remove duplicates
    }

    generateCaseDescription(history) {
        const userMessages = history.filter(msg => msg.type === 'user').map(msg => msg.content);
        return userMessages.join(' ').substring(0, 500) + (userMessages.join(' ').length > 500 ? '...' : '');
    }

    suggestSpecialty(symptoms) {
        const specialtyMap = {
            'chest': 'cardiology',
            'heart': 'cardiology',
            'lung': 'pulmonology',
            'cough': 'pulmonology',
            'stomach': 'gastroenterology',
            'headache': 'neurology',
            'back': 'orthopedics',
            'skin': 'dermatology'
        };

        for (const symptom of symptoms) {
            if (specialtyMap[symptom]) {
                return specialtyMap[symptom];
            }
        }
        
        return 'internal_medicine';
    }

    assessUrgency(symptoms) {
        const urgentSymptoms = ['chest pain', 'severe', 'intense', 'emergency'];
        const hasUrgentSymptoms = symptoms.some(symptom => 
            urgentSymptoms.some(urgent => symptom.includes(urgent))
        );
        
        return hasUrgentSymptoms ? 'urgent' : 'routine';
    }

    // Timeline Integration
    async addToTimeline() {
        const lastUserMessage = this.chatHistory.filter(msg => msg.type === 'user').pop();
        if (!lastUserMessage) return;

        const timelineData = {
            type: 'chat_consultation',
            title: 'AI Medical Consultation',
            description: lastUserMessage.content.substring(0, 200),
            date: new Date().toISOString(),
            severity: 'moderate',
            tags: ['ai_chat', 'consultation']
        };

        try {
            await window.apiService.createTimelineEvent(timelineData);
            
            const confirmMessage = {
                id: Date.now(),
                type: 'agent',
                content: '📅 This consultation has been added to your medical timeline for future reference.',
                timestamp: new Date()
            };
            
            this.addMessageToChat(confirmMessage);
        } catch (error) {
            console.error('Failed to add to timeline:', error);
        }
    }

    // Enhanced Quick Actions
    async quickSymptomAnalysis() {
        const symptoms = this.extractSymptomsFromHistory(this.chatHistory);
        if (symptoms.length === 0) {
            const message = "I need more information about your symptoms. Could you describe what you're experiencing?";
            this.simulateAgentMessage(message);
            return;
        }

        try {
            const analysis = await window.apiService.analyzeSymptoms({
                symptoms: symptoms,
                duration: 'recent',
                severity: 'moderate'
            });

            const analysisMessage = {
                id: Date.now(),
                type: 'agent',
                content: `🔬 **Symptom Analysis**\n\n${analysis.summary || 'Analysis completed'}\n\n**Recommendations:**\n${analysis.recommendations || 'Please consult with a healthcare provider for proper evaluation.'}`,
                timestamp: new Date(),
                metadata: analysis
            };

            this.addMessageToChat(analysisMessage);
            this.chatHistory.push(analysisMessage);
            
        } catch (error) {
            console.error('Symptom analysis failed:', error);
        }
    }

    simulateAgentMessage(content) {
        const message = {
            id: Date.now(),
            type: 'agent',
            content: content,
            timestamp: new Date()
        };
        
        this.addMessageToChat(message);
        this.chatHistory.push(message);
    }
}

// Initialize chat manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('chat-messages')) {
        window.chatManager = new ChatManager();
    }
});
