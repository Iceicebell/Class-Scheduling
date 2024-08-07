const menuButton = document.querySelectorAll(".menu-button");
const screenOverlay = document.querySelector(".screen-overlay");
const tabs = document.querySelectorAll('.tab_btn');
const all_content = document.querySelectorAll('.content');
const showAdd = document.querySelector("#show-add");
const closeAdd = document.querySelector(".popup .close-btn");


menuButton.forEach(button =>{
    button.addEventListener("click",()=>{
        document.body.classList.toggle("sidebar-hidden");
    });
});

screenOverlay.addEventListener("click", ()=>{
    document.body.classList.toggle("sidebar-hidden");
});


tabs.forEach((tab,index) => {
    tab.addEventListener('click',(e)=>{
        tabs.forEach(tab=>{tab.classList.remove('active')});
        tab.classList.add('active');

        var line = document.querySelector('.line');
        line.style.width = e.target.offsetWidth + 'px';
        line.style.left = e.target.offsetLeft + 'px';

        all_content.forEach(content=>{content.classList.remove('active')});
        all_content[index].classList.add('active');
    })


})

// =====================POP UP==================

showAdd.addEventListener("click", function(){
    document.querySelector(".popup").classList.add("active");
});

closeAdd.addEventListener("click", function(){
    document.querySelector(".popup").classList.remove("active");
});

// ===================OPTIONS================
