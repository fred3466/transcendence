
chatSocket.onopen = function (e) {
  console.log("The connection was set up successfully!");
};

chatSocket.onclose = function (e) {
  console.error("Chat socket closed unexpectedly.");
};

document.querySelector("#id_message_send_input").focus();
document.querySelector("#id_message_send_input").onkeyup = function (e) {
  if (e.keyCode === 13) {  // Enter key
    document.querySelector("#id_message_send_button").click();
  }
};

document.querySelector("#id_message_send_button").onclick = function (e) {
  const messageInputDom = document.querySelector("#id_message_send_input");
  const message = messageInputDom.value;
  chatSocket.send(JSON.stringify({ 
    message: message, 
    username: username, 
    room_name: roomName 
  }));
  messageInputDom.value = ""; // Clear the message input field.
};

chatSocket.onmessage = function (e) {
  const data = JSON.parse(e.data);

  if (data.type === 'chat_message') {
      // Existing chat message handling
      const messageElement = document.createElement("div");
      messageElement.innerText = data.message;

      if (data.username === username) {
          messageElement.className = "message own-message";
      } else {
          messageElement.className = "message other-message";
      }

      document.querySelector("#id_chat_item_container").appendChild(messageElement);
  } else if (data.type === 'game_invite') {
      // Handle game invitation
      const sender = data.sender;
      const recipient = data.recipient;
      const party_id = data.party_id;

      // Show a prompt to accept or decline the game invitation
      if (username === recipient) {
        const accept = confirm(`${sender} has invited you to a game. Do you accept?`);
        if (accept) {
            // Redirect to the game page
            window.location.href = `/game/${party_id}/`;
        } else {
            // Optionally, send a decline message back (not implemented here)
        }
      }
  }
};


function updateChatHeader() {
    const usernames = roomSlug.split('_'); // Split the slug to get both usernames
    const otherUsername = usernames.find(u => u !== username); // Find the username that is not the current user's
    document.getElementById('chatWith').textContent = `${otherUsername}`;

    const profileUrl = `https://localhost/users/profile/${otherUsername}`;
    document.getElementById('viewProfile').href = profileUrl;
}

document.getElementById('invitePlayer').addEventListener('click', function() {
  // Send an AJAX request to create a new game and send an invitation
  fetch('/chat/send_game_invite/', {
      method: 'POST',
      headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify({ 'room_slug': roomSlug })
  })
  .then(response => response.json())
  .then(data => {
      if (data.status === 'success') {
          // Redirect to the game page
          window.location.href = `/game/${data.party_id}/`;
      } else {
          alert('Error: ' + data.message);
      }
  });
});


document.getElementById('blockUser').addEventListener('click', function() {
    const otherUserId = '{{ other_user_id }}';
    const action = 'block';
    const url = "{% url 'users:blocking' %}";
    const csrftoken = getCookie('csrftoken');

    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        credentials: 'same-origin',
        body: JSON.stringify({
            'user_id': otherUserId,
            'action': action
        })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.response);
        // Optionally disable input fields or redirect
        document.querySelector("#id_message_send_input").disabled = true;
        document.querySelector("#id_message_send_button").disabled = true;

        // Optionally, redirect to the chat home or another page
        // window.location.href = "{% url 'chat:home' %}";
    })
    .catch((error) => {
        console.error('Error:', error);
    });
});

// Function to get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i=0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length+1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length+1));
                break;
            }
        }
    }
    return cookieValue;
}

updateChatHeader();
