(function () {
  var currentPath = window.location.pathname.split("/").pop() || "index.html";
  if (window.location.pathname.indexOf("/articles/") !== -1) {
    currentPath = "articles.html";
  }
  if (window.location.pathname.indexOf("/features/") !== -1) {
    currentPath = "features.html";
  }

  document.querySelectorAll(".nav-links a").forEach(function (link) {
    var href = (link.getAttribute("href") || "").split("#")[0];
    var target = href.split("/").pop() || "index.html";
    if (target === currentPath) {
      link.classList.add("is-current");
      link.setAttribute("aria-current", "page");
    }
  });

  var nav = document.querySelector(".nav");
  var navLinks = document.querySelector(".nav-links");
  if (nav && navLinks) {
    navLinks.id = navLinks.id || "primary-nav";

    var toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "nav-toggle";
    toggle.setAttribute("aria-controls", navLinks.id);
    toggle.setAttribute("aria-expanded", "false");
    toggle.setAttribute("aria-label", "打开导航菜单");
    toggle.innerHTML = '<span class="nav-toggle__bars" aria-hidden="true"></span><span class="nav-toggle__text">菜单</span>';
    nav.insertBefore(toggle, navLinks);

    var setNav = function (open) {
      nav.classList.toggle("is-open", open);
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      toggle.setAttribute("aria-label", open ? "关闭导航菜单" : "打开导航菜单");
    };

    toggle.addEventListener("click", function () {
      setNav(!nav.classList.contains("is-open"));
    });

    navLinks.addEventListener("click", function (event) {
      if (event.target.closest("a")) setNav(false);
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && nav.classList.contains("is-open")) {
        setNav(false);
        toggle.focus();
      }
    });

    document.addEventListener("click", function (event) {
      if (nav.classList.contains("is-open") && !nav.contains(event.target)) setNav(false);
    });

    var wide = window.matchMedia("(min-width: 981px)");
    var syncWide = function () {
      if (wide.matches) setNav(false);
    };
    if (wide.addEventListener) wide.addEventListener("change", syncWide);
    else if (wide.addListener) wide.addListener(syncWide);
  }

  var links = document.querySelectorAll("[data-download]");

  links.forEach(function (link) {
    link.addEventListener("click", function () {
      try {
        localStorage.setItem("zydh_last_download_click", new Date().toISOString());
      } catch (error) {
        return;
      }
    });
  });

  var updatesPanel = document.querySelector("[data-updates]");
  if (updatesPanel && window.fetch) {
    fetch("updates.json", { cache: "no-store" })
      .then(function (response) {
        if (!response.ok) throw new Error("updates unavailable");
        return response.json();
      })
      .then(function (items) {
        if (!Array.isArray(items) || !items.length) return;
        var html = items.slice(0, 4).map(function (item) {
          var date = item.date || "";
          var title = item.title || "产品更新";
          var summary = item.summary || "";
          var url = item.url || "changelog.html";
          return [
            '<article class="update-item">',
            '  <time datetime="' + date + '">' + date + "</time>",
            "  <div>",
            '    <h3><a href="' + url + '">' + title + "</a></h3>",
            "    <p>" + summary + "</p>",
            "  </div>",
            "</article>"
          ].join("");
        }).join("");
        updatesPanel.innerHTML = html + '<a class="btn" href="changelog.html">查看完整更新日志</a>';
      })
      .catch(function () {
        return;
      });
  }

  var galleryImages = document.querySelectorAll(".feature-card img");
  if (galleryImages.length) {
    var lightbox = document.createElement("div");
    lightbox.className = "image-lightbox";
    lightbox.setAttribute("role", "dialog");
    lightbox.setAttribute("aria-modal", "true");
    lightbox.setAttribute("aria-label", "高清截图预览");
    lightbox.innerHTML = [
      '<div class="image-lightbox__panel">',
      '  <div class="image-lightbox__bar">',
      '    <div class="image-lightbox__title"></div>',
      '    <div class="image-lightbox__actions">',
      '      <a href="#" target="_blank" rel="noopener">新窗口打开原图</a>',
      '      <button type="button">关闭</button>',
      "    </div>",
      "  </div>",
      '  <div class="image-lightbox__frame"><img alt=""></div>',
      "</div>"
    ].join("");
    document.body.appendChild(lightbox);

    var fullImage = lightbox.querySelector(".image-lightbox__frame img");
    var title = lightbox.querySelector(".image-lightbox__title");
    var openLink = lightbox.querySelector(".image-lightbox__actions a");
    var closeButton = lightbox.querySelector(".image-lightbox__actions button");
    var lastFocusedElement = null;

    // 高清图用同名 full-size webp（1800×925，约 60-95KB），
    // 不再回落到 3378×1736 的 png（约 200-900KB），省约 88% 体积。
    var getFullSrc = function (src) {
      if (!src) return "";
      return src.replace("-thumb.webp", ".webp");
    };

    var closeLightbox = function () {
      lightbox.classList.remove("is-open");
      fullImage.removeAttribute("src");
      document.body.style.overflow = "";
      if (lastFocusedElement && typeof lastFocusedElement.focus === "function") {
        lastFocusedElement.focus();
      }
    };

    galleryImages.forEach(function (image) {
      image.setAttribute("tabindex", "0");
      image.setAttribute("title", "点击查看高清截图");

      var openLightbox = function () {
        var fullSrc = getFullSrc(image.getAttribute("src"));
        if (!fullSrc) return;
        var alt = image.getAttribute("alt") || "章鱼带货软件截图";
        lastFocusedElement = image;
        fullImage.setAttribute("src", fullSrc);
        fullImage.setAttribute("alt", alt);
        title.textContent = alt;
        openLink.setAttribute("href", fullSrc);
        lightbox.classList.add("is-open");
        document.body.style.overflow = "hidden";
        closeButton.focus();
      };

      image.addEventListener("click", openLightbox);
      image.addEventListener("keydown", function (event) {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          openLightbox();
        }
      });
    });

    closeButton.addEventListener("click", closeLightbox);
    fullImage.addEventListener("click", closeLightbox);
    lightbox.addEventListener("click", function (event) {
      if (event.target === lightbox) closeLightbox();
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && lightbox.classList.contains("is-open")) {
        closeLightbox();
      }
    });
  }

  // 滚动显现：与 02-neo-brutal 变体同一套逻辑。
  // 安全网：观察器没触发时（无头截图、打印、异常滚动容器）2.6s 后强制可见，
  // 绝不把内容留在隐藏态。prefers-reduced-motion 直接全部可见。
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var revealTargets = document.querySelectorAll("[data-reveal]");
  var revealAll = function () {
    revealTargets.forEach(function (el) { el.classList.add("is-in"); });
  };
  window.addEventListener("beforeprint", revealAll);
  setTimeout(revealAll, 2600);
  if (!reduceMotion && "IntersectionObserver" in window && revealTargets.length) {
    var revealObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-in");
          revealObserver.unobserve(entry.target);
        }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.06 });
    revealTargets.forEach(function (el) {
      el.classList.add("zy-reveal");
      revealObserver.observe(el);
    });
  } else {
    revealTargets.forEach(function (el) { el.classList.add("is-in"); });
  }
})();

/* 百度统计（tongji.baidu.com）——站内全站统一在此加载，勿删 */
window._hmt = window._hmt || [];
(function () {
  var hm = document.createElement("script");
  hm.async = true;
  hm.src = "https://hm.baidu.com/hm.js?9c1c05454db4ac75ae3b9813a896e7cf";
  var s = document.getElementsByTagName("script")[0];
  s.parentNode.insertBefore(hm, s);
})();
