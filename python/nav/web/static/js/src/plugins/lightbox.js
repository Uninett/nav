define(["libs/jquery"], function () {

    let currentLightbox = null;
    let currentIndex = 0;
    let currentImages = [];

    function init() {
        // Use event delegation to handle all lightbox triggers and controls
        document.addEventListener('click', handleClick);
        document.addEventListener('keydown', handleKeydown);
        return { openGallery, close: closeLightbox };
    }

    function handleClick(event) {
        const trigger = event.target.closest('[data-lightbox]');
        if (trigger) {
            event.preventDefault();
            openGallery(trigger.dataset.lightbox, trigger.href);
            return;
        }

        if (!currentLightbox) return;

        // Handle all lightbox controls through event delegation
        if (event.target.matches('.lightbox-close') || event.target === currentLightbox) {
            closeLightbox();
        } else if (event.target.closest('.lightbox-prev')) {
            navigate(-1);
        } else if (event.target.closest('.lightbox-next')) {
            navigate(1);
        } else {
            const thumbnail = event.target.closest('.lightbox-thumbnail-list li');
            if (thumbnail) {
                // Convert NodeList to array to use indexOf
                const index = [...thumbnail.parentNode.children].indexOf(thumbnail);
                showImage(index);
            }
        }
    }

    function handleKeydown(event) {
        if (!currentLightbox?.classList.contains('show')) return;

        const keyMap = {
            'Escape': closeLightbox,
            'ArrowRight': () => navigate(1),
            'ArrowLeft': () => navigate(-1)
        };

        keyMap[event.key]?.();
    }

    function openGallery(galleryId, selectedSrc = null) {
        currentLightbox = document.getElementById(`lightbox-${galleryId}`);
        if (!currentLightbox) return;

        // Build image collection from all triggers with the same gallery ID
        currentImages = [...document.querySelectorAll(`[data-lightbox="${galleryId}"]`)].map(trigger => ({
            src: trigger.href,
            thumbUrl: trigger.querySelector('img')?.src || trigger.href,
            caption: trigger.dataset.title || trigger.title || ''
        }));

        // Find the selected image index, defaulting to 0 if not found
        currentIndex = Math.max(0, currentImages.findIndex(img => img.src === selectedSrc));
        showLightbox();
    }

    function showLightbox() {
        currentLightbox.classList.add('show');
        currentLightbox.style.display = 'block';
        document.body.style.overflow = 'hidden'; // Prevent body scrolling

        generateThumbnails();
        showImage(currentIndex);
    }

    function closeLightbox() {
        if (!currentLightbox) return;

        currentLightbox.classList.remove('show');
        // Delay hiding to allow CSS transitions to complete
        setTimeout(() => {
            currentLightbox.style.display = 'none';
            document.body.style.overflow = '';
            currentLightbox = null;
        }, 300);
    }

    function generateThumbnails() {
        const thumbnailList = currentLightbox.querySelector('.lightbox-thumbnail-list');
        if (!thumbnailList) return;

        // Generate thumbnails using template literals for better performance
        thumbnailList.innerHTML = currentImages.map((image, index) =>
            `<li><img src="${image.thumbUrl}" alt="${image.caption}" loading="lazy"></li>`
        ).join('');
    }

    function showImage(index) {
        if (index < 0 || index >= currentImages.length) return;

        currentIndex = index;
        const image = currentImages[index];

        const img = currentLightbox.querySelector('.lightbox-image');
        const caption = currentLightbox.querySelector('.lightbox-caption');

        if (img) {
            img.src = image.src;
            img.alt = image.caption;
        }
        if (caption) caption.textContent = image.caption;

        // Update thumbnail selection state
        currentLightbox.querySelectorAll('.lightbox-thumbnail-list li').forEach((thumb, i) => {
            thumb.classList.toggle('active', i === index);
        });
    }

    function navigate(direction) {
        if (currentImages.length <= 1) return;

        // Use modulo arithmetic for circular navigation
        const newIndex = (currentIndex + direction + currentImages.length) % currentImages.length;
        showImage(newIndex);
    }

    // Initialize when DOM is ready
    $(() => {
        const api = init();
        window.openLightboxGallery = api.openGallery;
    });

    return { init };
});
