document.addEventListener("DOMContentLoaded", () => {
  const filterButtons = [...document.querySelectorAll("[data-filter]")];
  const sourceCards = [...document.querySelectorAll("[data-source-card]")];

  filterButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const filter = button.dataset.filter;
      filterButtons.forEach((item) => item.classList.toggle("active", item === button));
      sourceCards.forEach((card) => {
        const show = filter === "all" || card.dataset.category === filter || card.dataset.state === filter;
        card.hidden = !show;
      });
    });
  });

  const search = document.querySelector("[data-comment-search]");
  const comments = [...document.querySelectorAll("[data-comment]")];
  const count = document.querySelector("[data-comment-count]");
  if (search && count) {
    search.addEventListener("input", () => {
      const query = search.value.trim().toLocaleLowerCase("sv");
      let visible = 0;
      comments.forEach((comment) => {
        const show = !query || comment.dataset.search.includes(query);
        comment.hidden = !show;
        if (show) visible += 1;
      });
      count.textContent = `${visible} ${visible === 1 ? "entry" : "entries"} shown`;
    });
  }
});
