const API_URL = "/api/chat";  // Integrated endpoint — no full URL needed!

async function sendMessage() {
  const input = document.getElementById("userInput");
  const message = input.value.trim();
  if (!message) return;

  addMessage(message, "user");
  input.value = "";

  const loadingId = addMessage("Thinking...", "assistant");

  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message })
    });
    const data = await res.json();
    replaceMessage(loadingId, data.reply || "No reply", "assistant");
  } catch (err) {
    replaceMessage(loadingId, "Error: Could not reach agent.", "assistant");
  }
}

function addMessage(text, sender) {
  const chat = document.getElementById("chat");
  const div = document.createElement("div");
  div.className = `message ${sender}`;
  div.textContent = text;
  div.id = "msg-" + Date.now();
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
  return div.id;
}

function replaceMessage(id, text, sender) {
  const el = document.getElementById(id);
  if (el) {
    el.textContent = text;
    el.className = `message ${sender}`;
  }
}

document.getElementById("userInput").addEventListener("keypress", (e) => {
  if (e.key === "Enter") sendMessage();
});
