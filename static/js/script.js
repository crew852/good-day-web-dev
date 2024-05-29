document.addEventListener("DOMContentLoaded", function () {
  const toggleBtn = document.getElementById("toggleBtn")
  const sidebar = document.getElementById("sidebar")
  const mainContent = document.getElementById("mainContent")

  const isCollapsed = localStorage.getItem("sidebarCollapsed") === "true"

  if (isCollapsed) {
    sidebar.classList.add("collapsed", "no-transition")
    mainContent.classList.add("collapsed", "no-transition")
    toggleBtn.classList.add("collapsed", "no-transition")

    setTimeout(() => {
      sidebar.classList.remove("no-transition")
      mainContent.classList.remove("no-transition")
      toggleBtn.classList.remove("no-transition")
    }, 10)
  }

  toggleBtn.onclick = function () {
    const isCollapsed = sidebar.classList.contains("collapsed")

    localStorage.setItem("sidebarCollapsed", !isCollapsed)

    sidebar.classList.toggle("collapsed")
    mainContent.classList.toggle("collapsed")
    toggleBtn.classList.toggle("collapsed")
  }
})

document
  .getElementById("fileUpload")
  .addEventListener("change", function (event) {
    const reader = new FileReader()
    reader.onload = function (event) {
      document.getElementById("codeInput").value = event.target.result
    }
    reader.readAsText(event.target.files[0])
  })

Prism.highlightAll()
