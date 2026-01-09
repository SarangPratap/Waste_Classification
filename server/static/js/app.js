// Category colors and icons
const categoryColors = {
    'battery': '#FFD700',
    'biological': '#32CD32',
    'cardboard': '#8B4513',
    'clothes': '#9370DB',
    'glass': '#00CED1',
    'metal': '#808080',
    'paper': '#87CEEB',
    'plastic': '#1E90FF',
    'shoe': '#FF8C00'
};

const categoryIcons = {
    'battery': '🔋',
    'biological': '🍎',
    'cardboard': '📦',
    'clothes': '👕',
    'glass': '🫙',
    'metal': '🔩',
    'paper': '📄',
    'plastic': '🍾',
    'shoe': '👟'
};

// WebSocket connection
const socket = io(window.location.origin);

// Connection status
socket.on('connect', () => {
    console.log('✅ Connected to server');
    updateConnectionStatus(true);
});

socket.on('disconnect', () => {
    console.log('❌ Disconnected from server');
    updateConnectionStatus(false);
});

// Listen for new predictions
socket.on('new_prediction', (data) => {
    console.log('📊 New prediction:', data);
    updatePredictionCard(data);
    addToHistory(data);
    updateStats();
});

// Update connection status indicator
function updateConnectionStatus(connected) {
    const statusEl = document.getElementById('connectionStatus');
    const dotEl = statusEl.querySelector('.status-dot');
    const textEl = statusEl.querySelector('span:last-child');
    
    if (connected) {
        dotEl.classList.remove('disconnected');
        textEl.textContent = 'Connected';
    } else {
        dotEl.classList.add('disconnected');
        textEl.textContent = 'Disconnected';
    }
}

// Update the main prediction card
function updatePredictionCard(prediction) {
    const card = document.getElementById('predictionCard');
    const icon = document.getElementById('predictionIcon');
    const category = document.getElementById('predictionCategory');
    const confidenceFill = document.getElementById('confidenceFill');
    const confidenceText = document.getElementById('confidenceText');
    const time = document.getElementById('predictionTime');
    
    // Update content
    icon.textContent = categoryIcons[prediction.category] || '🗑️';
    category.textContent = prediction.category;
    category.style.color = categoryColors[prediction.category] || '#ffffff';
    
    // Animate confidence bar
    const confidencePercent = (prediction.confidence * 100).toFixed(1);
    confidenceFill.style.width = confidencePercent + '%';
    confidenceFill.style.background = `linear-gradient(90deg, ${categoryColors[prediction.category]}, #1E90FF)`;
    confidenceText.textContent = confidencePercent + '%';
    
    // Update timestamp
    time.textContent = 'Just now';
    
    // Add border color animation
    card.style.borderLeft = `4px solid ${categoryColors[prediction.category]}`;
    
    // Trigger animations
    icon.style.animation = 'none';
    setTimeout(() => {
        icon.style.animation = 'bounceIn 0.5s ease';
    }, 10);
}

// Add prediction to history list
function addToHistory(prediction) {
    const historyList = document.getElementById('historyList');
    
    // Remove "no data" message if present
    const noData = historyList.querySelector('.no-data');
    if (noData) {
        noData.remove();
    }
    
    // Create history item
    const item = document.createElement('div');
    item.className = 'history-item category-' + prediction.category;
    item.style.borderLeftColor = categoryColors[prediction.category];
    
    const confidencePercent = (prediction.confidence * 100).toFixed(1);
    
    item.innerHTML = `
        <div class="history-icon">${categoryIcons[prediction.category] || '🗑️'}</div>
        <div class="history-details">
            <div class="history-category">${prediction.category}</div>
            <div class="history-time">Just now</div>
        </div>
        <div class="history-confidence">${confidencePercent}%</div>
    `;
    
    // Add to top of list
    historyList.insertBefore(item, historyList.firstChild);
    
    // Keep only last 10 items
    const items = historyList.querySelectorAll('.history-item');
    if (items.length > 10) {
        items[items.length - 1].remove();
    }
    
    // Update time stamps
    updateTimeStamps();
}

// Update time stamps for history items
function updateTimeStamps() {
    const items = document.querySelectorAll('.history-item');
    items.forEach((item, index) => {
        const timeEl = item.querySelector('.history-time');
        if (index === 0) {
            timeEl.textContent = 'Just now';
        } else if (index < 60) {
            timeEl.textContent = index + 's ago';
        } else {
            timeEl.textContent = Math.floor(index / 60) + 'm ago';
        }
    });
}

// Update statistics
async function updateStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        if (data.status === 'success') {
            const stats = data.stats;
            
            // Update stat values
            document.getElementById('statTotal').textContent = stats.total_classifications;
            document.getElementById('statMostCommon').textContent = 
                stats.most_common_category !== 'none' ? stats.most_common_category : '-';
            document.getElementById('statAvgConfidence').textContent = 
                (stats.average_confidence * 100).toFixed(1) + '%';
            
            // Update category distribution
            updateCategoryDistribution(stats.category_counts);
        }
    } catch (error) {
        console.error('Error fetching stats:', error);
    }
}

// Update category distribution chips
function updateCategoryDistribution(categoryCounts) {
    const container = document.getElementById('categoryDistribution');
    container.innerHTML = '';
    
    for (const [category, count] of Object.entries(categoryCounts)) {
        const chip = document.createElement('div');
        chip.className = 'category-chip';
        chip.style.background = categoryColors[category] + '33'; // Add transparency
        chip.style.color = categoryColors[category];
        chip.style.borderLeft = `3px solid ${categoryColors[category]}`;
        
        chip.innerHTML = `
            <span>${categoryIcons[category] || '🗑️'}</span>
            <span>${category}: ${count}</span>
        `;
        
        container.appendChild(chip);
    }
}

// Connect to video stream
function connectToStream() {
    const espIp = document.getElementById('espIpInput').value.trim();
    
    if (!espIp) {
        alert('Please enter ESP32-CAM IP address');
        return;
    }
    
    const streamUrl = `http://${espIp}/stream`;
    const videoStream = document.getElementById('videoStream');
    const videoOverlay = document.getElementById('videoOverlay');
    
    videoStream.src = streamUrl;
    videoOverlay.classList.add('hidden');
    
    // Handle errors
    videoStream.onerror = () => {
        videoOverlay.classList.remove('hidden');
        videoOverlay.innerHTML = '<p>❌ Failed to connect to stream<br>Check IP address and network</p>';
    };
    
    videoStream.onload = () => {
        console.log('✅ Stream connected');
    };
    
    // Save IP to localStorage
    localStorage.setItem('esp32cam_ip', espIp);
}

// Format time ago
function formatTimeAgo(timestamp) {
    const now = new Date();
    const then = new Date(timestamp);
    const seconds = Math.floor((now - then) / 1000);
    
    if (seconds < 60) return seconds + 's ago';
    if (seconds < 3600) return Math.floor(seconds / 60) + 'm ago';
    if (seconds < 86400) return Math.floor(seconds / 3600) + 'h ago';
    return Math.floor(seconds / 86400) + 'd ago';
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('🗑️ Waste Classification Dashboard Loaded');
    
    // Load saved IP from localStorage
    const savedIp = localStorage.getItem('esp32cam_ip');
    if (savedIp) {
        document.getElementById('espIpInput').value = savedIp;
    }
    
    // Fetch initial stats
    updateStats();
    
    // Fetch recent predictions
    fetchRecentPredictions();
    
    // Update time stamps every second
    setInterval(updateTimeStamps, 1000);
    
    // Update stats every 5 seconds
    setInterval(updateStats, 5000);
    
    // Allow Enter key to connect stream
    document.getElementById('espIpInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            connectToStream();
        }
    });
});

// Fetch recent predictions on load
async function fetchRecentPredictions() {
    try {
        const response = await fetch('/api/predictions');
        const data = await response.json();
        
        if (data.status === 'success' && data.predictions.length > 0) {
            // Add last 10 predictions to history
            const predictions = data.predictions.slice(-10).reverse();
            predictions.forEach(prediction => {
                addToHistory(prediction);
            });
            
            // Update current prediction card with latest
            if (predictions.length > 0) {
                updatePredictionCard(predictions[0]);
            }
        }
    } catch (error) {
        console.error('Error fetching recent predictions:', error);
    }
}
