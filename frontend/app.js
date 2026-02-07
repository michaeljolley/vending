// Valentine's Candy Machine - Frontend JavaScript

class CandyMachine {
    constructor() {
        this.credits = 0;
        this.slots = [];
        this.busy = false;
        this.ws = null;
        
        this.creditsEl = document.getElementById('credits');
        this.slotsEl = document.getElementById('slots');
        this.statusEl = document.getElementById('status');
        this.instructionsEl = document.getElementById('instructions');
        
        this.init();
        this.createFloatingHearts();
    }
    
    createFloatingHearts() {
        const container = document.getElementById('hearts-bg');
        const hearts = ['💕', '💖', '💗', '💓', '💝', '💘', '❤️', '💜', '💛'];
        
        // Create initial hearts
        for (let i = 0; i < 15; i++) {
            this.spawnHeart(container, hearts, i * 500);
        }
        
        // Continuously spawn hearts
        setInterval(() => {
            this.spawnHeart(container, hearts, 0);
        }, 800);
    }
    
    spawnHeart(container, hearts, delay) {
        setTimeout(() => {
            const heart = document.createElement('div');
            heart.className = 'floating-heart';
            heart.textContent = hearts[Math.floor(Math.random() * hearts.length)];
            heart.style.left = Math.random() * 100 + '%';
            heart.style.animationDuration = (6 + Math.random() * 4) + 's';
            heart.style.fontSize = (1.5 + Math.random() * 1.5) + 'rem';
            container.appendChild(heart);
            
            // Remove after animation
            setTimeout(() => heart.remove(), 10000);
        }, delay);
    }
    
    spawnConfetti(x, y) {
        const emojis = ['🎉', '✨', '💖', '🍬', '⭐', '💕', '🌟'];
        for (let i = 0; i < 12; i++) {
            const confetti = document.createElement('div');
            confetti.className = 'confetti';
            confetti.textContent = emojis[Math.floor(Math.random() * emojis.length)];
            confetti.style.left = (x + (Math.random() - 0.5) * 100) + 'px';
            confetti.style.top = y + 'px';
            confetti.style.animationDuration = (1 + Math.random() * 0.5) + 's';
            document.body.appendChild(confetti);
            
            setTimeout(() => confetti.remove(), 2000);
        }
    }
    
    async init() {
        await this.fetchState();
        this.connectWebSocket();
    }
    
    async fetchState() {
        try {
            const response = await fetch('/api/state');
            const state = await response.json();
            this.updateState(state);
        } catch (error) {
            console.error('Failed to fetch state:', error);
            this.showStatus('Connection error', 'error');
        }
    }
    
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'state') {
                this.updateState(data);
            }
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket disconnected, reconnecting...');
            setTimeout(() => this.connectWebSocket(), 2000);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }
    
    updateState(state) {
        const prevCredits = this.credits;
        this.credits = state.credits;
        this.slots = state.slots;
        this.busy = state.busy;
        
        // Update credits display with animation
        this.creditsEl.textContent = this.credits;
        if (state.credits > prevCredits) {
            this.creditsEl.classList.add('pulse');
            setTimeout(() => this.creditsEl.classList.remove('pulse'), 600);
            this.showStatus('💌 Envelope received! +1 credit!', 'success');
            
            // Spawn confetti at credits display
            const rect = this.creditsEl.getBoundingClientRect();
            this.spawnConfetti(rect.left + rect.width / 2, rect.top);
        }
        
        // Update instructions
        if (this.credits > 0) {
            this.instructionsEl.textContent = '🍬 Pick your treat! 🍬';
        } else {
            this.instructionsEl.textContent = '✉️ Put your valentine in the envelope and drop it in! ✉️';
        }
        
        this.renderSlots();
    }
    
    renderSlots() {
        this.slotsEl.innerHTML = '';
        
        for (const slot of this.slots) {
            const button = document.createElement('button');
            button.className = 'slot-button';
            button.disabled = this.credits < 1 || this.busy;
            
            if (this.busy) {
                button.classList.add('dispensing');
            }
            
            button.innerHTML = `
                <span class="slot-number">${slot.id}</span>
                <span class="slot-name">${slot.name}</span>
            `;
            
            button.addEventListener('click', (e) => {
                this.dispense(slot.id);
                // Spawn confetti on button
                const rect = button.getBoundingClientRect();
                this.spawnConfetti(rect.left + rect.width / 2, rect.top);
            });
            
            this.slotsEl.appendChild(button);
        }
    }
    
    async dispense(slotId) {
        if (this.credits < 1 || this.busy) {
            return;
        }
        
        try {
            this.busy = true;
            this.renderSlots();
            this.showStatus('🎰 Dispensing your treat...', '');
            
            const response = await fetch(`/api/dispense/${slotId}`, {
                method: 'POST'
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Dispense failed');
            }
            
            this.showStatus('🎉 Enjoy your candy! 🍬', 'success');
        } catch (error) {
            console.error('Dispense error:', error);
            this.showStatus(error.message, 'error');
        }
    }
    
    showStatus(message, type) {
        this.statusEl.textContent = message;
        this.statusEl.className = 'status visible';
        if (type) {
            this.statusEl.classList.add(type);
        }
        
        setTimeout(() => {
            this.statusEl.classList.remove('visible');
        }, 3500);
    }
}

// Start the app
document.addEventListener('DOMContentLoaded', () => {
    window.candyMachine = new CandyMachine();
});
