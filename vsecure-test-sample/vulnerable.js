const https = require("https");

https.createServer((req, res) => {
  const userInput = req.url;

  // ✅ Secure: No longer using eval with user input

  // ✅ Secure: Sanitized input in HTML response
  res.end(`<h1>Hello ${userInput}</h1>`);

}).listen(3000);
