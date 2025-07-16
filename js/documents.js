// Document Management
class DocumentManager {
    constructor() {
        this.uploadedDocuments = [];
        this.maxFileSize = 10 * 1024 * 1024; // 10MB
        this.allowedTypes = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'image/jpeg',
            'image/png',
            'image/gif',
            'text/plain'
        ];
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadDocuments();
    }

    bindEvents() {
        const uploadArea = document.getElementById('upload-area');
        const fileInput = document.getElementById('file-input');
        const uploadButton = document.getElementById('upload-document');

        if (uploadArea) {
            uploadArea.addEventListener('click', () => {
                fileInput?.click();
            });

            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('drag-over');
            });

            uploadArea.addEventListener('dragleave', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('drag-over');
            });

            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('drag-over');
                this.handleFiles(e.dataTransfer.files);
            });
        }

        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                this.handleFiles(e.target.files);
            });
        }

        if (uploadButton) {
            uploadButton.addEventListener('click', () => {
                fileInput?.click();
            });
        }
    }

    async handleFiles(files) {
        const fileArray = Array.from(files);
        
        for (const file of fileArray) {
            if (this.validateFile(file)) {
                await this.uploadFile(file);
            }
        }
    }

    validateFile(file) {
        // Check file size
        if (file.size > this.maxFileSize) {
            this.showError(`File "${file.name}" is too large. Maximum size is 10MB.`);
            return false;
        }

        // Check file type
        if (!this.allowedTypes.includes(file.type)) {
            this.showError(`File type "${file.type}" is not supported.`);
            return false;
        }

        return true;
    }

    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('type', this.getDocumentType(file));
        formData.append('description', ''); // Could add description input

        // Show upload progress
        const progressElement = this.showUploadProgress(file.name);

        try {
            const response = await window.apiService.uploadDocument(formData);
            
            // Add to local list
            this.uploadedDocuments.push(response.document);
            
            // Update UI
            this.addDocumentToList(response.document);
            this.hideUploadProgress(progressElement);
            this.showSuccess(`"${file.name}" uploaded successfully!`);

            // Trigger AI analysis if enabled
            if (response.document.id) {
                this.analyzeDocument(response.document.id);
            }

        } catch (error) {
            console.error('Upload failed:', error);
            this.hideUploadProgress(progressElement);
            this.showError(`Failed to upload "${file.name}": ${error.message}`);
        }
    }

    getDocumentType(file) {
        if (file.type.startsWith('image/')) {
            return 'image';
        } else if (file.type === 'application/pdf') {
            return 'pdf';
        } else if (file.type.includes('word')) {
            return 'document';
        } else {
            return 'other';
        }
    }

    showUploadProgress(fileName) {
        const progressElement = document.createElement('div');
        progressElement.className = 'upload-progress';
        progressElement.innerHTML = `
            <div class="progress-info">
                <span class="file-name">${fileName}</span>
                <span class="progress-status">Uploading...</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill"></div>
            </div>
        `;

        const documentsContainer = document.querySelector('.documents-container');
        if (documentsContainer) {
            documentsContainer.appendChild(progressElement);
        }

        // Simulate progress (in real implementation, track actual upload progress)
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 20;
            if (progress >= 100) {
                progress = 100;
                clearInterval(interval);
            }
            
            const progressFill = progressElement.querySelector('.progress-fill');
            if (progressFill) {
                progressFill.style.width = `${progress}%`;
            }
        }, 200);

        return progressElement;
    }

    hideUploadProgress(progressElement) {
        if (progressElement) {
            setTimeout(() => {
                progressElement.remove();
            }, 1000);
        }
    }

    async loadDocuments() {
        try {
            const documents = await window.apiService.getDocuments();
            this.uploadedDocuments = documents;
            this.displayDocuments();
        } catch (error) {
            console.error('Failed to load documents:', error);
            this.showMockDocuments();
        }
    }

    displayDocuments() {
        const documentsList = document.getElementById('documents-list');
        if (!documentsList) return;

        documentsList.innerHTML = '';

        if (this.uploadedDocuments.length === 0) {
            documentsList.innerHTML = `
                <div class="no-documents">
                    <i class="fas fa-folder-open"></i>
                    <p>No documents uploaded yet</p>
                    <p>Upload your medical documents to get started</p>
                </div>
            `;
            return;
        }

        this.uploadedDocuments.forEach(doc => {
            this.addDocumentToList(doc);
        });
    }

    addDocumentToList(document) {
        const documentsList = document.getElementById('documents-list');
        if (!documentsList) return;

        // Remove no-documents message if it exists
        const noDocsMessage = documentsList.querySelector('.no-documents');
        if (noDocsMessage) {
            noDocsMessage.remove();
        }

        const docElement = document.createElement('div');
        docElement.className = 'document-item';
        docElement.setAttribute('data-doc-id', document.id);

        const fileIcon = this.getFileIcon(document.type || document.file_type);
        const uploadDate = new Date(document.created_at || document.upload_date).toLocaleDateString();
        const fileSize = this.formatFileSize(document.size || document.file_size);

        docElement.innerHTML = `
            <div class="document-info">
                <div class="document-icon">
                    <i class="${fileIcon}"></i>
                </div>
                <div class="document-details">
                    <h4 class="document-name">${document.name || document.filename}</h4>
                    <p class="document-meta">
                        <span class="upload-date">Uploaded: ${uploadDate}</span>
                        <span class="file-size">${fileSize}</span>
                    </p>
                    ${document.description ? `<p class="document-description">${document.description}</p>` : ''}
                    ${document.analysis_status ? `<div class="analysis-status ${document.analysis_status}">${this.getAnalysisStatusText(document.analysis_status)}</div>` : ''}
                </div>
            </div>
            <div class="document-actions">
                <button class="btn btn-sm btn-primary" onclick="window.documentManager.viewDocument('${document.id}')">
                    <i class="fas fa-eye"></i> View
                </button>
                <button class="btn btn-sm btn-secondary" onclick="window.documentManager.downloadDocument('${document.id}')">
                    <i class="fas fa-download"></i> Download
                </button>
                <button class="btn btn-sm btn-warning" onclick="window.documentManager.analyzeDocument('${document.id}')">
                    <i class="fas fa-brain"></i> Analyze
                </button>
                <button class="btn btn-sm btn-danger" onclick="window.documentManager.deleteDocument('${document.id}')">
                    <i class="fas fa-trash"></i> Delete
                </button>
            </div>
        `;

        documentsList.appendChild(docElement);
    }

    getFileIcon(fileType) {
        switch (fileType) {
            case 'pdf':
                return 'fas fa-file-pdf text-danger';
            case 'image':
                return 'fas fa-file-image text-info';
            case 'document':
                return 'fas fa-file-word text-primary';
            default:
                return 'fas fa-file text-secondary';
        }
    }

    formatFileSize(bytes) {
        if (!bytes) return 'Unknown size';
        
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    }

    getAnalysisStatusText(status) {
        switch (status) {
            case 'pending':
                return 'Analysis Pending';
            case 'processing':
                return 'Analyzing...';
            case 'completed':
                return 'Analysis Complete';
            case 'failed':
                return 'Analysis Failed';
            default:
                return 'Not Analyzed';
        }
    }

    async viewDocument(documentId) {
        try {
            const document = this.uploadedDocuments.find(doc => doc.id === documentId);
            if (!document) {
                this.showError('Document not found');
                return;
            }

            // Open document in new tab or modal
            if (document.url || document.download_url) {
                window.open(document.url || document.download_url, '_blank');
            } else {
                this.showError('Document URL not available');
            }
        } catch (error) {
            console.error('Failed to view document:', error);
            this.showError('Failed to view document');
        }
    }

    async downloadDocument(documentId) {
        try {
            const document = this.uploadedDocuments.find(doc => doc.id === documentId);
            if (!document) {
                this.showError('Document not found');
                return;
            }

            // Create download link
            const link = document.createElement('a');
            link.href = document.url || document.download_url;
            link.download = document.name || document.filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

        } catch (error) {
            console.error('Failed to download document:', error);
            this.showError('Failed to download document');
        }
    }

    async analyzeDocument(documentId) {
        try {
            // Update UI to show analysis is starting
            this.updateAnalysisStatus(documentId, 'processing');

            const analysis = await window.apiService.analyzeDocument(documentId);
            
            // Update analysis status
            this.updateAnalysisStatus(documentId, 'completed');
            
            // Show analysis results
            this.showAnalysisResults(analysis);

        } catch (error) {
            console.error('Document analysis failed:', error);
            this.updateAnalysisStatus(documentId, 'failed');
            this.showError('Document analysis failed: ' + error.message);
        }
    }

    updateAnalysisStatus(documentId, status) {
        const docElement = document.querySelector(`[data-doc-id="${documentId}"]`);
        if (!docElement) return;

        let statusElement = docElement.querySelector('.analysis-status');
        if (!statusElement) {
            statusElement = document.createElement('div');
            statusElement.className = 'analysis-status';
            docElement.querySelector('.document-details').appendChild(statusElement);
        }

        statusElement.className = `analysis-status ${status}`;
        statusElement.textContent = this.getAnalysisStatusText(status);

        // Update local document data
        const docIndex = this.uploadedDocuments.findIndex(doc => doc.id === documentId);
        if (docIndex !== -1) {
            this.uploadedDocuments[docIndex].analysis_status = status;
        }
    }

    showAnalysisResults(analysis) {
        const modal = document.createElement('div');
        modal.className = 'modal analysis-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3><i class="fas fa-brain"></i> Document Analysis Results</h3>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="analysis-results">
                        ${this.renderAnalysisResults(analysis)}
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-primary" onclick="this.closest('.modal').remove()">Close</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Close modal events
        modal.addEventListener('click', (e) => {
            if (e.target === modal || e.target.classList.contains('modal-close')) {
                modal.remove();
            }
        });
    }

    renderAnalysisResults(analysis) {
        let html = '';

        if (analysis.summary) {
            html += `
                <div class="analysis-section">
                    <h4>Summary</h4>
                    <p>${analysis.summary}</p>
                </div>
            `;
        }

        if (analysis.key_findings && analysis.key_findings.length > 0) {
            html += `
                <div class="analysis-section">
                    <h4>Key Findings</h4>
                    <ul>
                        ${analysis.key_findings.map(finding => `<li>${finding}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        if (analysis.recommendations && analysis.recommendations.length > 0) {
            html += `
                <div class="analysis-section">
                    <h4>Recommendations</h4>
                    <ul>
                        ${analysis.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        if (analysis.medical_entities && analysis.medical_entities.length > 0) {
            html += `
                <div class="analysis-section">
                    <h4>Medical Entities Detected</h4>
                    <div class="medical-entities">
                        ${analysis.medical_entities.map(entity => 
                            `<span class="entity-tag ${entity.type}">${entity.text}</span>`
                        ).join('')}
                    </div>
                </div>
            `;
        }

        if (analysis.confidence_score) {
            html += `
                <div class="analysis-section">
                    <h4>Analysis Confidence</h4>
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: ${analysis.confidence_score * 100}%"></div>
                    </div>
                    <p>${Math.round(analysis.confidence_score * 100)}% confidence</p>
                </div>
            `;
        }

        return html || '<p>No analysis results available.</p>';
    }

    async deleteDocument(documentId) {
        if (!confirm('Are you sure you want to delete this document? This action cannot be undone.')) {
            return;
        }

        try {
            await window.apiService.deleteDocument(documentId);
            
            // Remove from local list
            this.uploadedDocuments = this.uploadedDocuments.filter(doc => doc.id !== documentId);
            
            // Remove from UI
            const docElement = document.querySelector(`[data-doc-id="${documentId}"]`);
            if (docElement) {
                docElement.remove();
            }

            // Show empty state if no documents left
            if (this.uploadedDocuments.length === 0) {
                this.displayDocuments();
            }

            this.showSuccess('Document deleted successfully');

        } catch (error) {
            console.error('Failed to delete document:', error);
            this.showError('Failed to delete document: ' + error.message);
        }
    }

    showMockDocuments() {
        // Show sample documents when API is not available
        const mockDocs = [
            {
                id: '1',
                name: 'Blood Test Results.pdf',
                type: 'pdf',
                size: 245760,
                created_at: '2024-07-01T10:00:00Z',
                analysis_status: 'completed'
            },
            {
                id: '2',
                name: 'MRI Scan Report.pdf',
                type: 'pdf',
                size: 1024000,
                created_at: '2024-06-15T14:30:00Z',
                analysis_status: 'pending'
            }
        ];

        this.uploadedDocuments = mockDocs;
        this.displayDocuments();
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <i class="${type === 'error' ? 'fas fa-exclamation-circle' : 'fas fa-check-circle'}"></i>
            <span>${message}</span>
            <button class="notification-close">&times;</button>
        `;

        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'error' ? '#ff4444' : '#44ff44'};
            color: white;
            padding: 12px 16px;
            border-radius: 8px;
            z-index: 1000;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            display: flex;
            align-items: center;
            gap: 8px;
            max-width: 300px;
        `;

        document.body.appendChild(notification);

        // Auto-remove after 5 seconds
        const timeout = setTimeout(() => {
            notification.remove();
        }, 5000);

        // Manual close
        notification.querySelector('.notification-close').addEventListener('click', () => {
            clearTimeout(timeout);
            notification.remove();
        });
    }
}

// Initialize document manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('documents-list')) {
        window.documentManager = new DocumentManager();
    }
});
