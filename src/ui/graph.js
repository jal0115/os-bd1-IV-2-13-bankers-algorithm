/* Resource graph (Гишүүн 4) — Banker's Algorithm · IV-2-13
 *
 * ЮУ ЗУРДАГ ВЭ (сурах бичгийн "Resource-Allocation Graph"-тай ижил зүйл):
 *   ○ Дугуй  = процесс (P0, P1, ...)
 *   ▭ Хүрээ  = нөөцийн төрөл (R0, R1, ...); доторх жижиг цэг бүр = нөөцийн 1 нэгж
 *   → Цэнхэр бүдүүн сум  R → P  : Allocation (нөөц процесст олгогдсон, тоо = хэдэн нэгж)
 *   ⇢ Саарал тасархай сум P → R : Need (процесс цаашид хүсч БОЛЗОШГҮЙ нөөц = "claim edge")
 *
 * ЮУГААР САЙН ОЙЛГОГДОХ ВЭ:
 *   - Процессын булан дахь тоотой цагираг: Safe sequence-ийн дараалал (1, 2, 3 ...).
 *     Улаан ✖ = энэ процесс дуусч чадахгүй (UNSAFE).
 *   - "Дараах ▶" товч: Safe sequence-ийг граф дээр алхам алхмаар тоглуулна.
 *     Процесс дуусахад түүний сумнууд алга болж, нөөц нь чөлөөтэй болж, Work нэмэгдэнэ.
 *   - Процесс / нөөц дээр хулгана аваачихад (эсвэл дарахад) зөвхөн холбоотой сумнууд тод гарна.
 *
 * ГЭРЭЭ (index.html-тэй): window.drawGraph(state, container)
 *   state     = docs/data-format.md §3 (n, m, available, max, allocation, need, safe, sequence, steps)
 *   container = <div id="graph">; доторх бүгдийг энэ файл өөрөө цэвэрлэж зурна.
 * Гадны сан (CDN) ашиглаагүй: цэвэр inline SVG тул интернетгүй ч ажиллана.
 * Өнгө: index.html-ийн window.BANKER_COLORS палитрыг ашиглана (байхгүй бол доорх default).
 */
(function () {
  "use strict";

  var NS = "http://www.w3.org/2000/svg";

  /* ---------------------------------------------------------------
   * 1. Тохиргоо (байрлал, хэмжээ)
   * ------------------------------------------------------------- */
  var CFG = {
    PAD: 30,          // зүүн/баруун хоосон зай
    PROC_Y: 70,       // процессын төвийн y
    PROC_R: 22,       // процессын радиус
    BOX_W: 132,       // нөөцийн хүрээний өргөн
    BOX_TOP: 250,     // нөөцийн хүрээний дээд y
    DOT_R: 6,         // нэгж (цэг)-ийн радиус
    DOT_COLS: 6,      // нэг мөрөнд хэдэн цэг
    DOT_MAX: 18,      // энэ тооноос их нэгжтэй бол цэгийн оронд пропорциональ туузаар зурна
    BEND: 22          // Allocation / Need хоёр сумны хоорондын нум
  };

  function palette() {
    var C = window.BANKER_COLORS || {};
    return {
      process: C.process || ["#2f6fe4", "#1fb386", "#8a44c8", "#f5b50a", "#0fa3b8", "#e0483e", "#64748b", "#d4577b"],
      processText: C.processText || ["#fff", "#fff", "#fff", "#3a2a00", "#fff", "#fff", "#fff", "#fff"],
      resource: C.resource || ["#e0483e", "#2563eb", "#f0a500", "#7c3aed", "#0891b2", "#db2777"],
      alloc: C.alloc || "#2563eb",
      need: C.need || "#94a3b8",
      ok: C.ok || "#15803d",
      bad: C.bad || "#dc2626",
      text: "#12233f",
      muted: "#64748b"
    };
  }

  /* ---------------------------------------------------------------
   * 2. Жижиг туслахууд
   * ------------------------------------------------------------- */
  function svgEl(tag, attrs, parent) {
    var e = document.createElementNS(NS, tag);
    for (var k in attrs) if (Object.prototype.hasOwnProperty.call(attrs, k)) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  function htmlEl(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  }
  function svgText(parent, x, y, str, attrs) {
    var a = { x: x, y: y, "font-family": "system-ui, 'Segoe UI', Roboto, Arial, sans-serif" };
    for (var k in attrs) a[k] = attrs[k];
    var t = svgEl("text", a, parent);
    t.textContent = str;
    return t;
  }
  function addTitle(el, str) { var t = svgEl("title", {}, el); t.textContent = str; }
  function vec(a) { return "(" + a.join(", ") + ")"; }
  function pIndex(name) { return Number(String(name).slice(1)); }

  /* ---------------------------------------------------------------
   * 3. Загвар (state → зурахад хэрэгтэй хэлбэр)
   * ------------------------------------------------------------- */
  function buildModel(state) {
    var n = state.n, m = state.m;
    var steps = (state.steps || []).map(function (s) {
      return { p: pIndex(s.process), before: s.work_before, after: s.work_after };
    });
    var order = {};                       // процесс → safe sequence дахь дугаар (1-ээс)
    steps.forEach(function (s, k) { order[s.p] = k + 1; });
    var total = [];                       // нөөц бүрийн НИЙТ нэгж = Available + Σ Allocation
    for (var j = 0; j < m; j++) {
      var t = state.available[j];
      for (var i = 0; i < n; i++) t += state.allocation[i][j];
      total.push(t);
    }
    return {
      n: n, m: m, safe: !!state.safe,
      available: state.available, allocation: state.allocation, need: state.need, max: state.max,
      steps: steps, order: order, total: total
    };
  }

  /* ---------------------------------------------------------------
   * 4. Нэг алхмын SVG зурах (k = хэдэн процесс дууссан бэ)
   * ------------------------------------------------------------- */
  function buildSvg(model, k, C) {
    var n = model.n, m = model.m, i, j;
    var finished = {};
    for (var q = 0; q < k; q++) finished[model.steps[q].p] = true;
    var nextP = k < model.steps.length ? model.steps[k].p : -1;

    // ---- хэмжээс ----
    var W = Math.max(480, n * 72, m * 140);
    var maxRows = 1;
    for (j = 0; j < m; j++) {
      if (model.total[j] <= CFG.DOT_MAX) maxRows = Math.max(maxRows, Math.ceil(model.total[j] / CFG.DOT_COLS));
    }
    var boxH = 38 + maxRows * 18 + 22;   // доод 16px = «чөлөөтэй x / нийт y» мөр
    var H = CFG.BOX_TOP + boxH + 16;

    var svg = svgEl("svg", {
      viewBox: "0 0 " + W + " " + H, role: "img",
      "aria-label": "Resource allocation graph: " + n + " процесс, " + m + " нөөцийн төрөл"
    });
    svg.style.width = "100%"; svg.style.minWidth = Math.min(W, 560) + "px"; svg.style.height = "auto"; svg.style.display = "block";

    // ---- сумны толгой ----
    var defs = svgEl("defs", {}, svg);
    [["ah-alloc", C.alloc], ["ah-need", "#64748b"]].forEach(function (d) {
      var mk = svgEl("marker", { id: d[0], viewBox: "0 0 10 10", refX: 9, refY: 5, markerWidth: 9, markerHeight: 9, markerUnits: "userSpaceOnUse", orient: "auto" }, defs);
      svgEl("path", { d: "M0,0 L10,5 L0,10 z", fill: d[1] }, mk);
    });

    // ---- байрлал ----
    var procs = [], ress = [];
    for (i = 0; i < n; i++) procs.push({ x: CFG.PAD + (i + 0.5) * (W - 2 * CFG.PAD) / n, y: CFG.PROC_Y });
    for (j = 0; j < m; j++) ress.push({ x: CFG.PAD + (j + 0.5) * (W - 2 * CFG.PAD) / m, y: CFG.BOX_TOP });
    var spread = Math.min(10, (CFG.BOX_W - 28) / Math.max(1, n - 1));

    // Нөөц бүрийн нэгжийг хэн эзэлж байгаа вэ (дууссан процессын нэгж чөлөөтэй болсон)
    var held = [];     // held[j][i] = i процессын j нөөцөд барьж буй нэгж
    var free = [];     // free[j]    = чөлөөтэй нэгж 😊 Work[j])
    for (j = 0; j < m; j++) {
      held.push([]);
      var used = 0;
      for (i = 0; i < n; i++) { var h = finished[i] ? 0 : model.allocation[i][j]; held[j].push(h); used += h; }
      free.push(model.total[j] - used);
    }

    var items = [];   // hover/pin-д оролцох элементүүд: {el, kind, p, r}

    var gEdges = svgEl("g", {}, svg);
    var gLabels = svgEl("g", {}, svg);
    var gRes = svgEl("g", {}, svg);
    var gProc = svgEl("g", {}, svg);

    // ---- сумнууд ----
    function geom(i2, j2, sign) {
      var P = procs[i2];
      var R = { x: ress[j2].x + (i2 - (n - 1) / 2) * spread, y: ress[j2].y };
      var dx = R.x - P.x, dy = R.y - P.y, len = Math.sqrt(dx * dx + dy * dy) || 1;
      var ux = dx / len, uy = dy / len;
      var a = { x: P.x + ux * (CFG.PROC_R + 2), y: P.y + uy * (CFG.PROC_R + 2) };
      var b = { x: R.x, y: R.y - 1 };
      var c = { x: (a.x + b.x) / 2 + (-uy) * sign * CFG.BEND, y: (a.y + b.y) / 2 + ux * sign * CFG.BEND };
      return { a: a, b: b, c: c, mid: { x: 0.25 * a.x + 0.5 * c.x + 0.25 * b.x, y: 0.25 * a.y + 0.5 * c.y + 0.25 * b.y } };
    }
    function label(mid, str, bg, i2, j2) {
      var w = 10 + 7 * String(str).length;
      var grp = svgEl("g", {}, gLabels);
      svgEl("rect", { x: mid.x - w / 2, y: mid.y - 8, width: w, height: 16, rx: 8, fill: bg, stroke: "#fff", "stroke-width": 1.5 }, grp);
      svgText(grp, mid.x, mid.y + 4, str, { "text-anchor": "middle", "font-size": 11, "font-weight": 800, fill: "#fff" });
      items.push({ el: grp, kind: "edge", p: i2, r: j2 });
    }
    // Need (тасархай) эхлээд, Allocation (бүдүүн) дээр нь
    for (i = 0; i < n; i++) {
      if (finished[i]) continue;
      for (j = 0; j < m; j++) {
        var nd = model.need[i][j];
        if (nd > 0) {
          var gn = geom(i, j, -1);
          var pn = svgEl("path", {
            d: "M" + gn.a.x + "," + gn.a.y + " Q" + gn.c.x + "," + gn.c.y + " " + gn.b.x + "," + gn.b.y,
            fill: "none", stroke: C.need, "stroke-width": 1.6, "stroke-dasharray": "6 4", "marker-end": "url(#ah-need)"
          }, gEdges);
          addTitle(pn, "Need: P" + i + " → R" + j + " (" + nd + " нэгж хүсч болзошгүй)");
          items.push({ el: pn, kind: "edge", p: i, r: j });
          label(gn.mid, String(nd), "#64748b", i, j);
        }
      }
    }
    for (i = 0; i < n; i++) {
      if (finished[i]) continue;
      for (j = 0; j < m; j++) {
        var al = model.allocation[i][j];
        if (al > 0) {
          var ga = geom(i, j, +1);
          var pa = svgEl("path", {
            d: "M" + ga.b.x + "," + ga.b.y + " Q" + ga.c.x + "," + ga.c.y + " " + ga.a.x + "," + ga.a.y,
            fill: "none", stroke: C.alloc, "stroke-width": 1.8 + 0.5 * Math.min(al, 5), "marker-end": "url(#ah-alloc)"
          }, gEdges);
          addTitle(pa, "Allocation: R" + j + " → P" + i + " (" + al + " нэгж олгосон)");
          items.push({ el: pa, kind: "edge", p: i, r: j });
          label(ga.mid, String(al), C.alloc, i, j);
        }
      }
    }

    // ---- нөөцийн хүрээнүүд ----
    for (j = 0; j < m; j++) {
      (function (j) {
        var rc = C.resource[j % C.resource.length];
        var bx = ress[j].x - CFG.BOX_W / 2, by = CFG.BOX_TOP;
        var g = svgEl("g", { style: "cursor:pointer" }, gRes);
        svgEl("rect", { x: bx, y: by, width: CFG.BOX_W, height: boxH, rx: 10, fill: "#fff", stroke: rc, "stroke-width": 2.5 }, g);
        svgEl("circle", { cx: bx + 14, cy: by + 17, r: 6, fill: rc }, g);
        svgText(g, bx + 26, by + 22, "R" + j, { "font-size": 15, "font-weight": 800, fill: C.text });
        svgText(g, bx + CFG.BOX_W / 2, by + boxH - 8, "чөлөөтэй " + free[j] + "/" + model.total[j],
          { "text-anchor": "middle", "font-size": 11.5, "font-weight": 700, fill: free[j] > 0 ? C.ok : C.muted });

        // нэгжүүд
        var total = model.total[j];
        if (total <= CFG.DOT_MAX) {
          var owners = [];                       // нэгж бүрийн эзэн: процессын индекс эсвэл -1 (чөлөөтэй)
          for (var pi = 0; pi < n; pi++) for (var u = 0; u < held[j][pi]; u++) owners.push(pi);
          while (owners.length < total) owners.push(-1);
          owners.forEach(function (ow, idx) {
            var cx = bx + 18 + (idx % CFG.DOT_COLS) * 18, cy = by + 40 + Math.floor(idx / CFG.DOT_COLS) * 18;
            var d = svgEl("circle", {
              cx: cx, cy: cy, r: CFG.DOT_R,
              fill: ow < 0 ? "#fff" : C.process[ow % C.process.length],
              stroke: ow < 0 ? "#94a3b8" : "#fff", "stroke-width": ow < 0 ? 1.6 : 1
            }, g);
            addTitle(d, ow < 0 ? "R" + j + ": чөлөөтэй нэгж" : "R" + j + ": P" + ow + "-д олгосон нэгж");
          });
        } else {
          // Олон нэгжтэй үед: пропорциональ туузаар зурна (цэг хэт олширно)
          var x0 = bx + 10, bw = CFG.BOX_W - 20, cur = x0;
          svgEl("rect", { x: x0, y: by + 32, width: bw, height: 16, rx: 4, fill: "#fff", stroke: "#94a3b8", "stroke-width": 1.2 }, g);
          for (var pj = 0; pj < n; pj++) {
            if (!held[j][pj]) continue;
            var w2 = bw * held[j][pj] / total;
            var seg = svgEl("rect", { x: cur, y: by + 32, width: w2, height: 16, fill: C.process[pj % C.process.length] }, g);
            addTitle(seg, "R" + j + ": P" + pj + "-д " + held[j][pj] + " нэгж");
            cur += w2;
          }
        }
        addTitle(g, "R" + j + ": нийт " + total + ", чөлөөтэй (Work) " + free[j]);
        items.push({ el: g, kind: "res", p: -1, r: j });
      })(j);
    }

    // ---- процессууд ----
    for (i = 0; i < n; i++) {
      (function (i) {
        var P = procs[i], ci = i % C.process.length;
        var done = !!finished[i];
        var stuck = !model.safe && model.order[i] === undefined;
        var g = svgEl("g", { style: "cursor:pointer" }, gProc);
        if (done) g.setAttribute("opacity", "0.5");

        if (i === nextP) svgEl("circle", { cx: P.x, cy: P.y, r: CFG.PROC_R + 6, fill: "none", stroke: "#2563eb", "stroke-width": 3 }, g);
        if (stuck) svgEl("circle", { cx: P.x, cy: P.y, r: CFG.PROC_R + 6, fill: "none", stroke: C.bad, "stroke-width": 2.5, "stroke-dasharray": "4 3" }, g);
        svgEl("circle", { cx: P.x, cy: P.y, r: CFG.PROC_R, fill: C.process[ci], stroke: done ? C.ok : "#fff", "stroke-width": done ? 3 : 2 }, g);
        svgText(g, P.x, P.y + 5, "P" + i, { "text-anchor": "middle", "font-size": 14, "font-weight": 800, fill: C.processText[ci] });

        // Булангийн тэмдэг: дарааллын дугаар / ✓ / ✖
        var bxp = P.x + CFG.PROC_R * 0.85, byp = P.y - CFG.PROC_R * 0.85;
        if (done) {
          svgEl("circle", { cx: bxp, cy: byp, r: 9, fill: C.ok, stroke: "#fff", "stroke-width": 1.5 }, g);
          svgText(g, bxp, byp + 4, "✓", { "text-anchor": "middle", "font-size": 12, "font-weight": 800, fill: "#fff" });
        } else if (stuck) {
          svgEl("circle", { cx: bxp, cy: byp, r: 9, fill: C.bad, stroke: "#fff", "stroke-width": 1.5 }, g);
          svgText(g, bxp, byp + 4, "✖", { "text-anchor": "middle", "font-size": 11, "font-weight": 800, fill: "#fff" });
        } else if (model.order[i] !== undefined) {
          svgEl("circle", { cx: bxp, cy: byp, r: 9, fill: "#fff", stroke: C.ok, "stroke-width": 2 }, g);
          svgText(g, bxp, byp + 4, String(model.order[i]), { "text-anchor": "middle", "font-size": 11.5, "font-weight": 800, fill: C.ok });
        }

        // Need вектор процессын дээр (m ≤ 4 үед)
        if (m <= 4) svgText(g, P.x, P.y - CFG.PROC_R - 12, "Need " + model.need[i].join(","), { "text-anchor": "middle", "font-size": 10.5, fill: C.muted });

        addTitle(g, "P" + i + "\nMax " + vec(model.max[i]) + "\nAllocation " + vec(model.allocation[i]) + "\nNeed " + vec(model.need[i]) +
          (done ? "\n(дууссан)" : model.order[i] !== undefined ? "\nSafe sequence-ийн " + model.order[i] + "-р процесс" : (model.safe ? "" : "\nдуусч чадахгүй")));
        items.push({ el: g, kind: "proc", p: i, r: -1 });
      })(i);
    }

    // ---- hover / click: холбоотой сумнуудыг тодруулах ----
    function connected(i2, j2) { return !finished[i2] && (model.allocation[i2][j2] > 0 || model.need[i2][j2] > 0); }
    function related(it, sel) {
      if (sel.p >= 0) {
        if (it.kind === "edge" || it.kind === "proc") return it.p === sel.p;
        return connected(sel.p, it.r);
      }
      if (it.kind === "edge" || it.kind === "res") return it.r === sel.r;
      return connected(it.p, sel.r);
    }
    var pinned = null;
    function apply(sel) {
      items.forEach(function (it) { it.el.style.opacity = (!sel || related(it, sel)) ? "" : "0.12"; });
    }
    items.forEach(function (it) {
      if (it.kind === "edge") return;
      var sel = { p: it.p, r: it.r };
      it.el.addEventListener("mouseenter", function () { apply(sel); });
      it.el.addEventListener("mouseleave", function () { apply(pinned); });
      it.el.addEventListener("click", function () {
        pinned = (pinned && pinned.p === sel.p && pinned.r === sel.r) ? null : sel;
        apply(pinned);
      });
    });

    return svg;
  }

  /* ---------------------------------------------------------------
   * 5. Тайлбар мөр (одоогийн алхам юу болж байгааг үгээр хэлнэ)
   * ------------------------------------------------------------- */
  function describe(model, k, info) {
    info.textContent = "";
    function b(t) { info.appendChild(htmlEl("b", null, t)); }
    function t(s) { info.appendChild(document.createTextNode(s)); }
    var N = model.steps.length;

    if (k === 0) {
      b("Эхлэл. "); t("Work = Available = " + vec(model.available) + ". ");
      if (model.safe) {
        t("Төлөв "); b("SAFE");
        t(": дараалал " + model.steps.map(function (s) { return "P" + s.p; }).join(" → ") + ". Дээрх «▶ Эхлүүлэх» товчийг дарж алхам алхмаар харна уу.");
      } else if (N > 0) {
        t("Төлөв "); b("UNSAFE"); t(": зөвхөн " + N + " процесс дуусаж чадна, бусад нь чадахгүй. «▶ Эхлүүлэх» товчоор харна уу.");
      } else {
        t("Төлөв "); b("UNSAFE"); t(": ямар ч процесс одоо дуусч чадахгүй (бүгдийн Need > Work).");
      }
      return;
    }
    var s = model.steps[k - 1];
    b("Алхам " + k + "/" + N + ": P" + s.p + " дууслаа. ");
    t("Need " + vec(model.need[s.p]) + " ≤ Work " + vec(s.before) + " тул дуусаад Allocation " + vec(model.allocation[s.p]) + "-аа буцаалаа → ");
    b("Work = " + vec(s.after) + ". ");
    if (k < N) { var nx = model.steps[k]; t("Дараа нь P" + nx.p + " дуусна (Need " + vec(model.need[nx.p]) + " ≤ Work " + vec(nx.before) + "). "); }
    if (k === N) {
      if (model.safe) { t("Бүх процесс дууслаа → "); b("SAFE."); }
      else {
        var left = [];
        for (var i = 0; i < model.n; i++) if (model.order[i] === undefined) left.push("P" + i);
        t("Үлдсэн " + left.join(", ") + "-ийн Need > Work тул дуусч чадахгүй → "); b("UNSAFE.");
      }
    }
  }

  /* ---------------------------------------------------------------
   * 6. Хурдны сонголт + нэг удаагийн CSS
   * ------------------------------------------------------------- */
  var SPEEDS = [[1600, "Удаан", "1.6"], [800, "Дунд", "0.8"], [400, "Хурдан", "0.4"]];
  var speedMs = 800;                       // шинэ төлөв ачаалахад ч хадгалагдана
  function speedText(ms) {
    for (var q = 0; q < SPEEDS.length; q++) if (SPEEDS[q][0] === ms) return SPEEDS[q][1] + " · " + SPEEDS[q][2] + " сек/алхам";
    return ms + " мс/алхам";
  }

  function injectStyle() {
    if (document.getElementById("graph-style")) return;
    var st = htmlEl("style"); st.id = "graph-style";
    st.textContent =
      "#graph .gnav{display:flex;gap:8px;align-items:center;justify-content:center;flex-wrap:wrap;margin:0 0 10px}" +
      "#graph .gspeed{display:flex;align-items:center;justify-content:center;gap:10px;flex-wrap:wrap;margin:0 0 8px;padding:7px 10px;background:#f1f5f9;border-radius:10px}" +
      "#graph .gspeed .lbl{font-size:13px;font-weight:700;color:#475569}" +
      "#graph .seg{display:inline-flex;border:1.5px solid #cbd5e1;border-radius:9px;overflow:hidden;background:#fff}" +
      "#graph .seg button{border:0;border-radius:0;padding:6px 14px;font-size:13px;background:#fff;color:#12233f;border-right:1px solid #e2e8f0}" +
      "#graph .seg button:last-child{border-right:0}" +
      "#graph .seg button[aria-pressed=true],#graph .seg button[aria-pressed=true]:hover{background:#1e3a8a;color:#fff}" +
      "#graph .gval{font-size:13px;font-weight:800;color:#1e3a8a;padding:3px 12px;border-radius:999px;background:#e8f0ff;display:inline-block}" +
      "#graph .gval.flash{animation:gflash .7s ease}" +
      "@keyframes gflash{0%{background:#fde68a;transform:scale(1.15)}100%{background:#e8f0ff;transform:scale(1)}}" +
      "#graph .ghint{width:100%;text-align:center;font-size:12px;color:#64748b}#graph .ghint:empty{display:none}" +
      "#graph .gbar{height:6px;background:#e2e8f0;border-radius:3px;overflow:hidden;margin:0 0 10px}" +
      "#graph .gbar i{display:block;height:100%;width:0;background:#2563eb;border-radius:3px}" +
      "#graph .gpos{width:100%;text-align:center;font-size:12.5px;color:#64748b}" +
      "#graph button:focus-visible,#graph:focus-visible{outline:3px solid #93c5fd;outline-offset:2px}" +
      "@media (prefers-reduced-motion:reduce){#graph .gval.flash{animation:none}#graph .gbar i{transition:none!important}}";
    document.head.appendChild(st);
  }

  /* ---------------------------------------------------------------
   * 7. Үндсэн функц
   * ------------------------------------------------------------- */
  window.drawGraph = function (state, container) {
    if (window.graphStop) window.graphStop();
    injectStyle();
    container.textContent = "";
    // index.html-ийн placeholder (тасархай хүрээ, голлуулсан текст)-ийг цэвэрлэнэ
    container.style.display = "block";
    container.style.border = "1px solid #e2e8f0";
    container.style.padding = "12px";
    container.style.textAlign = "left";
    container.style.color = "#12233f";
    container.style.background = "#fff";
    container.style.overflow = "auto";

    if (!state || !state.n || !state.m) {
      container.textContent = "Граф зурахад өгөгдөл алга.";
      return;
    }
    var C = palette();
    var model = buildModel(state);
    var N = model.steps.length;
    var k = 0, timer = null;       // шинэ төлөв болгонд эхнээс нь эхэлнэ

    /* --- тайлбар мөр --- */
    var info = htmlEl("div");
    info.style.cssText = "font-size:13.5px;line-height:1.5;padding:9px 12px;margin-bottom:10px;border-radius:10px;border:1.5px solid " +
      (model.safe ? "#9bd9b3" : "#f3a6a3") + ";background:" + (model.safe ? "#e8f8ee" : "#fdecec") + ";color:#12233f;";
    info.setAttribute("aria-live", "polite");

    var holder = htmlEl("div");

    /* --- удирдлагын товчнууд --- */
    var nav = htmlEl("div", "gnav");
    var bFirst = htmlEl("button", null, "⏮ Эхлэл"), bPrev = htmlEl("button", null, "◀ Өмнөх"), bPlay = htmlEl("button", "primary", "▶ Эхлүүлэх"),
        bNext = htmlEl("button", null, "Дараах ▶"), bLast = htmlEl("button", null, "Төгсгөл ⏭");
    bPlay.style.cssText = "font-size:15px;padding:10px 22px;min-width:170px;";
    [bFirst, bPrev, bPlay, bNext, bLast].forEach(function (e) { nav.appendChild(e); });

    /* --- хурдны сонголт: идэвхтэй товч + одоогийн утга + тайлбар --- */
    var speedBox = htmlEl("div", "gspeed");
    speedBox.appendChild(htmlEl("span", "lbl", "Тоглуулах хурд:"));
    var seg = htmlEl("div", "seg"); seg.setAttribute("role", "group"); seg.setAttribute("aria-label", "Тоглуулах хурд");
    var segBtns = SPEEDS.map(function (x) {
      var b = htmlEl("button", null, x[1]); b.type = "button";
      b.title = x[2] + " секунд тутамд 1 алхам";
      b.onclick = function () { setSpeed(x[0]); };
      seg.appendChild(b); return b;
    });
    var gval = htmlEl("span", "gval", "");
    var ghint = htmlEl("div", "ghint", "");
    speedBox.appendChild(seg); speedBox.appendChild(gval); speedBox.appendChild(ghint);

    /* --- ахицын зурвас (хурд өөрчлөхөд зурвасын хөдөлгөөн ч өөрчлөгдөнө) --- */
    var bar = htmlEl("div", "gbar"), fill = htmlEl("i");
    bar.appendChild(fill);
    bar.setAttribute("role", "progressbar"); bar.setAttribute("aria-valuemin", "0"); bar.setAttribute("aria-valuemax", String(N));
    var pos = htmlEl("div", "gpos", "");

    var note = htmlEl("div", null,
      "Хүрээ доторх өнгөт цэг = тухайн процесст олгосон нэгж, цагаан цэг = чөлөөтэй нэгж. " +
      "Тоотой цагираг = Safe sequence-ийн дараалал. Цэнхэр цагираг = дараа нь дуусах процесс. " +
      "Процесс/нөөц дээр хулгана аваачвал (эсвэл дарвал) зөвхөн холбоотой сумнууд тод гарна. " +
      "Гар: граф дээр дараад ← → (алхам), Зай (эхлүүлэх/зогсоох), Home / End.");
    note.style.cssText = "font-size:12px;color:#64748b;margin-top:10px;line-height:1.5;";

    function renderSpeed(flash) {
      segBtns.forEach(function (b, q) { b.setAttribute("aria-pressed", SPEEDS[q][0] === speedMs ? "true" : "false"); });
      gval.textContent = speedText(speedMs);
      if (flash) { gval.classList.remove("flash"); void gval.offsetWidth; gval.classList.add("flash"); }
    }
    function setSpeed(ms) {
      speedMs = ms; renderSpeed(true);
      if (timer) { clearInterval(timer); timer = setInterval(tick, speedMs); ghint.textContent = "Хурд шууд солигдлоо."; }
      else ghint.textContent = N ? "Дараагийн «▶ Эхлүүлэх» дээр энэ хурдаар тоглоно." : "";
    }

    function show(newK) {
      var prev = k;
      k = Math.max(0, Math.min(N, newK));
      holder.textContent = "";
      holder.appendChild(buildSvg(model, k, C));
      describe(model, k, info);
      bFirst.disabled = bPrev.disabled = (k === 0);
      bNext.disabled = bLast.disabled = (k >= N);
      pos.textContent = N ? ("Алхам " + k + " / " + N + " · " + k + " процесс дууссан") : "";
      fill.style.transition = (timer && k > prev) ? "width " + Math.round(speedMs * 0.9) + "ms linear" : "width .25s ease";
      fill.style.width = (N ? (k / N * 100) : 0) + "%";
      bar.setAttribute("aria-valuenow", String(k));
      if (typeof window.onGraphStep === "function") window.onGraphStep(k);
    }
    function tick() { if (k >= N) { stop(); return; } show(k + 1); if (k >= N) stop(); }
    function stop() {
      if (timer) { clearInterval(timer); timer = null; }
      bPlay.textContent = (N && k >= N) ? "↻ Дахин эхлүүлэх" : (k > 0 ? "▶ Үргэлжлүүлэх" : "▶ Эхлүүлэх");
    }
    function play() {
      if (timer) { stop(); return; }
      if (k >= N) show(0);
      bPlay.textContent = "⏸ Зогсоох";
      ghint.textContent = "";
      timer = setInterval(tick, speedMs);
    }
    bFirst.onclick = function () { stop(); show(0); };
    bPrev.onclick = function () { stop(); show(k - 1); };
    bNext.onclick = function () { stop(); show(k + 1); };
    bLast.onclick = function () { stop(); show(N); };
    bPlay.onclick = play;
    window.graphGoto = function (kk) {
      stop(); show(kk);
      if (container.scrollIntoView) container.scrollIntoView({ behavior: "smooth", block: "nearest" });
    };
    window.graphStop = stop;

    // Гараас удирдах (граф дээр дарж фокус авсан үед)
    container.tabIndex = 0;
    container.setAttribute("aria-label", "Resource graph. Сумаар алхам солино, Зайгаар тоглуулна.");
    container.onkeydown = function (e) {
      if (e.target !== container || !N) return;
      if (e.key === "ArrowRight") { stop(); show(k + 1); }
      else if (e.key === "ArrowLeft") { stop(); show(k - 1); }
      else if (e.key === "Home") { stop(); show(0); }
      else if (e.key === "End") { stop(); show(N); }
      else if (e.key === " ") { play(); }
      else return;
      e.preventDefault();
    };

    if (N === 0) { nav.style.display = "none"; speedBox.style.display = "none"; bar.style.display = "none"; }

    container.appendChild(nav);
    container.appendChild(speedBox);
    container.appendChild(bar);
    container.appendChild(pos);
    container.appendChild(info);
    container.appendChild(holder);
    container.appendChild(note);
    renderSpeed(false);
    show(0);
    stop();
  };
})();

