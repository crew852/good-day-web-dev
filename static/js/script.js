document.addEventListener("DOMContentLoaded", function () {
  const toggleBtn = document.getElementById("toggleBtn")
  const sidebar = document.getElementById("sidebar")
  const mainContent = document.getElementById("mainContent")

  toggleBtn.onclick = function () {
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
