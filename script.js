const menuItems = document.querySelectorAll('.menu-item');
const panels = document.querySelectorAll('.panel');

menuItems.forEach((item) => {
  item.addEventListener('click', () => {
    menuItems.forEach((it) => it.classList.remove('active'));
    panels.forEach((panel) => panel.classList.remove('active'));

    item.classList.add('active');
    const target = document.getElementById(item.dataset.section);
    if (target) {
      target.classList.add('active');
    }
  });
});
