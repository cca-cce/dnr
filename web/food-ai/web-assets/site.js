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

  // Players with a transcript (SVT interviews, audio overview): optional language switch for subtitles and
  // transcript, click-to-seek, follow playback, search.
  document.querySelectorAll("[data-clip]").forEach((clip) => {
    const video = clip.querySelector("video, audio");
    const box = clip.querySelector(".cue-box");
    const query = clip.querySelector("[data-cue-search]");
    const tab = clip.querySelector("[data-lang].active");
    let lang = tab ? tab.dataset.lang : clip.querySelector("[data-cues]").dataset.cues;
    const list = () => clip.querySelector(`[data-cues="${lang}"]`);

    const filter = () => {
      const q = query.value.trim().toLocaleLowerCase();
      list().querySelectorAll("li").forEach((li) => { li.hidden = q && !li.textContent.toLocaleLowerCase().includes(q); });
    };
    const follow = () => {
      const t = video.currentTime;
      let now = null;
      list().querySelectorAll("button").forEach((b) => {
        const on = t >= +b.dataset.start && t < +b.dataset.end;
        b.classList.toggle("now", on);
        if (on) now = b;
      });
      // scroll only the transcript box; scrollIntoView would also scroll the page
      if (now && !video.paused) box.scrollTo({ top: now.offsetTop - box.clientHeight / 2, behavior: "smooth" });
    };
    const setLang = (next) => {
      lang = next;
      clip.querySelectorAll("[data-lang]").forEach((tab) => tab.classList.toggle("active", tab.dataset.lang === lang));
      clip.querySelectorAll("[data-cues]").forEach((ol) => { ol.hidden = ol.dataset.cues !== lang; });
      [...video.textTracks].forEach((track) => { track.mode = track.language === lang ? "showing" : "disabled"; });
      filter(); follow();
    };

    clip.querySelectorAll("[data-lang]").forEach((tab) => tab.addEventListener("click", () => setLang(tab.dataset.lang)));
    clip.querySelectorAll("[data-start]").forEach((b) => b.addEventListener("click", () => {
      video.currentTime = +b.dataset.start + 0.01; video.play();
    }));
    query.addEventListener("input", filter);
    video.addEventListener("timeupdate", follow);
  });
});
