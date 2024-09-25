window.addEventListener("load", () => {
    console.log("Window loaded");
    const loader = document.querySelector(".loader");
    console.log("Loader found:", loader);
    
    if (!loader) {
        console.log("Loader not found in the DOM");
        return;
    }

    document.getElementById('generateForm').addEventListener('submit', function() {
        loader.style.display = 'flex';
        loader.classList.remove("loader-hidden");
    });

    // Listen for flash messages
    const flashMessage = document.querySelector('.flash-message');
    if (flashMessage && flashMessage.textContent.includes('Algorithm completed successfully')) {
        setTimeout(() => {
            window.location.reload();
        }, 500); // Adjust the delay as needed
    }
});