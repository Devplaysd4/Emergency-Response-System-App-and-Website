const loginForm = document.getElementById("loginForm");
const errorMsg = document.getElementById("error-msg");

// Hardcoded credentials
const USERNAME = "admin";
const PASSWORD = "1234";

loginForm.addEventListener("submit", function(e) {
  e.preventDefault();
  
  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;
  
  if(username === USERNAME && password === PASSWORD) {
    // correct credentials → go to admin portal
    window.location.href = "admin.html";
  } else {
    errorMsg.textContent = "Incorrect username or password!";
  }
});
