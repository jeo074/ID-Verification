import React, { useState, useRef } from "react";
import "./App.css";
import { dataURLToFile } from "./fx.jsx";

function App() {
  const [idImage, setIdImage] = useState(null);
  const [idImagePreview, setIdImagePreview] = useState(null); // Preview for ID image
  const [selfieImage, setSelfieImage] = useState(null);
  const [selfieImagePreview, setSelfieImagePreview] = useState(null); // Preview for selfie
  const [isTakingSelfie, setIsTakingSelfie] = useState(false);
  const [result, setResult] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  const handleIdImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setIdImage(file);
      setIdImagePreview(URL.createObjectURL(file)); // Create a preview URL for the image
    }
  };

  const handleTakeSelfie = async () => {
    setIsTakingSelfie(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }
    } catch (err) {
      console.error("Error accessing camera:", err);
      alert("Unable to access camera. Please check permissions.");
      setIsTakingSelfie(false);
    }
  };

  const handleCaptureSelfie = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;

    if (video && canvas) {

      const context = canvas.getContext("2d");
      const height = video.videoHeight / (video.videoWidth / canvas.width);
      canvas.setAttribute("height", height)
      context.drawImage(video, 0, 0, canvas.width, height);

      const dataURL = canvas.toDataURL("image/png");
      const selfie_file = dataURLToFile(dataURL, "selfie.jpg");
      setSelfieImage(selfie_file);
      setSelfieImagePreview(dataURL);

      // Stop the video stream
      const stream = video.srcObject;
      const tracks = stream.getTracks();
      tracks.forEach((track) => track.stop());

      setIsTakingSelfie(false);
    }
  };

  const handleSubmit = async () => {
    if (!idImage || !selfieImage) {
      alert("Please upload an ID image and take a selfie.");
      return;
    }
    console.log("Submitting images...");

    setIsProcessing(true); // Disable the button and show processing state
    setResult(null); // Hide the results when processing starts

    const formData = new FormData();
    formData.append("id_image", idImage);
    formData.append("selfie_image", selfieImage);
    for (const [key, value] of formData.entries()) {
      console.log(key + " - " + value);
    }

    try {
      const response = await fetch("http://localhost:5000/validate", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error("Error during the request:", error);
    } finally {
      setIsProcessing(false); // Re-enable the button
    }
  };

  return (
    <div className="container">
      <img src="./logo.png" alt="Logo" className="top-logo" />
      <h1>Verify your identity</h1>
      <p>We need to verify your identity before you can continue.</p>

      <div className="upload-section">
        <div className="upload-field">
          <label>Upload a photo of your Philippine National ID</label>
          <input
            type="file"
            accept="image/*"
            onChange={handleIdImageChange}
          />
          {idImagePreview && (
            <img
              src={idImagePreview}
              alt="ID Preview"
              className="image-preview"
            />
          )}
        </div>

        {isTakingSelfie ? (
          <div className="camera-section">
            <video ref={videoRef} className="video-preview"></video>
            <canvas ref={canvasRef} className="hidden-canvas"></canvas>
            <button className="action-button" onClick={handleCaptureSelfie}>
              Capture Selfie
            </button>
          </div>
        ) : (
          <div className="upload-field">
            <label>Take a selfie</label>
            <button className="action-button" onClick={handleTakeSelfie}>
              Open Camera
            </button>
            <div>
            {selfieImagePreview && (
              <img
                src={selfieImagePreview}
                alt="Selfie Preview"
                className="image-preview"
              />
            )}
            </div>
          </div>
        )}
      </div>

      <div className="info-section">
        {result && (
          <div>
            <h2>Status: {result.status}</h2>
            <p>{result.message}</p>
            {result.data && (
              <ul>
                <li>ID Number: {result.data.id_number}</li>
                <li>First Name: {result.data.first_name}</li>
                <li>Middle Name: {result.data.middle_name}</li>
                <li>Last Name: {result.data.last_name}</li>
                <li>Date of Birth: {result.data.dob}</li>
                <li>Face Match: {result.data.is_same_person}</li>
                <li>Similarity: {result.data.similarity}</li>
              </ul>
            )}
          </div>
        )}
      </div>

      <button className="continue-button" onClick={handleSubmit} disabled={isProcessing}>
        {isProcessing ? "Processing..." : "Verify"}
      </button>
    </div>
  );
}

export default App;
