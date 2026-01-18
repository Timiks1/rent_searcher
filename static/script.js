const API_BASE = '';

// State
let currentMessages = [];
let channels = []; // Array of channel names

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Apply translations first
    applyTranslations();

    loadStats();
    loadCurrentChannels();

    // Load saved channels from localStorage
    const savedChannels = localStorage.getItem('telegram_channels');
    if (savedChannels) {
        try {
            channels = JSON.parse(savedChannels);
            renderChannelsList();
        } catch (e) {
            channels = [];
        }
    }

    // Auto-load messages on start if channels are set
    setTimeout(() => {
        if (channels.length > 0) {
            applyFilters();
        }
    }, 500);
});

// Load statistics
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/api/stats`);
        const stats = await response.json();
        
        document.getElementById('totalMessages').textContent = stats.total_messages;
        document.getElementById('messagesWithPrice').textContent = stats.messages_with_price;
        document.getElementById('messagesWithLocation').textContent = stats.messages_with_location;
        
        if (stats.cache_age_minutes !== null) {
            const ageText = stats.cache_age_minutes < 1
                ? t('cache.just_now')
                : t('cache.minutes_ago', {minutes: Math.round(stats.cache_age_minutes)});
            document.getElementById('cacheAge').textContent = ageText;
        } else {
            document.getElementById('cacheAge').textContent = t('cache.not_loaded');
        }
    } catch (error) {
        console.error('Error loading stats:', error);
        showNotification(t('error.stats_loading'), 'error');
    }
}

// Apply filters and load messages
async function applyFilters() {
    const minPrice = document.getElementById('minPrice').value;
    const maxPrice = document.getElementById('maxPrice').value;
    const location = document.getElementById('location').value;
    const excludeAreas = document.getElementById('excludeAreas').value;
    const sortBy = document.getElementById('sortBy').value;
    
    const params = new URLSearchParams();
    if (minPrice) params.append('min_price', minPrice);
    if (maxPrice) params.append('max_price', maxPrice);
    if (location) params.append('location', location);
    if (excludeAreas) params.append('exclude_areas', excludeAreas);
    if (sortBy) params.append('sort_by', sortBy);
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE}/api/messages?${params.toString()}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const messages = await response.json();
        currentMessages = messages;
        displayMessages(messages);
        loadStats();

        showNotification(t('notif.found_messages', {count: messages.length}), 'success');
    } catch (error) {
        console.error('Error loading messages:', error);
        showNotification(t('error.messages_loading') + ': ' + error.message, 'error');
        displayEmptyState(t('error.data_loading'));
    } finally {
        showLoading(false);
    }
}

// Add channel to the list
function addChannel() {
    const input = document.getElementById('channelInput');
    const channelName = input.value.trim();

    if (!channelName) {
        showNotification(t('notif.enter_channel'), 'error');
        return;
    }

    // Validate channel format
    if (!channelName.startsWith('@') && !channelName.match(/^-?\d+$/)) {
        showNotification(t('notif.channel_invalid'), 'error');
        return;
    }

    // Check if channel already exists
    if (channels.includes(channelName)) {
        showNotification(t('notif.channel_exists'), 'error');
        return;
    }

    // Add to array
    channels.push(channelName);

    // Save to localStorage
    localStorage.setItem('telegram_channels', JSON.stringify(channels));

    // Clear input
    input.value = '';

    // Re-render list
    renderChannelsList();

    showNotification(t('notif.channel_added', {channel: channelName}), 'success');
}

// Remove channel from the list
function removeChannel(channelName) {
    channels = channels.filter(ch => ch !== channelName);

    // Save to localStorage
    localStorage.setItem('telegram_channels', JSON.stringify(channels));

    // Re-render list
    renderChannelsList();

    showNotification(t('notif.channel_removed', {channel: channelName}), 'success');
}

// Render channels list
function renderChannelsList() {
    const container = document.getElementById('channelsList');

    if (channels.length === 0) {
        container.innerHTML = `<div class="empty-channels" data-i18n="filters.no_channels">${t('filters.no_channels')}</div>`;
        return;
    }

    container.innerHTML = channels.map(channel => `
        <div class="channel-item">
            <span class="channel-name">📺 ${channel}</span>
            <button class="btn-remove" onclick="removeChannel('${channel}')" title="${t('notif.channel_removed', {channel: ''})}">
                ✕
            </button>
        </div>
    `).join('');
}

// Load current channels from backend
async function loadCurrentChannels() {
    try {
        const response = await fetch(`${API_BASE}/api/current-channels`);
        const data = await response.json();

        if (channels.length === 0 && data.channels && data.channels.length > 0) {
            channels = data.channels;
            localStorage.setItem('telegram_channels', JSON.stringify(channels));
            renderChannelsList();
        }
    } catch (error) {
        console.error('Error loading current channels:', error);
    }
}

// Refresh messages from Telegram
async function refreshMessages() {
    if (channels.length === 0) {
        showNotification(t('notif.add_channel_first'), 'error');
        document.getElementById('channelInput').focus();
        return;
    }

    showLoading(true);
    showNotification(t('notif.loading_from_channels', {count: channels.length}), 'info');

    try {
        // Send channels as JSON array in request body
        const response = await fetch(`${API_BASE}/api/fetch-messages`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ channels: channels })
        });

        if (!response.ok) {
            const errorData = await response.json();
            const errorMessage = errorData.detail || `HTTP error! status: ${response.status}`;
            throw new Error(errorMessage);
        }

        const result = await response.json();
        showNotification(t('notif.loaded_messages', {count: result.total_messages, channels: channels.length}), 'success');

        // Reload with current filters
        await applyFilters();
    } catch (error) {
        console.error('Error refreshing messages:', error);
        showNotification(t('error.refresh') + ': ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Reset filters
function resetFilters() {
    document.getElementById('minPrice').value = '';
    document.getElementById('maxPrice').value = '';
    document.getElementById('location').value = '';
    document.getElementById('excludeAreas').value = '';
    document.getElementById('sortBy').value = 'date_desc';
    applyFilters();
}

// Display messages
// Lazy load photo when it comes into view
async function lazyLoadPhoto(placeholder) {
    const photoId = placeholder.dataset.photoId;
    const msgId = placeholder.dataset.msgId;
    const photoIndex = parseInt(placeholder.dataset.photoIndex);
    const channel = placeholder.dataset.channel;

    if (!photoId) {
        placeholder.innerHTML = `<div class="photo-error">${t('photo.error')}</div>`;
        return;
    }

    if (!channel || channel === '') {
        console.error(`❌ Missing channel for photo ${photoId}`);
        placeholder.innerHTML = `<div class="photo-error">${t('photo.channel_missing')}</div>`;
        return;
    }

    try {
        const url = `${API_BASE}/api/photo/${photoId}?channel=${encodeURIComponent(channel)}`;
        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`Photo download failed: ${response.status}`);
        }

        const data = await response.json();

        // Replace placeholder with actual image
        const img = document.createElement('img');
        img.src = data.photo_url;
        img.alt = `Фото из объявления ${msgId}`;
        img.className = 'message-photo';
        img.loading = 'lazy';
        img.dataset.msgId = msgId;
        img.dataset.photoIndex = photoIndex;
        img.onclick = () => openPhotoModal(img);

        placeholder.replaceWith(img);
    } catch (error) {
        console.error(`❌ Failed to load photo ${photoId}:`, error);
        placeholder.innerHTML = `<div class="photo-error">${t('photo.error')}</div>`;
    }
}

// Setup Intersection Observer for lazy loading photos
function setupPhotoLazyLoading() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const placeholder = entry.target;
                lazyLoadPhoto(placeholder);
                observer.unobserve(placeholder); // Load only once
            }
        });
    }, {
        rootMargin: '50px' // Start loading 50px before visible
    });
    
    // Observe all photo placeholders
    document.querySelectorAll('.message-photo-placeholder').forEach(placeholder => {
        observer.observe(placeholder);
    });
}

function displayMessages(messages) {
    const messagesList = document.getElementById('messagesList');
    const resultsCountNumber = document.getElementById('resultsCountNumber');

    resultsCountNumber.textContent = messages.length;

    if (messages.length === 0) {
        displayEmptyState(t('notif.no_results'));
        return;
    }

    messagesList.innerHTML = messages.map(msg => createMessageCard(msg)).join('');

    // Setup lazy loading for photos
    setupPhotoLazyLoading();
}

// Create message card HTML
function createMessageCard(msg) {
    const date = new Date(msg.date).toLocaleString('uk-UA');
    const priceText = msg.price ? formatPrice(msg.price) : t('msg.price_not_set');
    const locationText = msg.location && msg.location.length > 0
        ? msg.location.join(', ')
        : t('msg.location_not_set');
    
    // Create photo gallery HTML with lazy loading
    let photosHtml = '';
    if (msg.photo_ids && Array.isArray(msg.photo_ids) && msg.photo_ids.length > 0) {
        photosHtml = `
            <div class="message-photos">
                ${msg.photo_ids.map((photoId, index) => `
                    <div class="message-photo-placeholder" data-photo-id="${photoId}" data-msg-id="${msg.id}" data-photo-index="${index}" data-channel="${msg.channel || ''}">
                        <div class="photo-loader">${t('photo.loading')}</div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    return `
        <div class="message-card" data-message-id="${msg.id}">
            <div class="message-header">
                <span class="message-date">📅 ${date}</span>
                <div class="message-meta">
                    ${msg.channel ? `<span class="meta-badge channel-badge">📺 ${msg.channel}</span>` : ''}
                    ${msg.price ? `<span class="meta-badge price-badge">💰 ${priceText}</span>` : ''}
                    ${msg.views ? `<span class="meta-badge views-badge">👁 ${msg.views} ${t('other.views_abbr')}</span>` : ''}
                </div>
            </div>

            ${photosHtml}

            ${msg.location && msg.location.length > 0 ? `
                <div class="message-locations">
                    <strong>📍 Локация:</strong> ${locationText}
                </div>
            ` : ''}

            <div class="message-text">${escapeHtml(msg.text)}</div>

            <div class="message-footer">
                <a href="${msg.link}" target="_blank" class="message-link">
                    ${t('msg.open_telegram')}
                </a>
            </div>
        </div>
    `;
}

// Open photo in modal for full view
// Photo gallery state
let currentPhotoGallery = [];
let currentPhotoIndex = 0;

function openPhotoModal(imgElement) {
    const modal = document.getElementById('photoModal') || createPhotoModal();
    
    // Get message ID and current photo index
    const messageId = imgElement.dataset.msgId;
    const clickedIndex = parseInt(imgElement.dataset.photoIndex || 0);
    
    // Find all photos in this message
    const messageCard = document.querySelector(`.message-card[data-message-id="${messageId}"]`);
    
    if (messageCard) {
        // Get all loaded photos (not placeholders)
        const allPhotoElements = Array.from(messageCard.querySelectorAll('.message-photo'))
            .sort((a, b) => {
                const indexA = parseInt(a.dataset.photoIndex || 0);
                const indexB = parseInt(b.dataset.photoIndex || 0);
                return indexA - indexB;
            });
        
        currentPhotoGallery = allPhotoElements.map(img => img.src);

        // Find the index of clicked photo in the gallery
        currentPhotoIndex = allPhotoElements.findIndex(img => img === imgElement);
        if (currentPhotoIndex === -1) currentPhotoIndex = 0;
    } else {
        currentPhotoGallery = [imgElement.src];
        currentPhotoIndex = 0;
    }
    
    updateModalPhoto();
    updateNavigationButtons();
    modal.style.display = 'flex';
}

// Update photo in modal
function updateModalPhoto() {
    const modal = document.getElementById('photoModal');
    const img = modal.querySelector('.modal-photo');
    const counter = modal.querySelector('.photo-counter');
    
    if (currentPhotoGallery.length > 0) {
        img.src = currentPhotoGallery[currentPhotoIndex];
        counter.textContent = `${currentPhotoIndex + 1} / ${currentPhotoGallery.length}`;
    }
}

// Update navigation buttons visibility
function updateNavigationButtons() {
    const modal = document.getElementById('photoModal');
    const prevBtn = modal.querySelector('.modal-nav-prev');
    const nextBtn = modal.querySelector('.modal-nav-next');
    const counter = modal.querySelector('.photo-counter');
    
    if (currentPhotoGallery.length <= 1) {
        prevBtn.style.display = 'none';
        nextBtn.style.display = 'none';
        counter.style.display = 'none';
    } else {
        prevBtn.style.display = 'flex';
        nextBtn.style.display = 'flex';
        counter.style.display = 'block';
        
        // Disable buttons at boundaries
        prevBtn.style.opacity = currentPhotoIndex === 0 ? '0.3' : '1';
        prevBtn.style.cursor = currentPhotoIndex === 0 ? 'not-allowed' : 'pointer';
        nextBtn.style.opacity = currentPhotoIndex === currentPhotoGallery.length - 1 ? '0.3' : '1';
        nextBtn.style.cursor = currentPhotoIndex === currentPhotoGallery.length - 1 ? 'not-allowed' : 'pointer';
    }
}

// Navigate to previous photo
function previousPhoto() {
    if (currentPhotoIndex > 0) {
        currentPhotoIndex--;
        updateModalPhoto();
        updateNavigationButtons();
    }
}

// Navigate to next photo
function nextPhoto() {
    if (currentPhotoIndex < currentPhotoGallery.length - 1) {
        currentPhotoIndex++;
        updateModalPhoto();
        updateNavigationButtons();
    }
}

// Create photo modal if it doesn't exist
function createPhotoModal() {
    const modal = document.createElement('div');
    modal.id = 'photoModal';
    modal.className = 'modal photo-modal';
    modal.innerHTML = `
        <div class="modal-content photo-modal-content">
            <span class="close" onclick="closePhotoModal()">&times;</span>
            <button class="modal-nav-btn modal-nav-prev" onclick="previousPhoto()">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="15 18 9 12 15 6"></polyline>
                </svg>
            </button>
            <img src="" alt="Full size photo" class="modal-photo">
            <button class="modal-nav-btn modal-nav-next" onclick="nextPhoto()">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="9 18 15 12 9 6"></polyline>
                </svg>
            </button>
            <div class="photo-counter">1 / 1</div>
        </div>
    `;
    document.body.appendChild(modal);
    
    // Close on outside click (but not on navigation buttons)
    modal.onclick = function(event) {
        if (event.target === modal || event.target.classList.contains('modal-photo')) {
            // Click on left/right side of photo for navigation
            const img = modal.querySelector('.modal-photo');
            const rect = img.getBoundingClientRect();
            const clickX = event.clientX - rect.left;
            const photoWidth = rect.width;
            
            if (clickX < photoWidth * 0.3) {
                previousPhoto();
            } else if (clickX > photoWidth * 0.7) {
                nextPhoto();
            } else if (event.target === modal) {
                closePhotoModal();
            }
        }
    };
    
    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
        const modal = document.getElementById('photoModal');
        if (modal && modal.style.display === 'flex') {
            if (e.key === 'ArrowLeft') {
                previousPhoto();
            } else if (e.key === 'ArrowRight') {
                nextPhoto();
            } else if (e.key === 'Escape') {
                closePhotoModal();
            }
        }
    });
    
    return modal;
}

// Close photo modal
function closePhotoModal() {
    const modal = document.getElementById('photoModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Display empty state
function displayEmptyState(message) {
    const messagesList = document.getElementById('messagesList');
    const resultsCountNumber = document.getElementById('resultsCountNumber');

    resultsCountNumber.textContent = '0';
    messagesList.innerHTML = `
        <div class="empty-state">
            <p>${message}</p>
        </div>
    `;
}

// Show/hide loading indicator
function showLoading(show) {
    const loadingIndicator = document.getElementById('loadingIndicator');
    const messagesList = document.getElementById('messagesList');
    
    if (show) {
        loadingIndicator.style.display = 'block';
        messagesList.style.display = 'none';
    } else {
        loadingIndicator.style.display = 'none';
        messagesList.style.display = 'grid';
    }
}


// Show notification (simple implementation)
function showNotification(message, type) {
    // Only log errors to console
    if (type === 'error') {
        console.error(message);
    }
    // You can implement a proper toast notification system here
}

// Utility functions
function formatPrice(price) {
    // Detect if it's likely USD (< 10000) or VND (>= 10000)
    if (price < 10000) {
        // Format as USD
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            maximumFractionDigits: 0
        }).format(price);
    } else {
        // Format as VND
        return new Intl.NumberFormat('vi-VN', {
            style: 'currency',
            currency: 'VND',
            maximumFractionDigits: 0
        }).format(price);
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Allow Enter key to submit filters or add channel
document.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        if (e.target.id === 'channelInput') {
            addChannel();
        } else if (
            e.target.id === 'minPrice' ||
            e.target.id === 'maxPrice' ||
            e.target.id === 'location' ||
            e.target.id === 'excludeAreas'
        ) {
            applyFilters();
        }
    }
});

// Apply filters on sort change
document.addEventListener('DOMContentLoaded', () => {
    const sortSelect = document.getElementById('sortBy');
    if (sortSelect) {
        sortSelect.addEventListener('change', applyFilters);
    }
});
