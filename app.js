const sideBar = document.querySelector('.sidebar');
const menu = document.querySelector('.menu-icon');
const close = document.querySelector('.close-icon');


menu.addEventListener('click', function() {
    sideBar.classList.remove('close-sidebar');
    sideBar.classList.toggle('open-sidebar');
})

close.addEventListener('click', function() {
    sideBar.classList.remove('open-sidebar');
    sideBar.classList.add('close-sidebar');
})