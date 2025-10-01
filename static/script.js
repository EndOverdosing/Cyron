document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.getElementById('search-form');
    const queryInput = document.getElementById('query-input');
    const clearSearchBtn = document.getElementById('clear-search-btn');
    const imageSizeSelect = document.getElementById('image-size-select');
    const timeRangeSelect = document.getElementById('time-range-select');
    const safeSearchToggle = document.getElementById('safe-search-toggle');
    const proxyModeToggle = document.getElementById('proxy-mode-toggle');
    const submitButton = document.getElementById('submit-button');
    const outputArea = document.getElementById('output-area');
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar');
    const progressStatus = document.getElementById('progress-status');
    const themeSwitcher = document.getElementById('theme-switcher');
    const infiniteScrollLoader = document.getElementById('infinite-scroll-loader');
    const lightbox = document.getElementById('lightbox');
    const lightboxImage = lightbox.querySelector('.lightbox-image');
    const lightboxTitle = lightbox.querySelector('.lightbox-title');
    const lightboxSourceLink = lightbox.querySelector('.lightbox-source-link');

    let currentQuery = '';
    let currentPage = 1;
    let isLoading = false;
    let noMoreResults = false;
    let allImageResults = [];
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

        const savedProxyMode = getPreference('proxy_mode');
        if (savedProxyMode === 'true') proxyModeToggle.checked = true;
    }

    themeSwitcher.addEventListener('click', () => {
        document.body.classList.toggle('light-theme');
        const newTheme = document.body.classList.contains('light-theme') ? 'light' : 'dark';
        savePreference('theme', newTheme);
    });

    imageSizeSelect.addEventListener('change', () => savePreference('image_size', imageSizeSelect.value));
    timeRangeSelect.addEventListener('change', () => savePreference('time_range', timeRangeSelect.value));
    safeSearchToggle.addEventListener('change', () => savePreference('safe_search', safeSearchToggle.checked));
    proxyModeToggle.addEventListener('change', () => savePreference('proxy_mode', proxyModeToggle.checked));

    queryInput.addEventListener('input', () => {
        clearSearchBtn.classList.toggle('hidden', !queryInput.value);
    });

    clearSearchBtn.addEventListener('click', (event) => {
        event.preventDefault();
        queryInput.value = '';
        queryInput.focus();
        clearSearchBtn.classList.add('hidden');
    });

    queryInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            searchForm.requestSubmit();
        }
    });

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

    function startSearch(query) {
        document.body.classList.add('search-active');
        currentQuery = query;
        currentPage = 1;
        allImageResults = [];
        noMoreResults = false;
        outputArea.innerHTML = '';
        progressContainer.classList.remove('hidden');
        updateProgress(10, "Initializing search...");

        const url = new URL(window.location);
        url.pathname = '/search';
        url.searchParams.set('query', query);
        window.history.pushState({ query }, '', url);

        fetchAndDisplayImages(true).finally(() => {
            setTimeout(() => progressContainer.classList.add('hidden'), 500);
        });
    }

    searchForm.addEventListener('submit', (event) => {
        event.preventDefault();
        const query = queryInput.value.trim();
        if (query.length === 0) {
            showError("Please enter a search query.");
            return;
        }
        startSearch(query);
    });

    async function fetchAndDisplayImages(isNewSearch = false) {
        if (isLoading || noMoreResults) return;

        isLoading = true;
        submitButton.disabled = true;
        if (!isNewSearch) infiniteScrollLoader.classList.remove('hidden');

        try {
            if (isNewSearch) updateProgress(30, "Finding images...");

            const response = await fetch('/search_api', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: currentQuery,
                    safe_search: safeSearchToggle.checked,
                    proxy_mode: proxyModeToggle.checked,
                    size: imageSizeSelect.value,
                    time_range: timeRangeSelect.value,
                    page: currentPage
                })
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                noMoreResults = true;
                if (isNewSearch) showError(data.error || "No images found.");
                return;
            }

            if (!data.images || data.images.length === 0) {
                noMoreResults = true;
                if (isNewSearch) showError("No more images found for this query.");
                return;
            }

            if (isNewSearch) updateProgress(100, "Displaying results...");

            const newImageResults = data.images.filter(img => !allImageResults.some(existing => existing.img_src === img.img_src));
            allImageResults.push(...newImageResults);
            displayImages(newImageResults);
            currentPage++;

        } catch (e) {
            console.error("Error:", e);
            if (isNewSearch) showError("A network error occurred. Please try again.");
        } finally {
            isLoading = false;
            submitButton.disabled = false;
            infiniteScrollLoader.classList.add('hidden');
        }
    }

    function displayImages(imageResults) {
        let grid = document.getElementById('image-results-grid');
        if (!grid) {
            grid = document.createElement('div');
            grid.id = 'image-results-grid';
            outputArea.appendChild(grid);
        }

        imageResults.forEach(result => {
            const resultIndex = allImageResults.findIndex(item => item.img_src === result.img_src);

            const link = document.createElement('a');
            link.href = result.display_src;
            link.className = 'image-result';
            link.style.animationDelay = `${(grid.children.length % 20) * 50}ms`;
            link.dataset.index = resultIndex;

            link.addEventListener('click', e => {
                e.preventDefault();
                openLightbox(parseInt(link.dataset.index));
            });

            const img = document.createElement('img');
            img.src = result.display_src;
            img.alt = result.title;
            img.loading = 'lazy';

            img.onerror = function () {
                if (this.src === result.display_src && result.display_src !== result.img_src) {
                    result.display_src = result.img_src;
                    this.src = result.img_src;
                } else {
                    link.remove();
                }
            };

            const overlay = document.createElement('div');
            overlay.className = 'image-overlay';
            overlay.innerHTML = `
                <div class="image-info">
                    <p class="image-title">${result.title}</p>
                    <div class="image-actions">
                         <a href="${result.display_src}" target="_blank" rel="noopener noreferrer" class="source-link" onclick="event.stopPropagation()">View Image</a>
                         <button class="copy-url-btn" title="Copy Original URL"><i class="fa-solid fa-copy"></i></button>
                    </div>
                </div>`;

            overlay.querySelector('.copy-url-btn').addEventListener('click', e => {
                e.stopPropagation();
                e.preventDefault();
                copyUrlToClipboard(result.img_src, e.currentTarget);
            });

            link.appendChild(img);
            link.appendChild(overlay);
            grid.appendChild(link);
        });
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
        progressContainer.classList.add('hidden');
        outputArea.innerHTML = `<div class="error-box">${message}</div>`;
    }

    function openLightbox(index) {
        currentLightboxIndex = index;
        const result = allImageResults[index];
        lightboxImage.src = result.display_src;
        lightboxTitle.textContent = result.title;
        lightboxSourceLink.href = result.display_src;
        lightboxSourceLink.textContent = 'View Full Image';
        lightbox.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }

    function closeLightbox() {
        lightbox.classList.add('hidden');
        lightboxImage.src = "";
        lightboxSourceLink.textContent = 'Source';
        document.body.style.overflow = '';
    }

    function changeLightboxImage(direction) {
        currentLightboxIndex += direction;
        if (currentLightboxIndex < 0) currentLightboxIndex = allImageResults.length - 1;
        if (currentLightboxIndex >= allImageResults.length) currentLightboxIndex = 0;

        const result = allImageResults[currentLightboxIndex];
        lightboxImage.src = result.display_src;
        lightboxTitle.textContent = result.title;
        lightboxSourceLink.href = result.display_src;
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

    window.addEventListener('scroll', () => {
        if (isLoading || noMoreResults || !document.body.classList.contains('search-active')) return;
        if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 500) {
            fetchAndDisplayImages(false);
        }
    });

    applySavedPreferences();

    const urlParams = new URLSearchParams(window.location.search);
    const queryFromUrl = urlParams.get('query');
    if (queryFromUrl) {
        queryInput.value = decodeURIComponent(queryFromUrl);
        startSearch(queryFromUrl);
    }
});