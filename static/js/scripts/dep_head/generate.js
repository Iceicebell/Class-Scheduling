window.addEventListener("load", () => {
    console.log("Window loaded");
    const loader = document.querySelector(".loader");
    console.log("Loader found:", loader);
    
    if (loader) {
        console.log("Adding loader-hidden class");
        loader.classList.add("loader-hidden");
        loader.addEventListener("transitionend", () => {
            console.log("Transition ended, removing loader");
            document.body.removeChild(loader);
        }, { once: true });
    } else {
        console.log("Loader not found in the DOM");
    }
});