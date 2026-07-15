document.addEventListener("DOMContentLoaded", function () {
  console.log("Flood Prediction System Loaded Successfully");

  initTheme();
  initRain();
  initLightning();
  initGauge();
});

/* =========================================================
   Light / dark theme toggle
   ========================================================= */
function initTheme() {
  var root = document.documentElement;
  var toggle = document.getElementById("theme-toggle");
  var stored = localStorage.getItem("flood-theme");
  var preferred = stored || (window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");

  applyTheme(preferred);

  if (!toggle) return;

  toggle.addEventListener("click", function () {
    var current = root.getAttribute("data-theme") === "light" ? "light" : "dark";
    var next = current === "light" ? "dark" : "light";
    applyTheme(next);
    localStorage.setItem("flood-theme", next);
  });

  function applyTheme(theme) {
    root.setAttribute("data-theme", theme);
    var icon = toggle ? toggle.querySelector(".theme-toggle-icon") : null;
    if (icon) icon.textContent = theme === "light" ? "☀️" : "🌙";
  }
}

/* =========================================================
   Ambient rain canvas
   Intensity can be tuned per-page via body[data-rain="heavy|normal|light"]

   Also drives two optional extra weather effects on the same canvas:
     - Wind streaks:  body[data-wind="off"] to disable (on by default)
     - Rain ripples:  body[data-ripples="off"] to disable (on by default)
   ========================================================= */
function initRain() {
  var canvas = document.getElementById("rain-canvas");
  if (!canvas) return;

  var ctx = canvas.getContext("2d");
  var intensity = document.body.getAttribute("data-rain") || "normal";
  var countMap = { light: 60, normal: 120, heavy: 220 };
  var speedMap = { light: 4, normal: 7, heavy: 11 };
  var dropCount = countMap[intensity] || 120;
  var baseSpeed = speedMap[intensity] || 7;

  var windEnabled = document.body.getAttribute("data-wind") !== "off";
  var ripplesEnabled = document.body.getAttribute("data-ripples") !== "off";

  var width, height, drops, windLines, ripples, rippleTimer;

  function resize() {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  }

  function makeDrop() {
    return {
      x: Math.random() * width,
      y: Math.random() * height,
      len: 10 + Math.random() * 18,
      speed: baseSpeed + Math.random() * 6,
      drift: 1.2 + Math.random() * 0.8,
      opacity: 0.12 + Math.random() * 0.25
    };
  }

  function makeWindLine() {
    return {
      x: Math.random() * width,
      y: Math.random() * height * 0.6, // upper/mid section, above the "ground"
      len: 60 + Math.random() * 130,
      speed: 2 + Math.random() * 4,
      opacity: 0.05 + Math.random() * 0.10
    };
  }

  function spawnRipple() {
    if (!ripplesEnabled) return;
    ripples.push({
      x: Math.random() * width,
      y: height * (0.72 + Math.random() * 0.24), // near the bottom, like ground/water
      radius: 1,
      maxRadius: 12 + Math.random() * 16,
      opacity: 0.3
    });
  }

  function init() {
    resize();
    drops = [];
    for (var i = 0; i < dropCount; i++) drops.push(makeDrop());

    windLines = [];
    if (windEnabled) {
      for (var w = 0; w < 16; w++) windLines.push(makeWindLine());
    }

    ripples = [];
    if (ripplesEnabled) {
      clearInterval(rippleTimer);
      rippleTimer = setInterval(spawnRipple, 280);
    }
  }

  function drawRain() {
    ctx.strokeStyle = "rgba(180, 210, 230, 1)";
    ctx.lineCap = "round";

    for (var i = 0; i < drops.length; i++) {
      var d = drops[i];
      ctx.globalAlpha = d.opacity;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(d.x, d.y);
      ctx.lineTo(d.x - d.drift * 2, d.y + d.len);
      ctx.stroke();

      d.x -= d.drift;
      d.y += d.speed;

      if (d.y > height || d.x < 0) {
        d.x = Math.random() * width;
        d.y = -20;
      }
    }
    ctx.globalAlpha = 1;
  }

  function drawWind() {
    if (!windEnabled) return;
    ctx.strokeStyle = "rgba(180, 210, 230, 1)";
    ctx.lineWidth = 1;

    for (var i = 0; i < windLines.length; i++) {
      var w = windLines[i];
      ctx.globalAlpha = w.opacity;
      ctx.beginPath();
      ctx.moveTo(w.x, w.y);
      ctx.lineTo(w.x - w.len, w.y + w.len * 0.06);
      ctx.stroke();

      w.x += w.speed;
      w.y += w.speed * 0.04;

      if (w.x - w.len > width) {
        w.x = -w.len;
        w.y = Math.random() * height * 0.6;
      }
    }
    ctx.globalAlpha = 1;
  }

  function drawRipples() {
    if (!ripplesEnabled) return;
    ctx.lineWidth = 1.1;

    for (var i = ripples.length - 1; i >= 0; i--) {
      var r = ripples[i];
      ctx.globalAlpha = r.opacity;
      ctx.strokeStyle = "rgba(150, 200, 220, 1)";
      ctx.beginPath();
      ctx.ellipse(r.x, r.y, r.radius, r.radius * 0.35, 0, 0, Math.PI * 2);
      ctx.stroke();

      r.radius += 0.6;
      r.opacity -= 0.01;

      if (r.radius >= r.maxRadius || r.opacity <= 0) {
        ripples.splice(i, 1);
      }
    }
    ctx.globalAlpha = 1;
  }

  function tick() {
    ctx.clearRect(0, 0, width, height);
    drawWind();
    drawRain();
    drawRipples();
    requestAnimationFrame(tick);
  }

  window.addEventListener("resize", resize);
  init();
  requestAnimationFrame(tick);
}

/* =========================================================
   Occasional lightning flash
   ========================================================= */
function initLightning() {
  var flash = document.querySelector(".lightning-flash");
  if (!flash) return;

  var enabled = document.body.getAttribute("data-lightning") !== "off";
  if (!enabled) return;

  function scheduleFlash() {
    var delay = 6000 + Math.random() * 10000;
    setTimeout(function () {
      flash.classList.add("flash");
      setTimeout(function () {
        flash.classList.remove("flash");
        scheduleFlash();
      }, 600);
    }, delay);
  }
  scheduleFlash();
}

/* =========================================================
   Risk gauge — animates needle + arc fill on result pages
   Reads data-risk="high|low" and data-value="0-100" from the gauge element
   ========================================================= */
function initGauge() {
  var gauge = document.querySelector("[data-gauge]");
  if (!gauge) return;

  var value = parseFloat(gauge.getAttribute("data-value")) || 0;
  var risk = gauge.getAttribute("data-risk") || "low";
  var fill = gauge.querySelector(".gauge-fill");
  var needle = gauge.querySelector(".gauge-needle");

  var color = risk === "high" ? "#F5A623" : "#34D399";
  var offset = 251.2 - (251.2 * value) / 100;
  var angle = -90 + (value / 100) * 180;

  requestAnimationFrame(function () {
    setTimeout(function () {
      if (fill) {
        fill.style.stroke = color;
        fill.style.strokeDashoffset = offset;
      }
      if (needle) {
        needle.style.transform = "rotate(" + angle + "deg)";
      }
    }, 150);
  });
}