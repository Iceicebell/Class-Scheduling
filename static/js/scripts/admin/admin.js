const menuButton = document.querySelectorAll(".menu-button");
const screenOverlay = document.querySelector(".screen-overlay");
const optionMenu = document.querySelector(".select-menu"),
    selectBtn = document.querySelector(".select-btn"),
    options = document.querySelectorAll(".option"),
    sBtn_text = document.querySelector(".sBtn-text ");
const showEdit = document.querySelector("#show-edit");
const closeEdit = document.querySelector(".popup .close-btn");


menuButton.forEach(button =>{
    button.addEventListener("click",()=>{
        document.body.classList.toggle("sidebar-hidden");
    });
});

screenOverlay.addEventListener("click", ()=>{
    document.body.classList.toggle("sidebar-hidden");
});

selectBtn.addEventListener("click", () => optionMenu.classList.toggle("active"));

options.forEach(option =>{
    option.addEventListener("click", ()=>{
        let selectedOption = option.querySelector(".option-text").innerText;
        sBtn_text.innerText = selectedOption;
        

        optionMenu.classList.remove("active")
    })
})

showEdit.addEventListener("click", function(){
    document.querySelector(".popup").classList.add("active");
});

closeEdit.addEventListener("click", function(){
    document.querySelector(".popup").classList.remove("active");
});