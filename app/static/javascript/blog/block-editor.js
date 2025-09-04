class BlogBlockEditor {
    constructor(containerId, hiddenFieldId) {
        this.container = document.getElementById(containerId);
        this.hiddenField = document.getElementById(hiddenFieldId);
        this.blocks = [];
        this.init();
    }

    init() {
        this.setupContainer();
        this.loadExistingBlocks();
        this.render();
    }

    setupContainer() {
        this.container.innerHTML = `
            <div class="block-editor">
                <div class="blocks-container"></div>
                <div class="add-block-menu">
                    <button type="button" class="add-block-btn" onclick="blockEditor.showAddMenu(event)">
                        <i class="fas fa-plus"></i> Add Content Block
                    </button>
                    <div class="add-menu" style="display: none;">
                        <button type="button" onclick="blockEditor.addBlock('text')">
                            <i class="fas fa-paragraph"></i> Text Paragraph
                        </button>
                        <button type="button" onclick="blockEditor.addBlock('heading')">
                            <i class="fas fa-heading"></i> Heading
                        </button>
                        <button type="button" onclick="blockEditor.addBlock('image')">
                            <i class="fas fa-image"></i> Image
                        </button>
                        <button type="button" onclick="blockEditor.addBlock('link')">
                            <i class="fas fa-link"></i> Link
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    loadExistingBlocks() {
        try {
            if (this.hiddenField.value) {
                this.blocks = JSON.parse(this.hiddenField.value);
            }
        } catch (e) {
            console.log('No existing blocks or invalid JSON');
        }

        // If no blocks, add a default text block
        if (this.blocks.length === 0) {
            this.blocks = [{ type: 'text', content: '' }];
        }
        
        console.log('Loaded blocks:', this.blocks);
    }

    render() {
        const container = this.container.querySelector('.blocks-container');
        container.innerHTML = '';

        this.blocks.forEach((block, index) => {
            const blockElement = this.createBlockElement(block, index);
            container.appendChild(blockElement);
        });

        this.updateHiddenField();
    }

    createBlockElement(block, index) {
        const div = document.createElement('div');
        div.className = 'content-block';
        div.dataset.index = index;

        let blockContent = '';
        switch (block.type) {
            case 'text':
                blockContent = `
                    <div class="block-header">
                        <span class="block-type"><i class="fas fa-paragraph"></i> Text Paragraph</span>
                        <div class="block-controls">
                            <button type="button" onclick="blockEditor.moveBlock(${index}, -1)" ${index === 0 ? 'disabled' : ''}>
                                <i class="fas fa-arrow-up"></i>
                            </button>
                            <button type="button" onclick="blockEditor.moveBlock(${index}, 1)" ${index === this.blocks.length - 1 ? 'disabled' : ''}>
                                <i class="fas fa-arrow-down"></i>
                            </button>
                            <button type="button" onclick="blockEditor.removeBlock(${index})" class="delete-btn">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                    <div class="rich-text-toolbar">
                        <button type="button" onclick="blockEditor.formatText(${index}, 'bold')" class="format-btn" title="Bold">
                            <i class="fas fa-bold"></i>
                        </button>
                        <button type="button" onclick="blockEditor.formatText(${index}, 'italic')" class="format-btn" title="Italic">
                            <i class="fas fa-italic"></i>
                        </button>
                        <button type="button" onclick="blockEditor.formatText(${index}, 'underline')" class="format-btn" title="Underline">
                            <i class="fas fa-underline"></i>
                        </button>
                        <button type="button" onclick="blockEditor.insertLink(${index})" class="format-btn" title="Insert Link">
                            <i class="fas fa-link"></i>
                        </button>
                    </div>
                    <div class="rich-text-editor" 
                         contenteditable="true" 
                         data-block-index="${index}"
                         data-placeholder="Enter your text content..."
                         oninput="blockEditor.updateRichText(${index})"
                         onpaste="blockEditor.handlePaste(event, ${index})">${block.content || ''}</div>
                `;
                break;
            
            case 'heading':
                blockContent = `
                    <div class="block-header">
                        <span class="block-type"><i class="fas fa-heading"></i> Heading</span>
                        <div class="block-controls">
                            <select onchange="blockEditor.updateBlock(${index}, 'level', this.value)" class="heading-level">
                                <option value="h1" ${block.level === 'h1' ? 'selected' : ''}>H1</option>
                                <option value="h2" ${block.level === 'h2' ? 'selected' : ''}>H2</option>
                                <option value="h3" ${block.level === 'h3' ? 'selected' : ''}>H3</option>
                                <option value="h4" ${block.level === 'h4' ? 'selected' : ''}>H4</option>
                                <option value="h5" ${block.level === 'h5' ? 'selected' : ''}>H5</option>
                            </select>
                            <button type="button" onclick="blockEditor.moveBlock(${index}, -1)" ${index === 0 ? 'disabled' : ''}>
                                <i class="fas fa-arrow-up"></i>
                            </button>
                            <button type="button" onclick="blockEditor.moveBlock(${index}, 1)" ${index === this.blocks.length - 1 ? 'disabled' : ''}>
                                <i class="fas fa-arrow-down"></i>
                            </button>
                            <button type="button" onclick="blockEditor.removeBlock(${index})" class="delete-btn">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                    <div class="rich-text-toolbar">
                        <button type="button" onclick="blockEditor.formatText(${index}, 'bold')" class="format-btn" title="Bold">
                            <i class="fas fa-bold"></i>
                        </button>
                        <button type="button" onclick="blockEditor.formatText(${index}, 'italic')" class="format-btn" title="Italic">
                            <i class="fas fa-italic"></i>
                        </button>
                        <button type="button" onclick="blockEditor.formatText(${index}, 'underline')" class="format-btn" title="Underline">
                            <i class="fas fa-underline"></i>
                        </button>
                        <button type="button" onclick="blockEditor.insertLink(${index})" class="format-btn" title="Insert Link">
                            <i class="fas fa-link"></i>
                        </button>
                    </div>
                    <div class="rich-text-editor heading-editor" 
                         contenteditable="true" 
                         data-block-index="${index}"
                         data-placeholder="Enter heading text..."
                         oninput="blockEditor.updateRichText(${index})"
                         onpaste="blockEditor.handlePaste(event, ${index})">${block.content || ''}</div>
                `;
                break;
            
            case 'image':
                blockContent = `
                    <div class="block-header">
                        <span class="block-type"><i class="fas fa-image"></i> Image</span>
                        <div class="block-controls">
                            <button type="button" onclick="blockEditor.moveBlock(${index}, -1)" ${index === 0 ? 'disabled' : ''}>
                                <i class="fas fa-arrow-up"></i>
                            </button>
                            <button type="button" onclick="blockEditor.moveBlock(${index}, 1)" ${index === this.blocks.length - 1 ? 'disabled' : ''}>
                                <i class="fas fa-arrow-down"></i>
                            </button>
                            <button type="button" onclick="blockEditor.removeBlock(${index})" class="delete-btn">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                    <input type="url" class="block-input" placeholder="Enter image URL..." 
                           value="${block.url || ''}" onchange="blockEditor.updateBlock(${index}, 'url', this.value)">
                    <input type="text" class="block-input" placeholder="Alt text (optional)..." 
                           value="${block.alt || ''}" onchange="blockEditor.updateBlock(${index}, 'alt', this.value)">
                `;
                break;
            
            case 'link':
                blockContent = `
                    <div class="block-header">
                        <span class="block-type"><i class="fas fa-link"></i> Link</span>
                        <div class="block-controls">
                            <button type="button" onclick="blockEditor.moveBlock(${index}, -1)" ${index === 0 ? 'disabled' : ''}>
                                <i class="fas fa-arrow-up"></i>
                            </button>
                            <button type="button" onclick="blockEditor.moveBlock(${index}, 1)" ${index === this.blocks.length - 1 ? 'disabled' : ''}>
                                <i class="fas fa-arrow-down"></i>
                            </button>
                            <button type="button" onclick="blockEditor.removeBlock(${index})" class="delete-btn">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                    <input type="text" class="block-input" placeholder="Link text..." 
                           value="${block.text || ''}" onchange="blockEditor.updateBlock(${index}, 'text', this.value)">
                    <input type="url" class="block-input" placeholder="URL..." 
                           value="${block.url || ''}" onchange="blockEditor.updateBlock(${index}, 'url', this.value)">
                `;
                break;
        }

        div.innerHTML = blockContent;
        console.log('Created block element:', block.type, div);
        return div;
    }

    showAddMenu(event) {
        const menu = this.container.querySelector('.add-menu');
        menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
    }

    addBlock(type) {
        let newBlock = { type };
        
        switch (type) {
            case 'text':
                newBlock.content = '';
                break;
            case 'heading':
                newBlock.level = 'h2';
                newBlock.content = '';
                break;
            case 'image':
                newBlock.url = '';
                newBlock.alt = '';
                break;
            case 'link':
                newBlock.text = '';
                newBlock.url = '';
                break;
        }

        this.blocks.push(newBlock);
        this.render();
        
        // Hide menu
        this.container.querySelector('.add-menu').style.display = 'none';
    }

    updateBlock(index, field, value) {
        if (this.blocks[index]) {
            this.blocks[index][field] = value;
            this.updateHiddenField();
        }
    }

    removeBlock(index) {
        if (this.blocks.length > 1) {
            this.blocks.splice(index, 1);
            this.render();
        }
    }

    moveBlock(index, direction) {
        const newIndex = index + direction;
        if (newIndex >= 0 && newIndex < this.blocks.length) {
            [this.blocks[index], this.blocks[newIndex]] = [this.blocks[newIndex], this.blocks[index]];
            this.render();
        }
    }

    updateHiddenField() {
        this.hiddenField.value = JSON.stringify(this.blocks);
    }

    updateRichText(index) {
        const editor = this.container.querySelector(`[data-block-index="${index}"]`);
        if (editor && this.blocks[index]) {
            this.blocks[index].content = editor.innerHTML;
            this.updateHiddenField();
        }
    }

    formatText(index, format) {
        const editor = this.container.querySelector(`[data-block-index="${index}"]`);
        if (!editor) {
            console.error('Editor not found for index:', index);
            return;
        }

        editor.focus();
        
        // Check if text is selected
        const selection = window.getSelection();
        if (selection.rangeCount === 0 || selection.toString().trim() === '') {
            alert('Please select some text first');
            return;
        }

        console.log('Applying format:', format, 'to selected text:', selection.toString());

        // Apply formatting
        try {
            switch (format) {
                case 'bold':
                    document.execCommand('bold', false, null);
                    break;
                case 'italic':
                    document.execCommand('italic', false, null);
                    break;
                case 'underline':
                    document.execCommand('underline', false, null);
                    break;
            }
        } catch (error) {
            console.error('Error applying format:', error);
        }

        // Update the block content
        this.updateRichText(index);
    }

    insertLink(index) {
        const editor = this.container.querySelector(`[data-block-index="${index}"]`);
        if (!editor) return;

        editor.focus();
        
        const selection = window.getSelection();
        if (selection.rangeCount === 0 || selection.toString().trim() === '') {
            alert('Please select some text to turn into a link');
            return;
        }

        const url = prompt('Enter the URL:', 'https://');
        if (url && url.trim() !== '' && url !== 'https://') {
            document.execCommand('createLink', false, url);
            
            // Update the block content
            this.updateRichText(index);
        }
    }

    handlePaste(event, index) {
        event.preventDefault();
        
        // Get plain text from clipboard
        const text = (event.clipboardData || window.clipboardData).getData('text/plain');
        
        // Insert plain text at cursor position
        document.execCommand('insertText', false, text);
        
        // Update the block content
        this.updateRichText(index);
    }
}

// Initialize when DOM is loaded
let blockEditor;
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, looking for block-editor-container');
    const container = document.getElementById('block-editor-container');
    const hiddenField = document.getElementById('content_blocks');
    
    if (container && hiddenField) {
        console.log('Found container and hidden field, initializing block editor');
        blockEditor = new BlogBlockEditor('block-editor-container', 'content_blocks');
    } else {
        console.log('Container or hidden field not found:', {
            container: !!container,
            hiddenField: !!hiddenField
        });
    }
});
