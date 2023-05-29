const nav = document.getElementById("gnb");
const layer = document.getElementById("layer");
const btnShowMenu = document.getElementById("btn-menu");
const btnHideMenu = document.getElementById("btn-close_menu");

function openMenu() { // 메뉴 버튼을 클릭하면 메뉴가 열리는 함수
    nav.classList.add("active");
    layer.classList.add("active");
}
function closeMenu() { // 메뉴 버튼을 클릭하면 메뉴가 닫히는 함수
    nav.classList.remove("active");
    layer.classList.remove("active");
}

(() => { // 클릭을 하면 메뉴가 열리고 닫히는 화살표 함수
    btnShowMenu.addEventListener("click", openMenu);
    btnHideMenu.addEventListener("click", closeMenu);
    layer.addEventListener("click", closeMenu);
})();