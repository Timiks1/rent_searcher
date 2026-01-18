// Translations for the application
const translations = {
    ua: {
        // Header
        'app.title': '🏠 Фільтр оголошень про оренду',
        'app.subtitle': 'Пошук житла з Telegram каналу',

        // Stats bar
        'stats.total': 'Всього оголошень:',
        'stats.with_price': 'З ціною:',
        'stats.with_location': 'З локацією:',
        'stats.updated': 'Оновлено:',

        // Filters section
        'filters.title': 'Налаштування та фільтри',
        'filters.channels': '📺 Telegram канали',
        'filters.channels_hint': '(наприклад: @arenda_kvartir)',
        'filters.add_channel': '➕ Додати',
        'filters.no_channels': 'Немає доданих каналів',

        // Search filters
        'filters.search_title': 'Фільтри пошуку',
        'filters.min_price': 'Мінімальна ціна (млн VND або USD)',
        'filters.max_price': 'Максимальна ціна (млн VND або USD)',
        'filters.include_locations': 'Включити локації (whitelist)',
        'filters.include_hint': 'тільки з цими районами',
        'filters.exclude_areas': '⛔ Виключити райони (blacklist)',
        'filters.exclude_hint': 'пошук по всьому тексту, через кому',
        'filters.sort': '📊 Сортування',
        'filters.sort_hint': 'порядок відображення',

        // Sort options
        'sort.date_desc': 'Спочатку нові',
        'sort.date_asc': 'Спочатку старі',
        'sort.price_desc': 'Ціна: від більшої до меншої',
        'sort.price_asc': 'Ціна: від меншої до більшої',

        // Buttons
        'btn.apply_filters': '🔍 Застосувати фільтри',
        'btn.reset': '↺ Скинути',
        'btn.refresh': '⟳ Оновити повідомлення',

        // Results
        'results.title': 'Результати',
        'results.count': 'оголошень',
        'results.empty': 'Натисніть "Оновити повідомлення" для завантаження оголошень',
        'results.loading': 'Завантаження...',

        // Messages
        'msg.price_not_set': 'Ціна не вказана',
        'msg.location_not_set': 'Локація не вказана',
        'msg.open_telegram': '📱 Відкрити в Telegram',

        // Notifications
        'notif.channel_added': 'Канал {channel} додано',
        'notif.channel_removed': 'Канал {channel} видалено',
        'notif.channel_exists': 'Цей канал вже додано',
        'notif.channel_invalid': 'Канал повинен починатися з @ або бути ID',
        'notif.enter_channel': 'Введіть назву каналу',
        'notif.add_channel_first': 'Спочатку додайте хоча б один канал!',
        'notif.loading_from_channels': 'Завантаження повідомлень з {count} каналів...',
        'notif.loaded_messages': 'Завантажено {count} повідомлень з {channels} каналів',
        'notif.found_messages': 'Знайдено {count} оголошень',
        'notif.no_results': 'Немає оголошень, що відповідають критеріям',

        // Placeholders
        'placeholder.channel': '@channel_name',
        'placeholder.min_price': 'Від 0',
        'placeholder.max_price': 'До ∞',
        'placeholder.locations': 'Mỹ An, An Thượng...',
        'placeholder.exclude': 'my an, hoa hai, khue my...',

        // Photo
        'photo.loading': '📸 Завантаження...',
        'photo.error': '⚠️ Помилка завантаження',
        'photo.channel_missing': '⚠️ Канал не вказано',

        // Errors
        'error.stats_loading': 'Помилка завантаження статистики',
        'error.messages_loading': 'Помилка завантаження повідомлень',
        'error.data_loading': 'Помилка завантаження даних. Перевірте налаштування API.',
        'error.refresh': 'Помилка оновлення',

        // Cache age
        'cache.just_now': 'Щойно',
        'cache.minutes_ago': '{minutes} хв тому',
        'cache.not_loaded': 'Не завантажено',

        // Other
        'other.views_abbr': 'перегл.',
    },

    vi: {
        // Header
        'app.title': '🏠 Bộ lọc tin cho thuê nhà',
        'app.subtitle': 'Tìm kiếm nhà từ kênh Telegram',

        // Stats bar
        'stats.total': 'Tổng tin đăng:',
        'stats.with_price': 'Có giá:',
        'stats.with_location': 'Có địa điểm:',
        'stats.updated': 'Cập nhật:',

        // Filters section
        'filters.title': 'Cài đặt và bộ lọc',
        'filters.channels': '📺 Kênh Telegram',
        'filters.channels_hint': '(ví dụ: @arenda_kvartir)',
        'filters.add_channel': '➕ Thêm',
        'filters.no_channels': 'Chưa có kênh nào',

        // Search filters
        'filters.search_title': 'Bộ lọc tìm kiếm',
        'filters.min_price': 'Giá tối thiểu (triệu VND hoặc USD)',
        'filters.max_price': 'Giá tối đa (triệu VND hoặc USD)',
        'filters.include_locations': 'Bao gồm địa điểm (whitelist)',
        'filters.include_hint': 'chỉ những khu vực này',
        'filters.exclude_areas': '⛔ Loại trừ khu vực (blacklist)',
        'filters.exclude_hint': 'tìm trong toàn bộ văn bản, phân cách bằng dấu phẩy',
        'filters.sort': '📊 Sắp xếp',
        'filters.sort_hint': 'thứ tự hiển thị',

        // Sort options
        'sort.date_desc': 'Mới nhất trước',
        'sort.date_asc': 'Cũ nhất trước',
        'sort.price_desc': 'Giá: Cao đến thấp',
        'sort.price_asc': 'Giá: Thấp đến cao',

        // Buttons
        'btn.apply_filters': '🔍 Áp dụng bộ lọc',
        'btn.reset': '↺ Đặt lại',
        'btn.refresh': '⟳ Làm mới tin nhắn',

        // Results
        'results.title': 'Kết quả',
        'results.count': 'tin đăng',
        'results.empty': 'Nhấn "Làm mới tin nhắn" để tải tin đăng',
        'results.loading': 'Đang tải...',

        // Messages
        'msg.price_not_set': 'Chưa có giá',
        'msg.location_not_set': 'Chưa có địa điểm',
        'msg.open_telegram': '📱 Mở trong Telegram',

        // Notifications
        'notif.channel_added': 'Đã thêm kênh {channel}',
        'notif.channel_removed': 'Đã xóa kênh {channel}',
        'notif.channel_exists': 'Kênh này đã được thêm',
        'notif.channel_invalid': 'Kênh phải bắt đầu bằng @ hoặc là ID',
        'notif.enter_channel': 'Nhập tên kênh',
        'notif.add_channel_first': 'Vui lòng thêm ít nhất một kênh trước!',
        'notif.loading_from_channels': 'Đang tải tin nhắn từ {count} kênh...',
        'notif.loaded_messages': 'Đã tải {count} tin nhắn từ {channels} kênh',
        'notif.found_messages': 'Tìm thấy {count} tin đăng',
        'notif.no_results': 'Không có tin đăng phù hợp với tiêu chí',

        // Placeholders
        'placeholder.channel': '@ten_kenh',
        'placeholder.min_price': 'Từ 0',
        'placeholder.max_price': 'Đến ∞',
        'placeholder.locations': 'Mỹ An, An Thượng...',
        'placeholder.exclude': 'my an, hoa hai, khue my...',

        // Photo
        'photo.loading': '📸 Đang tải...',
        'photo.error': '⚠️ Lỗi tải',
        'photo.channel_missing': '⚠️ Chưa có kênh',

        // Errors
        'error.stats_loading': 'Lỗi tải thống kê',
        'error.messages_loading': 'Lỗi tải tin nhắn',
        'error.data_loading': 'Lỗi tải dữ liệu. Kiểm tra cài đặt API.',
        'error.refresh': 'Lỗi làm mới',

        // Cache age
        'cache.just_now': 'Vừa xong',
        'cache.minutes_ago': '{minutes} phút trước',
        'cache.not_loaded': 'Chưa tải',

        // Other
        'other.views_abbr': 'lượt xem',
    }
};

// Get translation for current language
function t(key, replacements = {}) {
    const currentLang = localStorage.getItem('language') || 'ua';
    let text = translations[currentLang][key] || translations['ua'][key] || key;

    // Replace placeholders like {channel}, {count}, etc.
    Object.keys(replacements).forEach(placeholder => {
        text = text.replace(`{${placeholder}}`, replacements[placeholder]);
    });

    return text;
}

// Apply translations to the page
function applyTranslations() {
    const currentLang = localStorage.getItem('language') || 'ua';

    // Update all elements with data-i18n attribute
    document.querySelectorAll('[data-i18n]').forEach(element => {
        const key = element.getAttribute('data-i18n');
        const translation = translations[currentLang][key];

        if (translation) {
            if (element.tagName === 'INPUT' && element.placeholder !== undefined) {
                element.placeholder = translation;
            } else {
                element.textContent = translation;
            }
        }
    });

    // Update language selector
    const langSelector = document.getElementById('languageSelector');
    if (langSelector) {
        langSelector.value = currentLang;
    }
}

// Switch language
function switchLanguage(lang) {
    localStorage.setItem('language', lang);
    applyTranslations();

    // Re-render messages to update prices and locations text
    if (typeof currentMessages !== 'undefined' && currentMessages.length > 0) {
        displayMessages(currentMessages);
    }

    // Update stats if available
    if (typeof loadStats === 'function') {
        loadStats();
    }
}
