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
document.getElementById("addCodeBlock").addEventListener("click", function () {
  const codeInput = document.getElementById("codeInput")
  const insertionText = "```\n(여기에 코드를 입력)\n```"
  const cursorPositionStart = codeInput.value.length + 6
  const cursorPositionEnd = cursorPositionStart + "여기에 코드를 입력".length

  codeInput.value += insertionText
  codeInput.focus()
  codeInput.setSelectionRange(cursorPositionEnd, cursorPositionEnd)
})
