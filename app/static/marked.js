
document.addEventListener("DOMContentLoaded", function () {
  const chatForm = document.getElementById("chatForm");
  chatForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const formData = new FormData(chatForm);
    const userMessage = formData.get("message");

    const conversation = document.getElementById("conversation");

    // Display user's message
    const userMessageElement = document.createElement("div");
    userMessageElement.classList.add("user-message");
    userMessageElement.innerHTML = marked(userMessage);
    conversation.appendChild(userMessageElement);

    // Send the message to the server
    try {
      const response = await fetch("/send_message", {
        method: "POST",
        body: formData,
      });

      const result = await response.json();

      // Display bot's response
      const botMessageElement = document.createElement("div");
      botMessageElement.classList.add("bot-message");
      botMessageElement.innerHTML = marked(result.response || "Error: No response");
      conversation.appendChild(botMessageElement);
    } catch (error) {
      console.error("Error:", error);
      const botMessageElement = document.createElement("div");
      botMessageElement.classList.add("bot-message");
      botMessageElement.textContent = "Error: No response";
      conversation.appendChild(botMessageElement);
    }

    conversation.scrollTop = conversation.scrollHeight; // Scroll to the bottom
    chatForm.reset();
  });
});