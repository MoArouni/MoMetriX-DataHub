const hamburger = document.getElementById('hamburger');
const rightMenu = document.getElementById('right-menu');
const body = document.body;

hamburger.addEventListener('click', () => {
    hamburger.classList.toggle('open');
    rightMenu.classList.toggle('open');
    body.classList.toggle('menu-open');
});



