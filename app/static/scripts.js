document.addEventListener("DOMContentLoaded", function () {
    const chatForm = document.getElementById("chatForm");
    chatForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        const formData = new FormData(chatForm);
        const userMessage = formData.get("message");

        const conversation = document.getElementById("conversation");

        // Afficher le message de l'utilisateur
        const userMessageElement = document.createElement("div");
        userMessageElement.classList.add("user-message");
        userMessageElement.innerHTML = userMessage; // Ajouter le message de l'utilisateur en texte brut
        conversation.appendChild(userMessageElement);

        // Réinitialiser l'input après envoi du message
        chatForm.reset();

        // Envoyer le message au serveur
        try {
            const response = await fetch("/send_message", {
                method: "POST",
                body: formData,
            });

            const result = await response.json();

            // Afficher la réponse du bot
            const botMessageElement = document.createElement("div");
            botMessageElement.classList.add("bot-message");
            botMessageElement.innerHTML = result.response || "Error: No response";
            conversation.appendChild(botMessageElement);

            // Rendre les éléments LaTeX avec KaTeX
            renderMathInElement(botMessageElement, {
                delimiters: [
                    { left: "$$", right: "$$", display: true },
                    { left: "$", right: "$", display: false },
                    { left: "\\[", right: "\\]", display: true },
                    { left: "\\(", right: "\\)", display: false }
                ]
            });

            conversation.scrollTop = conversation.scrollHeight; // Scroll to the bottom
        } catch (error) {
            console.error("Error:", error);
            const botMessageElement = document.createElement("div");
            botMessageElement.classList.add("bot-message");
            botMessageElement.textContent = "Error: No response";
            conversation.appendChild(botMessageElement);

            conversation.scrollTop = conversation.scrollHeight; // Scroll to the bottom
        }

        conversation.scrollTop = conversation.scrollHeight; // Scroll to the bottom
    });
});
