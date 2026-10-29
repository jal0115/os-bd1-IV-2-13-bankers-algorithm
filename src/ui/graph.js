/* Resource graph (Гишүүн 4 энэ файлыг өөрчилж хэрэгжүүлнэ).
 *
 * Гэрээ: index.html нь төлөв шинэчлэгдэх болгонд
 *     window.drawGraph(state, container)
 * гэж дууддаг. state нь docs/data-format.md §3-ын JSON
 * (available, max, allocation, need, safe, sequence, steps).
 * container нь <div id="graph"> элемент: дотрыг нь өөрөө цэвэрлэж зурна.
 * Зөвлөмж: гадны сан (CDN) ашиглахгүй, inline SVG-ээр зурвал интернетгүй
 * компьютер дээр ч ажиллана.
 *
 * Доорх нь зөвхөн түр хоосон (placeholder) хэрэгжилт.
 */
window.drawGraph = function (state, container) {
  container.textContent =
    "Resource graph энд зурагдана (Гишүүн 4: src/ui/graph.js). " +
    "Одоогийн төлөв: " + state.n + " процесс, " + state.m + " нөөц.";
};
