
// script.js
const chatInput = $('.chat-input textarea');
const sendChatBtn = $('.chat-input button');
const chatbox = $(".chatbox");
const chatbot = $(".chatBot");
const chatbotToggler = $(".chatbot-toggler");

let userMessage;
let sessionId ="";
const API_URL = ""; // TOBE ADDED
const API_KEY = ""; // TOBE ADDED

const createChatLi = (message, className) => {
    const chatLi = $("<li></li>").addClass("chat").addClass(className);
    let chatContent = className === "chat-outgoing" ? `<i class="bi bi-person" style="font-size:24px;"></i> <p>${message}</p>` 
													: `<i class="bi bi-cpu" style="font-size:24px;" ></i> <p>${message}</p>`;
    chatLi.html(chatContent);
    return chatLi;
}
// Calling API Gateway to get Gen-AI response through post call 
const generateResponse = (incomingChatLi) => {
   const messageElement = incomingChatLi.find("p");

	$.ajax({
		url: API_URL,
		method: 'POST',
		contentType: 'application/json',
		headers: {
			'x-api-key': API_KEY,
		},
		data: JSON.stringify({
			"question":userMessage,
			"sessionId":sessionId
        }),
	  })
	  .done(response => {
		console.log('Success!', response);
		sessionId = response.sessionId;
		messageElement.text(response.answer);
	  })
	  .fail(error => {
		console.error('Error!', error);
		messageElement.addClass("error").text("Oops! Something went wrong. Please try again!");
	  })
	  .always(() => {
		console.log('Always!');
		chatbox.scrollTop(chatbox.prop("scrollHeight"));
	  });

};
const handleChat = () => {
    userMessage = chatInput.val().trim();
	console.log(userMessage);
    if (!userMessage) {
        return;
    }
    chatbox.append(createChatLi(userMessage, "chat-outgoing"));
    chatbox.scrollTop(chatbox.prop("scrollHeight"));

    setTimeout(() => {
        const incomingChatLi = createChatLi("Thinking...", "chat-incoming");
        chatbox.append(incomingChatLi);
        chatbox.scrollTop(chatbox.prop("scrollHeight"));
		    chatInput.val("")
        generateResponse(incomingChatLi);
    }, 600);
}
function cancel() {
  chatbot.toggleClass("show-chatbot")
    // let chatbotcomplete = $(".chatBot");
    // if (chatbotcomplete.css('display') !== 'none') {
    //     chatbotcomplete.css('display', 'none');
    //     let lastMsg = $("<p></p>").text('Thanks for using our Chatbot!').addClass('lastMessage');
    //     $('body').append(lastMsg);
    // }
}
sendChatBtn.click(handleChat);
chatInput[0].addEventListener('keypress', function(event) {
  if(event.key === 'Enter') {
    handleChat();
  }
});

chatbotToggler[0].addEventListener("click", () => {
  console.log("Toggle clicked");
  chatbot.toggleClass("show-chatbot")
});