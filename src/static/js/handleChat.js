var chatInput = document.querySelector(".chat-input textarea");
var sendChatBtn = document.querySelector(".chat-input button");
var chatbox = document.querySelector(".chatbox");

const enableEnterSendMessage = function (e) {
  // Enter pressed
  if (e.keyCode === 13 && !e.shiftKey) {
    // Prevent default behavior
    e.preventDefault();
    handleChat();
    chatInput.value = "";
  }
};

const createChatLi = (message, className) => {
  const chatLi = document.createElement("li");
  chatLi.classList.add("chat", className);
  let chatContent =
    className === "chat-outgoing" ? `<p>${message}</p>` : `<p>${message}</p>`;
  chatLi.innerHTML = chatContent;
  return chatLi;
};

const generateResponse = (incomingChatLi) => {
  const API_URL = "/chatbot/";
  const messageElement = incomingChatLi.querySelector("p");
  const groupedSentences = document
    .getElementById("data")
    .getAttribute("data-grouped-sentences");
  const chats = document.getElementsByClassName("chat");
  let chatHistory = [];
  for (let i = 1; i < chats.length - 2; i++) {
    chatHistory.push({
      role: chats[i].classList.contains("chat-incoming") ? "assistant" : "user",
      content: chats[i].firstChild.textContent,
    });
  }
  const requestOptions = {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify({
      content: userMessage,
      groupedSentences: groupedSentences,
      messageHistory: JSON.stringify(chatHistory),
    }),
  };
  fetch(API_URL, requestOptions)
    .then((res) => {
      if (!res.ok) {
        throw new Error("Network response was not ok");
      }
      return res.json();
    })
    .then((data) => {
      messageElement.textContent = data.content;
    })
    .catch((error) => {
      messageElement.classList.add("error");
      messageElement.textContent =
        "Oops! Something went wrong. Please try again!";
    })
    .finally(() => chatbox.scrollTo(0, chatbox.scrollHeight));
};

const quizContent = () => {
  document.getElementsByClassName("chat-input")[0].style.display = "none";
  document.getElementById("quiz-me").style.display = "none";
  let quizSolution = document.getElementById("quiz-solution");
  quizSolution.style.display = "block";
  let quizNext = document.getElementById("quiz-next");
  quizNext.style.display = "block";

  let questionIndex = 0;
  const fetchQuestion = () => {
    quizNext.disabled = true;
    quizSolution.disabled = true;
    let quizLi = createChatLi("Generating Question...", "chat-quiz");
    chatbox.appendChild(quizLi);
    chatbox.scrollTo(0, chatbox.scrollHeight);

    let messageElement = quizLi.querySelector("p");

    const API_URL = "/quiz/";
    const groupedSentences = document
      .getElementById("data")
      .getAttribute("data-grouped-sentences");
    const targetLang = document
      .getElementById("data")
      .getAttribute("data-target-language");
    const quizLang = document
      .getElementById("data")
      .getAttribute("data-quiz-lang");
    const requestOptions = {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
      },
      body: JSON.stringify({
        groupedSentences: groupedSentences,
        targetLang: targetLang,
        quizLang: quizLang,
      }),
    };
    fetch(API_URL, requestOptions)
      .then((res) => {
        if (!res.ok) {
          throw new Error("Network response was not ok");
        }
        return res.json();
      })
      .then((data) => {
        let question;
        try {
          question = JSON.parse(data.content);
        } catch (e) {
          question = data.content;
        }
        messageElement.textContent = question.question;

        let answer =
          question.correct_answer.length > 1
            ? question.correct_answer[0]
            : question.correct_answer;
        let solution = question.explanation;
        btnList = [];
        question.options.forEach((option, i) => {
          let optionBtn = document.createElement("button");
          btnList.push(optionBtn);
          optionBtn.classList.add("options-btn");
          optionBtn.textContent = option;
          if (answer === option[0]) {
            optionBtn.classList.add("correct-hide");
            optionBtn.onclick = () =>
              checkOption(
                "correct",
                optionBtn,
                undefined,
                (btnList = btnList),
                (solution = solution),
                (quizChat = quizLi)
              );
          } else {
            optionBtn.onclick = () =>
              checkOption(
                "wrong",
                optionBtn,
                undefined,
                (btnList = btnList),
                (solution = solution),
                (quizChat = quizLi)
              );
          }

          quizLi.appendChild(optionBtn);
        });
      })
      .catch((error) => {
        console.log(error);
        messageElement.classList.add("error");
        messageElement.textContent =
          "Oops! Something went wrong. Please try again!";
      })
      .finally(() => chatbox.scrollTo(0, chatbox.scrollHeight));
  };

  const checkOption = (
    result,
    buttonElement,
    correctBtn,
    btnList,
    solution,
    quizChat
  ) => {
    correctBtn = document.getElementsByClassName("correct-hide")[0];
    if (result === "correct") {
      buttonElement.innerHTML += "<br><b>CORRECT</b>";
      buttonElement.style.backgroundColor = "#6abf4b";
    } else {
      buttonElement.innerHTML += "<br><b>WRONG</b>";
      buttonElement.style.backgroundColor = "#e74c3c";
      correctBtn.style.backgroundColor = "#6abf4b";
    }
    correctBtn.classList.remove("correct-hide");
    for (let i = 0; i < btnList.length; i++) {
      btnList[i].onclick = null;
      btnList[i].disabled = true;
    }
    quizNext.disabled = false;
    quizSolution.disabled = false;
    quizSolution.onclick = () => {
      showSolution(solution, quizChat);
    };
    quizNext.onclick = () => {
      nextQuestion();
    };
  };

  const showSolution = (solution, quizChat) => {
    let solutionArea = document.createElement("div");
    solutionArea.classList.add("quiz-solution");
    solutionArea.textContent = solution;
    quizChat.appendChild(solutionArea);
    quizSolution.textContent = "Hide Solution";
    quizSolution.onclick = () => {
      hideSolution(solution, quizChat);
    };
    chatbox.scrollTo(0, chatbox.scrollHeight);
  };

  const hideSolution = (solution, quizChat) => {
    quizChat.removeChild(quizChat.lastChild);
    quizSolution.textContent = "Show Solution";
    quizSolution.onclick = () => {
      showSolution(solution, quizChat);
    };
    chatbox.scrollTo(0, chatbox.scrollHeight);
  };

  const nextQuestion = () => {
    questionIndex++;
    if (questionIndex === 4) {
      quizNext.textContent = "End Quiz";
    } else if (questionIndex >= 5) {
      document.getElementsByClassName("chat-input")[0].style.display = "flex";
      document.getElementById("quiz-me").style.display = "block";
      quizSolution.style.display = "none";
      quizNext.textContent = "Next Question";
      quizNext.style.display = "none";
      return;
    }
    quizSolution.textContent = "Show Solution";
    fetchQuestion();
    chatbox.scrollTo(0, chatbox.scrollHeight);
  };

  fetchQuestion();
};

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

const handleChat = () => {
  chatInput.removeEventListener("keydown", enableEnterSendMessage);
  sendChatBtn.removeEventListener("click", handleChat);
  userMessage = chatInput.value.trim();
  if (!userMessage) {
    return;
  }
  chatbox.appendChild(createChatLi(userMessage, "chat-outgoing"));
  chatbox.scrollTo(0, chatbox.scrollHeight);

  setTimeout(() => {
    const incomingChatLi = createChatLi("Thinking...", "chat-incoming");
    chatbox.appendChild(incomingChatLi);
    chatbox.scrollTo(0, chatbox.scrollHeight);
    generateResponse(incomingChatLi); // work on the function
    sendChatBtn.addEventListener("click", handleChat);
    chatInput.addEventListener("keydown", enableEnterSendMessage);
  }, 600);
};

sendChatBtn.addEventListener("click", handleChat);
chatInput.addEventListener("keydown", enableEnterSendMessage);
