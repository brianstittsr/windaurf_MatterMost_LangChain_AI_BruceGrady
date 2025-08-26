// LangChain Automation Platform - Workflow Builder JavaScript

class WorkflowBuilder {
    constructor() {
        this.socket = io();
        this.currentWorkflow = null;
        this.network = null;
        this.nodes = new vis.DataSet([]);
        this.edges = new vis.DataSet([]);
        this.selectedNode = null;
        
        this.init();
    }
    
    init() {
        this.initNetwork();
        this.initEventListeners();
        this.loadWorkflows();
        this.setupSocketEvents();
    }
    
    initNetwork() {
        const container = document.getElementById('workflow-network');
        const data = {
            nodes: this.nodes,
            edges: this.edges
        };
        
        const options = {
            nodes: {
                shape: 'box',
                margin: 10,
                font: { size: 14, color: '#333' },
                borderWidth: 2,
                shadow: true,
                chosen: true
            },
            edges: {
                arrows: { to: { enabled: true, scaleFactor: 1 } },
                color: { color: '#667eea', highlight: '#5a6fd8' },
                width: 2,
                smooth: { type: 'cubicBezier', forceDirection: 'horizontal' }
            },
            physics: {
                enabled: false
            },
            interaction: {
                dragNodes: true,
                dragView: true,
                zoomView: true
            }
        };
        
        this.network = new vis.Network(container, data, options);
        
        // Network event listeners
        this.network.on('doubleClick', (params) => {
            if (params.nodes.length > 0) {
                this.openNodeConfig(params.nodes[0]);
            }
        });
        
        this.network.on('oncontext', (params) => {
            params.event.preventDefault();
            if (params.nodes.length > 0) {
                this.showNodeContextMenu(params.nodes[0], params.pointer.DOM);
            }
        });
        
        // Enable drag and drop from palette
        this.setupDragAndDrop();
    }
    
    setupDragAndDrop() {
        const canvas = document.getElementById('workflow-network');
        const nodeItems = document.querySelectorAll('.node-item');
        
        nodeItems.forEach(item => {
            item.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('text/plain', JSON.stringify({
                    type: item.dataset.nodeType,
                    subtype: item.dataset.nodeSubtype,
                    name: item.textContent.trim()
                }));
            });
        });
        
        canvas.addEventListener('dragover', (e) => {
            e.preventDefault();
        });
        
        canvas.addEventListener('drop', (e) => {
            e.preventDefault();
            const data = JSON.parse(e.dataTransfer.getData('text/plain'));
            const canvasPosition = this.network.DOMtoCanvas({
                x: e.offsetX,
                y: e.offsetY
            });
            
            this.addNode(data, canvasPosition);
        });
    }
    
    addNode(nodeData, position) {
        const nodeId = this.generateId();
        const nodeColor = this.getNodeColor(nodeData.type);
        
        const node = {
            id: nodeId,
            label: nodeData.name,
            x: position.x,
            y: position.y,
            color: {
                background: nodeColor.background,
                border: nodeColor.border
            },
            font: { color: nodeColor.text },
            nodeType: nodeData.type,
            nodeSubtype: nodeData.subtype,
            config: this.getDefaultNodeConfig(nodeData.type, nodeData.subtype)
        };
        
        this.nodes.add(node);
        this.markWorkflowModified();
    }
    
    getNodeColor(nodeType) {
        const colors = {
            trigger: { background: '#28a745', border: '#1e7e34', text: 'white' },
            ai_agent: { background: '#667eea', border: '#5a6fd8', text: 'white' },
            action: { background: '#17a2b8', border: '#138496', text: 'white' },
            condition: { background: '#ffc107', border: '#e0a800', text: '#333' },
            transform: { background: '#6f42c1', border: '#5a32a3', text: 'white' },
            output: { background: '#fd7e14', border: '#e8650e', text: 'white' }
        };
        
        return colors[nodeType] || { background: '#6c757d', border: '#545b62', text: 'white' };
    }
    
    getDefaultNodeConfig(type, subtype) {
        const configs = {
            trigger: {
                webhook: { url: '', method: 'POST', headers: {} },
                schedule: { cron: '0 9 * * *', timezone: 'UTC' },
                mattermost: { channels: [], keywords: [] }
            },
            ai_agent: {
                chat: { prompt: 'You are a helpful assistant. Process this input: {input}', model: 'gpt-4' },
                analyst: { prompt: 'Analyze this data and provide insights: {input}', model: 'gpt-4' },
                writer: { prompt: 'Write content based on this input: {input}', style: 'professional' }
            },
            action: {
                http: { url: '', method: 'GET', headers: {}, body: '' },
                email: { to: '', subject: '', body: '', smtp_server: '' },
                database: { query: '', connection_string: '' }
            },
            condition: {
                if: { condition: 'data.value > 0', true_path: '', false_path: '' }
            },
            transform: {
                data: { script: 'return data;', language: 'javascript' }
            },
            output: {
                mattermost: { channel_id: '', message_template: 'Result: {data}' },
                webhook: { url: '', method: 'POST', headers: {} }
            }
        };
        
        return configs[type]?.[subtype] || {};
    }
    
    openNodeConfig(nodeId) {
        const node = this.nodes.get(nodeId);
        if (!node) return;
        
        this.selectedNode = node;
        this.generateNodeConfigForm(node);
        document.getElementById('node-config-modal').style.display = 'block';
    }
    
    generateNodeConfigForm(node) {
        const form = document.getElementById('node-config-form');
        form.innerHTML = '';
        
        // Node name
        form.innerHTML += `
            <div class="form-group">
                <label for="node-name">Node Name</label>
                <input type="text" id="node-name" class="form-control" value="${node.label}">
            </div>
        `;
        
        // Type-specific configuration
        if (node.nodeType === 'ai_agent') {
            form.innerHTML += `
                <div class="form-group">
                    <label for="ai-prompt">AI Prompt</label>
                    <textarea id="ai-prompt" class="form-control" rows="4">${node.config.prompt || ''}</textarea>
                    <small class="form-text text-muted">Use {input} to reference input data</small>
                </div>
                <div class="form-group">
                    <label for="ai-model">Model</label>
                    <select id="ai-model" class="form-control">
                        <option value="gpt-4" ${node.config.model === 'gpt-4' ? 'selected' : ''}>GPT-4</option>
                        <option value="gpt-3.5-turbo" ${node.config.model === 'gpt-3.5-turbo' ? 'selected' : ''}>GPT-3.5 Turbo</option>
                    </select>
                </div>
            `;
        } else if (node.nodeType === 'action' && node.nodeSubtype === 'http') {
            form.innerHTML += `
                <div class="form-group">
                    <label for="http-url">URL</label>
                    <input type="url" id="http-url" class="form-control" value="${node.config.url || ''}">
                </div>
                <div class="form-group">
                    <label for="http-method">Method</label>
                    <select id="http-method" class="form-control">
                        <option value="GET" ${node.config.method === 'GET' ? 'selected' : ''}>GET</option>
                        <option value="POST" ${node.config.method === 'POST' ? 'selected' : ''}>POST</option>
                        <option value="PUT" ${node.config.method === 'PUT' ? 'selected' : ''}>PUT</option>
                        <option value="DELETE" ${node.config.method === 'DELETE' ? 'selected' : ''}>DELETE</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="http-headers">Headers (JSON)</label>
                    <textarea id="http-headers" class="form-control" rows="3">${JSON.stringify(node.config.headers || {}, null, 2)}</textarea>
                </div>
            `;
        } else if (node.nodeType === 'condition') {
            form.innerHTML += `
                <div class="form-group">
                    <label for="condition-expr">Condition Expression</label>
                    <input type="text" id="condition-expr" class="form-control" value="${node.config.condition || ''}">
                    <small class="form-text text-muted">Use 'data' to reference input data (e.g., data.value > 100)</small>
                </div>
            `;
        } else if (node.nodeType === 'output' && node.nodeSubtype === 'mattermost') {
            form.innerHTML += `
                <div class="form-group">
                    <label for="output-channel">Channel ID</label>
                    <input type="text" id="output-channel" class="form-control" value="${node.config.channel_id || ''}">
                </div>
                <div class="form-group">
                    <label for="output-message">Message Template</label>
                    <textarea id="output-message" class="form-control" rows="3">${node.config.message_template || ''}</textarea>
                    <small class="form-text text-muted">Use {data} to reference workflow data</small>
                </div>
            `;
        }
    }
    
    saveNodeConfig() {
        if (!this.selectedNode) return;
        
        const nodeName = document.getElementById('node-name').value;
        const updatedNode = { ...this.selectedNode };
        updatedNode.label = nodeName;
        
        // Save type-specific configuration
        if (updatedNode.nodeType === 'ai_agent') {
            updatedNode.config.prompt = document.getElementById('ai-prompt').value;
            updatedNode.config.model = document.getElementById('ai-model').value;
        } else if (updatedNode.nodeType === 'action' && updatedNode.nodeSubtype === 'http') {
            updatedNode.config.url = document.getElementById('http-url').value;
            updatedNode.config.method = document.getElementById('http-method').value;
            try {
                updatedNode.config.headers = JSON.parse(document.getElementById('http-headers').value);
            } catch (e) {
                updatedNode.config.headers = {};
            }
        } else if (updatedNode.nodeType === 'condition') {
            updatedNode.config.condition = document.getElementById('condition-expr').value;
        } else if (updatedNode.nodeType === 'output' && updatedNode.nodeSubtype === 'mattermost') {
            updatedNode.config.channel_id = document.getElementById('output-channel').value;
            updatedNode.config.message_template = document.getElementById('output-message').value;
        }
        
        this.nodes.update(updatedNode);
        this.markWorkflowModified();
        this.closeNodeConfig();
    }
    
    closeNodeConfig() {
        document.getElementById('node-config-modal').style.display = 'none';
        this.selectedNode = null;
    }
    
    async loadWorkflows() {
        try {
            const response = await fetch('/api/workflows');
            const workflows = await response.json();
            this.displayWorkflows(workflows);
        } catch (error) {
            console.error('Failed to load workflows:', error);
            this.showNotification('Failed to load workflows', 'error');
        }
    }
    
    displayWorkflows(workflows) {
        const container = document.getElementById('workflows-container');
        container.innerHTML = '';
        
        workflows.forEach(workflow => {
            const workflowElement = document.createElement('div');
            workflowElement.className = 'workflow-item';
            workflowElement.innerHTML = `
                <h4>${workflow.name}</h4>
                <p>${workflow.description || 'No description'}</p>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span class="workflow-status status-${workflow.status}">${workflow.status}</span>
                    <small>${workflow.node_count} nodes</small>
                </div>
            `;
            
            workflowElement.addEventListener('click', () => {
                this.loadWorkflow(workflow.id);
            });
            
            container.appendChild(workflowElement);
        });
    }
    
    async loadWorkflow(workflowId) {
        try {
            const response = await fetch(`/api/workflows/${workflowId}`);
            const workflow = await response.json();
            
            this.currentWorkflow = workflow;
            this.displayWorkflow(workflow);
            this.updateWorkflowStatus(`Loaded: ${workflow.name}`);
            
            // Join workflow room for real-time updates
            this.socket.emit('join_workflow', { workflow_id: workflowId });
            
        } catch (error) {
            console.error('Failed to load workflow:', error);
            this.showNotification('Failed to load workflow', 'error');
        }
    }
    
    displayWorkflow(workflow) {
        // Clear existing nodes and edges
        this.nodes.clear();
        this.edges.clear();
        
        // Add nodes
        workflow.nodes.forEach(node => {
            const nodeColor = this.getNodeColor(node.type);
            this.nodes.add({
                id: node.id,
                label: node.name,
                x: node.position.x,
                y: node.position.y,
                color: {
                    background: nodeColor.background,
                    border: nodeColor.border
                },
                font: { color: nodeColor.text },
                nodeType: node.type,
                nodeSubtype: node.config.subtype || 'default',
                config: node.config
            });
            
            // Add edges for connections
            node.connections.forEach(targetId => {
                this.edges.add({
                    id: this.generateId(),
                    from: node.id,
                    to: targetId
                });
            });
        });
        
        // Fit network to show all nodes
        this.network.fit();
    }
    
    async saveWorkflow() {
        if (!this.currentWorkflow) {
            this.showNotification('No workflow to save', 'error');
            return;
        }
        
        try {
            // Convert network data to workflow format
            const nodes = this.nodes.get().map(node => ({
                id: node.id,
                type: node.nodeType,
                name: node.label,
                config: node.config,
                position: this.network.getPositions([node.id])[node.id],
                connections: this.edges.get()
                    .filter(edge => edge.from === node.id)
                    .map(edge => edge.to)
            }));
            
            const workflowData = {
                name: this.currentWorkflow.name,
                description: this.currentWorkflow.description,
                nodes: nodes,
                status: this.currentWorkflow.status
            };
            
            const response = await fetch(`/api/workflows/${this.currentWorkflow.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(workflowData)
            });
            
            if (response.ok) {
                this.showNotification('Workflow saved successfully', 'success');
                this.updateWorkflowStatus('Saved');
            } else {
                throw new Error('Failed to save workflow');
            }
            
        } catch (error) {
            console.error('Failed to save workflow:', error);
            this.showNotification('Failed to save workflow', 'error');
        }
    }
    
    async executeWorkflow() {
        if (!this.currentWorkflow) {
            this.showNotification('No workflow to execute', 'error');
            return;
        }
        
        try {
            const response = await fetch(`/api/workflows/${this.currentWorkflow.id}/execute`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    trigger_data: { message: 'Manual execution' },
                    channel_id: null
                })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showNotification('Workflow execution started', 'success');
                this.updateWorkflowStatus('Executing...');
                this.showExecutionLog(result.execution_id);
            } else {
                throw new Error(result.error || 'Failed to execute workflow');
            }
            
        } catch (error) {
            console.error('Failed to execute workflow:', error);
            this.showNotification('Failed to execute workflow', 'error');
        }
    }
    
    showExecutionLog(executionId) {
        document.getElementById('execution-log-modal').style.display = 'block';
        const logContent = document.getElementById('execution-log-content');
        logContent.innerHTML = `
            <div class="log-entry log-info">
                <strong>[${new Date().toLocaleTimeString()}]</strong> Execution started (ID: ${executionId})
            </div>
        `;
    }
    
    closeExecutionLog() {
        document.getElementById('execution-log-modal').style.display = 'none';
    }
    
    async createNewWorkflow() {
        const name = prompt('Enter workflow name:');
        if (!name) return;
        
        try {
            const response = await fetch('/api/workflows', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: name,
                    description: '',
                    created_by: 'user',
                    team_id: 'default'
                })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showNotification('Workflow created successfully', 'success');
                this.loadWorkflows(); // Refresh workflow list
                this.loadWorkflow(result.id); // Load the new workflow
            } else {
                throw new Error('Failed to create workflow');
            }
            
        } catch (error) {
            console.error('Failed to create workflow:', error);
            this.showNotification('Failed to create workflow', 'error');
        }
    }
    
    initEventListeners() {
        // Tab switching
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', () => {
                const tabName = tab.dataset.tab;
                this.switchTab(tabName);
            });
        });
        
        // Modal close events
        window.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                e.target.style.display = 'none';
            }
        });
    }
    
    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        
        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${tabName}-tab`).classList.add('active');
    }
    
    setupSocketEvents() {
        this.socket.on('workflow_update', (data) => {
            if (this.currentWorkflow && data.workflow_id === this.currentWorkflow.id) {
                this.updateWorkflowStatus(data.message);
            }
        });
        
        this.socket.on('execution_log', (data) => {
            this.addExecutionLogEntry(data);
        });
    }
    
    addExecutionLogEntry(logData) {
        const logContent = document.getElementById('execution-log-content');
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry log-${logData.level}`;
        logEntry.innerHTML = `
            <strong>[${new Date(logData.timestamp).toLocaleTimeString()}]</strong> 
            ${logData.message}
        `;
        logContent.appendChild(logEntry);
        logContent.scrollTop = logContent.scrollHeight;
    }
    
    updateWorkflowStatus(status) {
        document.getElementById('workflow-status').textContent = status;
    }
    
    markWorkflowModified() {
        this.updateWorkflowStatus('Modified (unsaved)');
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Show notification
        setTimeout(() => notification.classList.add('show'), 100);
        
        // Hide notification after 3 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => document.body.removeChild(notification), 300);
        }, 3000);
    }
    
    generateId() {
        return Math.random().toString(36).substr(2, 9);
    }
}

// Global functions for HTML onclick events
function createNewWorkflow() {
    workflowBuilder.createNewWorkflow();
}

function saveWorkflow() {
    workflowBuilder.saveWorkflow();
}

function executeWorkflow() {
    workflowBuilder.executeWorkflow();
}

function testWorkflow() {
    workflowBuilder.showNotification('Test functionality coming soon!', 'info');
}

function closeNodeConfig() {
    workflowBuilder.closeNodeConfig();
}

function saveNodeConfig() {
    workflowBuilder.saveNodeConfig();
}

function closeWorkflowConfig() {
    document.getElementById('workflow-config-modal').style.display = 'none';
}

function saveWorkflowConfig() {
    // Implementation for workflow configuration
    closeWorkflowConfig();
}

function closeExecutionLog() {
    workflowBuilder.closeExecutionLog();
}

// Initialize the workflow builder when the page loads
let workflowBuilder;
document.addEventListener('DOMContentLoaded', () => {
    workflowBuilder = new WorkflowBuilder();
});
