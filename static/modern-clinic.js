(function () {
  "use strict";

  function addBrandMetadata() {
    if (!document.querySelector('link[rel="icon"]')) {
      var favicon = document.createElement("link");
      favicon.rel = "icon";
      favicon.href = "/static/favicon.ico?v=1";
      document.head.appendChild(favicon);
    }
    if (!document.querySelector('link[rel="apple-touch-icon"]')) {
      var touchIcon = document.createElement("link");
      touchIcon.rel = "apple-touch-icon";
      touchIcon.href = "/static/img/apple-touch-icon.png?v=1";
      document.head.appendChild(touchIcon);
    }
  }

  function addMobileNavigation() {
    if (!document.body || document.querySelector(".clinic-bottom-nav")) return;
    var path = window.location.pathname;
    var items = [
      ["/", "fa-home", "Home"],
      ["/patient", "fa-users", "Clients"],
      ["/appointment", "fa-calendar", "Schedule"],
      ["/admin/adminPanel", "fa-cog", "Settings"]
    ];
    var nav = document.createElement("nav");
    nav.className = "clinic-bottom-nav";
    nav.setAttribute("aria-label", "Main navigation");
    nav.innerHTML = items.map(function (item) {
      var active = item[0] === "/" ? path === "/" : path.indexOf(item[0]) === 0;
      return '<a href="' + item[0] + '" class="' + (active ? "is-active" : "") + '">' +
        '<i class="fa ' + item[1] + '" aria-hidden="true"></i><span>' + item[2] + "</span></a>";
    }).join("");
    document.body.appendChild(nav);
  }

  function applyMobileTableLabels(table) {
    var headers = Array.prototype.map.call(table.querySelectorAll("thead th"), function (header) {
      return header.textContent.trim();
    });
    if (!headers.length) return;

    table.classList.add("clinic-responsive-table");
    var isClientList = window.location.pathname === "/patient" && table.id === "datatable4";
    table.classList.toggle("clinic-client-list", isClientList);
    table.querySelectorAll("tbody tr").forEach(function (row) {
      var cells = row.querySelectorAll("td");
      cells.forEach(function (cell, index) {
        if (cell.classList.contains("dataTables_empty") || cell.colSpan > 1) {
          cell.classList.add("clinic-table-empty");
          cell.removeAttribute("data-label");
          return;
        }
        cell.classList.remove("clinic-table-empty");
        cell.setAttribute("data-label", headers[index] || "Actions");
      });

      if (isClientList && cells.length >= 2 && !cells[0].classList.contains("dataTables_empty")) {
        var language = sessionStorage.getItem("lang") || "EN";
        var fullNameLabel = window.Translate_jsonData && window.Translate_jsonData[language]
          ? window.Translate_jsonData[language].fullName
          : null;
        cells[0].classList.add("clinic-mobile-name");
        cells[0].setAttribute("data-label", fullNameLabel || "Full name");
        cells[0].setAttribute("data-mobile-full-name", (cells[0].textContent + " " + cells[1].textContent).trim());
        for (var hiddenIndex = 1; hiddenIndex <= 6 && hiddenIndex < cells.length; hiddenIndex += 1) {
          cells[hiddenIndex].classList.add("clinic-mobile-hidden");
        }
        for (var actionIndex = 7; actionIndex < cells.length; actionIndex += 1) {
          cells[actionIndex].classList.add("clinic-mobile-action");
        }
      }
    });
  }

  function refreshResponsiveTables() {
    document.querySelectorAll("table.table").forEach(function (table) {
      table.setAttribute("role", "table");
      applyMobileTableLabels(table);
    });
  }

  function improveTables() {
    refreshResponsiveTables();

    var observer = new MutationObserver(function () {
      refreshResponsiveTables();
    });
    document.querySelectorAll("table.table").forEach(function (table) {
      observer.observe(table, {childList: true, subtree: true, characterData: true});
    });

    document.querySelectorAll(".language-flag").forEach(function (button) {
      button.addEventListener("click", function () {
        window.setTimeout(refreshResponsiveTables, 0);
      });
    });
  }

  function markSingleTherapistFields() {
    document.querySelectorAll("#doctor_select").forEach(function (select) {
      var group = select.closest(".form-group");
      if (group) group.classList.add("single-therapist-field");
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    addBrandMetadata();
    addMobileNavigation();
    improveTables();
    markSingleTherapistFields();
  });
})();
