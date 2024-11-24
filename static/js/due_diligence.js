document
.getElementById("drop-area")
.addEventListener("dragover", function (event) {
  event.preventDefault(); // Prevent default behavior
});

document
.getElementById("drop-area")
.addEventListener("dragleave", function (event) {
  // Optional: You can add additional UI changes here if you want
});

document
.getElementById("drop-area")
.addEventListener("drop", function (event) {
  event.preventDefault(); // Prevent default behavior and stop propagation

  const files = event.dataTransfer.files; // Get the files from the drop event
  if (files.length > 0) {
    // Set the file to the input
    document.getElementById("file-input").files = files;
    handleFileSelect(); // Call your existing file selection handler
  }
});

// Your existing handleFileSelect function
function handleFileSelect() {
var uploadButton = document.getElementById("upload-button");
uploadButton.disabled = true; // Disable the button
uploadButton.style.backgroundColor = "#ccc"; // Change color to indicate disabled
uploadButton.style.cursor = "not-allowed"; // Change cursor to not-allowed

// Show initial upload status message
// document.getElementById('status').innerHTML = 'Uploading file...';

// Submit the form
document.getElementById("upload-form").submit();
}

function updateStatus() {
fetch("/get_processing_status") // Endpoint to get the session status
  .then((response) => {
    if (!response.ok) {
      throw new Error("Network response was not ok");
    }
    return response.json();
  })
  .then((data) => {
    console.log("Received status data:", data); // Log fetched data for debugging
    const statusElement = document.getElementById("status");
    statusElement.innerHTML = ""; // Clear previous status
    if (data.status.length === 0) {
      statusElement.innerHTML = "No status updates available.";
    } else {
      data.status.forEach((item) => {
        statusElement.innerHTML += `<p>${item}</p>`;
      });
    }
  })
  .catch((error) => {
    console.error("Error fetching status:", error);
    const statusElement = document.getElementById("status");
    statusElement.innerHTML = "Error fetching status updates.";
  });
}

setInterval(updateStatus, 2000); // Poll every 2 seconds