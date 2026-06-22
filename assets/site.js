(function () {
  var downloadUrl = "https://sso.zhangyumofang.com/zydh_v1.3.10_x64.exe";
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

  var redirect = document.querySelector("[data-download-redirect]");
  if (redirect) {
    var counter = document.querySelector("[data-countdown]");
    var seconds = 3;
    var tick = function () {
      if (counter) counter.textContent = String(seconds);
      if (seconds === 0) {
        window.location.href = downloadUrl;
        return;
      }
      seconds -= 1;
      window.setTimeout(tick, 1000);
    };
    tick();
  }

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

    var getFullSrc = function (src) {
      return src.replace("-thumb.webp", ".png").replace(".webp", ".png");
    };

    var closeLightbox = function () {
      lightbox.classList.remove("is-open");
      fullImage.removeAttribute("src");
      document.body.style.overflow = "";
    };

    galleryImages.forEach(function (image) {
      image.setAttribute("tabindex", "0");
      image.setAttribute("title", "点击查看高清截图");

      var openLightbox = function () {
        var fullSrc = getFullSrc(image.getAttribute("src"));
        var alt = image.getAttribute("alt") || "章鱼带货软件截图";
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
})();
