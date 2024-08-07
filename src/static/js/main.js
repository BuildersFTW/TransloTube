function extractContent(s) {
  var span = document.createElement("span");
  span.innerHTML = s;
  return span.textContent || span.innerText;
}

document.getElementById("form").addEventListener("submit", function (event) {
  event.preventDefault();
  startTask();
});

function startTask() {
  document.getElementById("submitBtn").disabled = true;

  const link = document.getElementById("yt-url").value;
  const language = document.getElementById("languageInp").value;
  const voiceoverGender = document.querySelector(
    'input[name="voiceoverGender"]:checked'
  ).value;
  const quizLang = document.querySelector(
    'input[name="quizLang"]:checked'
  ).value;

  fetch(
    `/watch/?link=${encodeURIComponent(link)}&language=${encodeURIComponent(
      language
    )}&voiceoverGender=${encodeURIComponent(
      voiceoverGender
    )}&quizLang=${encodeURIComponent(quizLang)}`,
    {
      method: "GET",
    }
  )
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "Starting Voiceover Generation...") {
        pollTaskStatus(data.task_id);
        document.getElementById("taskStatus").innerText =
          "Voiceover Generation Starting...";

        document.getElementById(
          "loading"
        ).innerHTML = `<section class="dots-container">
                      <div class="dot"></div>
                      <div class="dot"></div>
                      <div class="dot"></div>
                      <div class="dot"></div>
                      <div class="dot"></div>
                  </section>`;
      } else {
        document.getElementById("taskStatus").innerText =
          "Error starting task.";
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      document.getElementById("taskStatus").innerText = "Error starting task.";
    });
}

function pollTaskStatus(taskId) {
  const intervalId = setInterval(() => {
    fetch(`/task-status/${taskId}/`, {
      method: "GET",
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.status.startsWith("Error")) {
          clearInterval(intervalId);
          document.getElementById("loading").innerHTML = "";
          document.getElementById("taskStatus").innerText = data.status;
        } else if (data.status === "Completed") {
          clearInterval(intervalId);
          window.location.href = `/video/${taskId}/`;
          setupChat();
          // fetch(`/video/${taskId}/`, {
          //   method: "GET",
          // })
          //   .then((response) => response.text())
          //   .then((html) => {
          //     const parser = new DOMParser();
          //     const doc = parser.parseFromString(html, "text/html");

          //     // Replace the current document's content with the fetched HTML
          //     document.documentElement.replaceWith(doc.documentElement);
          //     console.log("Before handle yt frame");

          //
          //   });
        } else {
          document.getElementById("taskStatus").innerText = data.status;
        }
      })
      .catch((error) => {
        console.error("Error:", error);
        clearInterval(intervalId);
        document.getElementById("taskStatus").innerText =
          "Error checking task status.";
      });
  }, 5000); // Poll every 3 seconds
}

function copyToClipboard() {
  let selection = document.querySelector("md-block");
  console.log(selection);
  var copyText = extractContent(selection.innerHTML);

  // Copy the text inside the text field
  navigator.clipboard
    .writeText(copyText)
    .then(() => {
      alert("Content copied to clipboard");
    })
    .catch((err) => {
      console.error("Failed to copy: ", err);
    });
}

function onLanguageChange(lang) {
  console.log(lang);
  const languageInput = document.getElementById("languageInp");
  languageInput.value = lang;
  const languageP = document.getElementById("language");
  languageP.innerText = lang;
}

window.onload = function () {
  // const radioButtons = document.querySelectorAll(".radio-inputs .radio input");
  // const contentSummary = document.getElementById("summary-content");
  // const contentNotes = document.getElementById("notes-content");
  // radioButtons.forEach((radio) => {
  //   radio.addEventListener("change", function () {
  //     if (this.checked) {
  //       if (this.nextElementSibling.textContent.trim() === "Summary") {
  //         contentSummary.style.display = "block";
  //         contentNotes.style.display = "none";
  //       } else if (this.nextElementSibling.textContent.trim() === "Notes") {
  //         contentSummary.style.display = "none";
  //         contentNotes.style.display = "block";
  //       }
  //     }
  //   });
  // });
};

function addURL(vid) {
  document.getElementById("yt-url").value =
    "https://www.youtube.com/watch?v=" + vid;
}
