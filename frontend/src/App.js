import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleFileChange = (event) => {
    setFiles(event.target.files);
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      alert('Please select files to upload.');
      return;
    }

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }

    setUploading(true);
    setProgress(0);

    const newTab = window.open();
    newTab.document.write('<h1>Generating document...</h1>');

    try {
      const response = await axios.post('http://localhost:8000/upload-images/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setProgress(percentCompleted);
        },
      });

      newTab.document.open();
      newTab.document.write(response.data);
      newTab.document.close();

    } catch (error) {
      console.error('Error uploading files:', error);
      newTab.document.write('<h1>An error occurred. Please check the console for details.</h1>');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Doc Creation Agent</h1>
        <p>Upload screenshots of a technical issue and its resolution to generate a Confluence document.</p>

        <div className="upload-section">
          <input type="file" multiple onChange={handleFileChange} />
          <button onClick={handleUpload} disabled={uploading}>
            {uploading ? `Uploading... ${progress}%` : 'Upload and Analyze'}
          </button>
        </div>

        {uploading && (
          <div className="progress-bar-container">
            <div className="progress-bar" style={{ width: `${progress}%` }}></div>
          </div>
        )}
      </header>
    </div>
  );
}

export default App;
