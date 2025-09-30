document.addEventListener('DOMContentLoaded', () => {
    const queryInput = document.getElementById('query-input');
    const imageSizeSelect = document.getElementById('image-size-select');
    const timeRangeSelect = document.getElementById('time-range-select');
    const safeSearchToggle = document.getElementById('safe-search-toggle');
    const submitButton = document.getElementById('submit-button');
    const outputArea = document.getElementById('output-area');
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar');
    const progressStatus = document.getElementById('progress-status');
    const themeSwitcher = document.getElementById('theme-switcher');
    const suggestionsBox = document.getElementById('suggestions-box');
    const lightbox = document.getElementById('lightbox');
    const lightboxImage = lightbox.querySelector('.lightbox-image');

    let currentQuery = '';
    let currentPage = 1;
    let isLoading = false;
    let noMoreResults = false;
    let allImageUrls = [];
    let currentLightboxIndex = -1;

    const savePreference = (key, value) => localStorage.setItem(key, value);
    const getPreference = (key) => localStorage.getItem(key);

    function applySavedPreferences() {
        const savedTheme = getPreference('theme');
        if (savedTheme === 'light') document.body.classList.add('light-theme');

        const savedSize = getPreference('image_size');
        if (savedSize) imageSizeSelect.value = savedSize;

        const savedTime = getPreference('time_range');
        if (savedTime) timeRangeSelect.value = savedTime;

        const savedSafeSearch = getPreference('safe_search');
        if (savedSafeSearch === 'false') safeSearchToggle.checked = false;
    }

    themeSwitcher.addEventListener('click', () => {
        document.body.classList.toggle('light-theme');
        const newTheme = document.body.classList.contains('light-theme') ? 'light' : 'dark';
        savePreference('theme', newTheme);
    });

    imageSizeSelect.addEventListener('change', () => savePreference('image_size', imageSizeSelect.value));
    timeRangeSelect.addEventListener('change', () => savePreference('time_range', timeRangeSelect.value));
    safeSearchToggle.addEventListener('change', () => savePreference('safe_search', safeSearchToggle.checked));

    function handleMouseMove(e) {
        document.body.style.setProperty('--cursor-x', `${e.clientX}px`);
        document.body.style.setProperty('--cursor-y', `${e.clientY}px`);
        document.body.style.setProperty('--cursor-opacity', '1');
    }

    function handleMouseLeave() { document.body.style.setProperty('--cursor-opacity', '0'); }

    function addInteractiveBorderListeners(element) {
        element.addEventListener('mousemove', e => {
            const rect = element.getBoundingClientRect();
            element.style.setProperty('--x', `${e.clientX - rect.left}px`);
            element.style.setProperty('--y', `${e.clientY - rect.top}px`);
            element.style.setProperty('--opacity', '1');
        });
        element.addEventListener('mouseleave', () => element.style.setProperty('--opacity', '0'));
    }

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseleave', handleMouseLeave);
    document.querySelectorAll('.interactive-border').forEach(addInteractiveBorderListeners);

    async function startSearch(event) {
        event.preventDefault();
        const query = queryInput.value.trim();
        if (!query) {
            showError("Please enter a search query.");
            return;
        }

        currentQuery = query;
        currentPage = 1;
        allImageUrls = [];
        noMoreResults = false;
        outputArea.innerHTML = '';
        progressContainer.classList.remove('hidden');
        updateProgress(10, "Initializing search...");

        updateSearchHistory(query);
        suggestionsBox.classList.remove('visible');

        await fetchAndDisplayImages(true);

        setTimeout(() => progressContainer.classList.add('hidden'), 500);
    }

    window.startSearch = startSearch;

    async function fetchAndDisplayImages(isNewSearch = false) {
        if (isLoading || noMoreResults) return;

        isLoading = true;
        submitButton.disabled = true;
        if (!isNewSearch) {
            const loadMoreButton = document.getElementById('load-more-button');
            if (loadMoreButton) loadMoreButton.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
        }

        try {
            if (isNewSearch) updateProgress(30, "Finding images...");

            const response = await fetch('/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: currentQuery,
                    safe_search: safeSearchToggle.checked,
                    size: imageSizeSelect.value,
                    time_range: timeRangeSelect.value,
                    page: currentPage
                })
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                if (response.status === 404) {
                    noMoreResults = true;
                    const loadMoreButton = document.getElementById('load-more-button');
                    if (loadMoreButton) loadMoreButton.remove();
                    if (isNewSearch) showError(data.error || "No images found.");
                } else {
                    throw new Error(data.error || `Server error: ${response.statusText}`);
                }
                return;
            }

            if (isNewSearch) updateProgress(100, "Displaying results...");

            const newImageUrls = data.images.filter(url => !allImageUrls.includes(url));
            allImageUrls.push(...newImageUrls);
            displayImages(newImageUrls);
            currentPage++;

        } catch (e) {
            console.error("Error:", e);
            showError(e.message);
        } finally {
            isLoading = false;
            submitButton.disabled = false;
            if (!isNewSearch) {
                const loadMoreButton = document.getElementById('load-more-button');
                if (loadMoreButton) loadMoreButton.innerHTML = 'Load More';
            }
        }
    }

    function displayImages(imageUrls) {
        let grid = document.getElementById('image-results-grid');
        if (!grid) {
            grid = document.createElement('div');
            grid.id = 'image-results-grid';
            outputArea.appendChild(grid);
        }

        imageUrls.forEach(url => {
            const startIndex = allImageUrls.length - imageUrls.length;
            const link = document.createElement('a');
            link.href = url;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            link.className = 'image-result';
            link.style.animationDelay = `${(grid.children.length % 20) * 50}ms`;
            link.dataset.index = startIndex + grid.children.length;

            link.addEventListener('click', e => {
                e.preventDefault();
                openLightbox(parseInt(link.dataset.index));
            });

            const img = document.createElement('img');
            img.src = url;
            img.alt = `${currentQuery} result`;
            img.loading = 'lazy';

            const overlay = document.createElement('div');
            overlay.className = 'image-overlay';
            overlay.innerHTML = `<button class="copy-url-btn" title="Copy URL"><i class="fa-solid fa-copy"></i></button>`;
            overlay.querySelector('.copy-url-btn').addEventListener('click', e => {
                e.stopPropagation();
                e.preventDefault();
                copyUrlToClipboard(url, e.currentTarget);
            });

            link.appendChild(img);
            link.appendChild(overlay);
            grid.appendChild(link);
        });

        let loadMoreButton = document.getElementById('load-more-button');
        if (!loadMoreButton && !noMoreResults) {
            loadMoreButton = document.createElement('button');
            loadMoreButton.id = 'load-more-button';
            loadMoreButton.className = 'interactive-border';
            loadMoreButton.textContent = 'Load More';
            loadMoreButton.onclick = () => fetchAndDisplayImages(false);
            outputArea.appendChild(loadMoreButton);
            addInteractiveBorderListeners(loadMoreButton);
        }
    }

    function copyUrlToClipboard(url, button) {
        navigator.clipboard.writeText(url).then(() => {
            button.innerHTML = '<i class="fa-solid fa-check"></i>';
            setTimeout(() => {
                button.innerHTML = '<i class="fa-solid fa-copy"></i>';
            }, 1500);
        });
    }

    function updateProgress(percentage, status) {
        progressBar.style.width = `${percentage}%`;
        progressStatus.textContent = status;
    }

    function showError(message) {
        outputArea.innerHTML = `<div class="error-box">${message}</div>`;
    }

    function getSearchHistory() {
        return JSON.parse(getPreference('search_history') || '[]');
    }

    function updateSearchHistory(query) {
        let history = getSearchHistory();
        history = history.filter(item => item.toLowerCase() !== query.toLowerCase());
        history.unshift(query);
        if (history.length > 5) history.pop();
        savePreference('search_history', JSON.stringify(history));
    }

    function showSuggestions(query) {
        if (!query) {
            suggestionsBox.classList.remove('visible');
            return;
        }
        const history = getSearchHistory();
        const filtered = history.filter(item => item.toLowerCase().includes(query.toLowerCase()));

        if (filtered.length > 0) {
            suggestionsBox.innerHTML = filtered.map(item => `<div>${item}</div>`).join('');
            suggestionsBox.classList.add('visible');
        } else {
            suggestionsBox.classList.remove('visible');
        }
    }

    queryInput.addEventListener('input', () => showSuggestions(queryInput.value));
    queryInput.addEventListener('focus', () => showSuggestions(queryInput.value));
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.search-input-wrapper')) {
            suggestionsBox.classList.remove('visible');
        }
    });

    suggestionsBox.addEventListener('click', (e) => {
        if (e.target.tagName === 'DIV') {
            queryInput.value = e.target.textContent;
            suggestionsBox.classList.remove('visible');
            startSearch(new Event('submit'));
        }
    });

    function openLightbox(index) {
        currentLightboxIndex = index;
        lightboxImage.src = allImageUrls[index];
        lightbox.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }

    function closeLightbox() {
        lightbox.classList.add('hidden');
        document.body.style.overflow = '';
    }

    function changeLightboxImage(direction) {
        currentLightboxIndex += direction;
        if (currentLightboxIndex < 0) currentLightboxIndex = allImageUrls.length - 1;
        if (currentLightboxIndex >= allImageUrls.length) currentLightboxIndex = 0;
        lightboxImage.src = allImageUrls[currentLightboxIndex];
    }

    lightbox.querySelector('.lightbox-close').addEventListener('click', closeLightbox);
    lightbox.querySelector('.lightbox-prev').addEventListener('click', () => changeLightboxImage(-1));
    lightbox.querySelector('.lightbox-next').addEventListener('click', () => changeLightboxImage(1));
    lightbox.addEventListener('click', (e) => {
        if (e.target === lightbox) closeLightbox();
    });

    document.addEventListener('keydown', (e) => {
        if (lightbox.classList.contains('hidden')) return;
        if (e.key === 'Escape') closeLightbox();
        if (e.key === 'ArrowLeft') changeLightboxImage(-1);
        if (e.key === 'ArrowRight') changeLightboxImage(1);
    });

    applySavedPreferences();
});