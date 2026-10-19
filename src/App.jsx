import {
  useRef,
  useState
} from "react";

import axios from "axios";

import {
  BrowserRouter,
  Routes,
  Route,
  Navigate
} from "react-router-dom";

import AdminLogin from "./components/AdminLogin.jsx";
import AdminDashboard from "./pages/AdminDashboard.jsx";
import AdminPredictions from "./pages/AdminPredictions.jsx";
import AdminUsers from "./pages/AdminUsers.jsx";

import Login from "./components/Login.jsx";
import Register from "./components/Register.jsx";

import {
  FontAwesomeIcon
} from "@fortawesome/react-fontawesome";

import {
  faMagnifyingGlass,
  faArrowUp,
  faFilm,
  faLightbulb,
  faTriangleExclamation,
  faRotateRight,
  faArrowRight,
  faCheck,
  faFileLines
} from "@fortawesome/free-solid-svg-icons";

import "./App.css";


/* ============================================================
   BACKEND
============================================================ */

const API_BASE_URL = "http://127.0.0.1:8000";


/* ============================================================
   NORMAL DETECTION APPLICATION
============================================================ */

function DetectionApp() {

  /* ==========================================================
     VIDEO DETECTION STATE
  ========================================================== */

  const [selectedFile, setSelectedFile] = useState(null);
  const [videoPreview, setVideoPreview] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fileInputRef = useRef(null);


  /* ==========================================================
     TEXT DETECTION STATE
  ========================================================== */

  const [textInput, setTextInput] = useState("");
  const [textPrediction, setTextPrediction] = useState(null);
  const [textLoading, setTextLoading] = useState(false);
  const [textError, setTextError] = useState("");


  /* ==========================================================
     AUTH TOKEN
  ========================================================== */

  const getAuthToken = () => {

    return (
      localStorage.getItem("access_token") ||
      localStorage.getItem("token")
    );

  };


  /* ==========================================================
     FILE SELECTION
  ========================================================== */

  const handleFileChange = (event) => {

    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    setError("");
    setPrediction(null);
    setSelectedFile(file);

    if (videoPreview) {
      URL.revokeObjectURL(videoPreview);
    }

    const previewUrl = URL.createObjectURL(file);

    setVideoPreview(previewUrl);
  };


  /* ==========================================================
     REMOVE VIDEO
  ========================================================== */

  const handleRemoveVideo = () => {

    if (videoPreview) {
      URL.revokeObjectURL(videoPreview);
    }

    setSelectedFile(null);
    setVideoPreview(null);
    setPrediction(null);
    setError("");

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };


  /* ==========================================================
     ANALYZE VIDEO
  ========================================================== */

  const handleAnalyze = async () => {

    if (!selectedFile) {

      setError(
        "Please select a video before starting the analysis."
      );

      return;
    }

    setLoading(true);
    setError("");
    setPrediction(null);

    try {

      const formData = new FormData();

      formData.append(
        "video",
        selectedFile
      );

      console.log("");
      console.log("====================================");
      console.log("STARTING FRONTEND VIDEO ANALYSIS");
      console.log("====================================");

      const token = getAuthToken();

      const requestConfig = {
        headers: {
          "Content-Type": "multipart/form-data"
        }
      };

      if (token) {

        requestConfig.headers.Authorization =
          `Bearer ${token}`;

      }

      const response = await axios.post(
        `${API_BASE_URL}/api/predictions/predict`,
        formData,
        requestConfig
      );

      console.log("FULL VIDEO BACKEND RESPONSE");
      console.log(response.data);

      if (!response.data?.success) {

        throw new Error(
          "Backend did not return a successful prediction."
        );

      }

      if (!response.data?.prediction) {

        throw new Error(
          "Prediction data was not returned by the backend."
        );

      }

      setPrediction(
        response.data.prediction
      );

    }

    catch (err) {

      console.error(
        "Video prediction request failed:",
        err
      );

      let message =
        "Unable to analyze the video.";

      if (err.response?.data?.detail) {

        message =
          typeof err.response.data.detail === "string"
            ? err.response.data.detail
            : "Unable to analyze the video.";

      }

      else if (err.message) {

        message =
          err.message;

      }

      setError(message);

    }

    finally {

      setLoading(false);

    }

  };


  /* ==========================================================
     ANALYZE DIRECT TEXT
  ========================================================== */

  const handleTextAnalyze = async () => {

    const cleanedText = textInput.trim();

    if (!cleanedText) {

      setTextError(
        "Please enter some news text before starting the analysis."
      );

      return;
    }

    setTextLoading(true);
    setTextError("");
    setTextPrediction(null);

    console.log("");
    console.log("====================================");
    console.log("STARTING DIRECT TEXT ANALYSIS");
    console.log("====================================");
    console.log("Text length:", cleanedText.length);

    try {

      const token = getAuthToken();

      const requestConfig = {
        headers: {
          "Content-Type": "application/json"
        }
      };

      if (token) {

        requestConfig.headers.Authorization =
          `Bearer ${token}`;

      }

      const response = await axios.post(
        `${API_BASE_URL}/api/predictions/text-predict`,
        {
          text: cleanedText
        },
        requestConfig
      );

      console.log("FULL TEXT BACKEND RESPONSE");
      console.log(response.data);

      if (!response.data?.success) {

        throw new Error(
          "Backend did not return a successful text prediction."
        );

      }

      if (!response.data?.prediction) {

        throw new Error(
          "Text prediction data was not returned by the backend."
        );

      }

      setTextPrediction(
        response.data.prediction
      );

    }

    catch (err) {

      console.error(
        "Text prediction request failed:",
        err
      );

      let message =
        "Unable to analyze the text.";

      if (err.response?.data?.detail) {

        if (Array.isArray(err.response.data.detail)) {

          message =
            err.response.data.detail
              .map((item) => item.msg)
              .join(", ");

        }

        else if (
          typeof err.response.data.detail === "string"
        ) {

          message =
            err.response.data.detail;

        }

      }

      else if (err.message) {

        message =
          err.message;

      }

      setTextError(message);

    }

    finally {

      setTextLoading(false);

    }

  };


  /* ==========================================================
     CLEAR TEXT
  ========================================================== */

  const handleClearText = () => {

    setTextInput("");
    setTextPrediction(null);
    setTextError("");
    setTextLoading(false);

  };


  /* ==========================================================
     ANALYZE ANOTHER VIDEO
  ========================================================== */

  const handleAnalyzeAnother = () => {

    if (videoPreview) {
      URL.revokeObjectURL(videoPreview);
    }

    setSelectedFile(null);
    setVideoPreview(null);
    setPrediction(null);
    setError("");
    setLoading(false);

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }

    window.scrollTo({
      top: 0,
      behavior: "smooth"
    });

  };


  /* ==========================================================
     FORMAT PERCENTAGE
  ========================================================== */

  const formatPercentage = (value) => {

    const number = Number(value);

    if (Number.isNaN(number)) {
      return "0.00%";
    }

    return `${(
      number * 100
    ).toFixed(2)}%`;

  };


  /* ==========================================================
     DETECTED VIDEO PROBABILITY
  ========================================================== */

  const detectedProbability = () => {

    if (!prediction) {
      return 0;
    }

    if (
      String(
        prediction.label
      ).toUpperCase() === "FAKE"
    ) {

      return prediction.fake_probability;

    }

    return prediction.real_probability;

  };


  /* ==========================================================
     DETECTED TEXT PROBABILITY
  ========================================================== */

  const textDetectedProbability = () => {

    if (!textPrediction) {
      return 0;
    }

    if (
      String(
        textPrediction.label
      ).toUpperCase() === "FAKE"
    ) {

      return textPrediction.fake_probability;

    }

    return textPrediction.real_probability;

  };


  /* ==========================================================
     VIDEO EXPLANATIONS
  ========================================================== */

  const explanations =
    prediction?.explanations || {};

  const shap =
    explanations.shap || {};

  const gradcam =
    explanations.gradcam || {};


  /* ==========================================================
     GRAD-CAM URL
  ========================================================== */

  const getGradcamUrl = (url) => {

    if (!url) {
      return "";
    }

    if (
      url.startsWith("http://") ||
      url.startsWith("https://")
    ) {

      return url;

    }

    return `${API_BASE_URL}${url}`;

  };


  /* ==========================================================
     VIDEO HUMAN EXPLANATION
  ========================================================== */

  const humanExplanation =
    prediction?.human_readable_explanation ||
    prediction?.reason ||
    explanations.human_readable_explanation ||
    explanations.reason ||
    "No human-readable explanation was provided.";


  /* ==========================================================
     VIDEO EVIDENCE TYPE
  ========================================================== */

  const evidenceType =
    explanations.evidence_type ||
    "NOT AVAILABLE";


  /* ==========================================================
     TEXT HUMAN EXPLANATION
  ========================================================== */

  const textHumanExplanation =
    textPrediction?.human_readable_explanation ||
    textPrediction?.reason ||
    "The entered text was classified by the dedicated BERT + Text XGBoost detector.";


  /* ==========================================================
     RENDER DETECTION APP
  ========================================================== */

  return (

    <div className="app">

      {/* ======================================================
          HEADER
      ====================================================== */}

      <header className="header">

        <div className="header-inner">

          <div className="brand">

            <div className="brand-icon">

              <FontAwesomeIcon
                icon={faMagnifyingGlass}
              />

            </div>

            <div>

              <h1>
                TruthLens
              </h1>

              <p>
                Multimodal Fake News Video Detection
              </p>

            </div>

          </div>


          <div className="header-status">

            <span className="status-dot"></span>

            AI Detection System

          </div>

        </div>

      </header>


      {/* ======================================================
          MAIN
      ====================================================== */}

      <main className="container">

        {/* ====================================================
            VIDEO UPLOAD CARD
        ==================================================== */}

        <section className="upload-card">

          <div className="section-heading">

            <div>

              <h2>
                Upload a Video
              </h2>

              <p className="description">

                Upload a news video to analyze its
                visual and spoken content using our
                multimodal detection pipeline.

              </p>

            </div>

          </div>


          {/* ==================================================
              UPLOAD AREA
          ================================================== */}

          {!selectedFile && (

            <label
              className="upload-area"
              htmlFor="video-upload"
            >

              <input
                ref={fileInputRef}
                id="video-upload"
                type="file"
                accept="video/*"
                onChange={handleFileChange}
              />

              <div className="upload-icon">

                <FontAwesomeIcon
                  icon={faArrowUp}
                />

              </div>

              <strong>
                Click to upload a video
              </strong>

              <span>
                MP4, AVI, MOV, MKV or WEBM
              </span>

            </label>

          )}


          {/* ==================================================
              SELECTED FILE
          ================================================== */}

          {selectedFile && (

            <div className="selected-file">

              <div className="file-information">

                <div className="file-icon">

                  <FontAwesomeIcon
                    icon={faFilm}
                  />

                </div>

                <div>

                  <strong>
                    {selectedFile.name}
                  </strong>

                  <p>

                    {(
                      selectedFile.size /
                      (1024 * 1024)
                    ).toFixed(2)}

                    {" MB"}

                  </p>

                </div>

              </div>

              <button
                type="button"
                className="remove-button"
                onClick={handleRemoveVideo}
              >

                Remove

              </button>

            </div>

          )}


          {/* ==================================================
              VIDEO PREVIEW
          ================================================== */}

          {videoPreview && (

            <div className="video-preview">

              <h3>
                Video Preview
              </h3>

              <video
                src={videoPreview}
                controls
              />

            </div>

          )}


          {/* ==================================================
              ANALYZE VIDEO BUTTON
          ================================================== */}

          <button
            type="button"
            className="analyze-button"
            onClick={handleAnalyze}
            disabled={
              !selectedFile ||
              loading
            }
          >

            {loading ? (

              <>

                <span className="button-spinner"></span>

                Analyzing Video...

              </>

            ) : (

              <>

                Analyze Video

                <span className="button-arrow">

                  <FontAwesomeIcon
                    icon={faArrowRight}
                  />

                </span>

              </>

            )}

          </button>


          {/* ==================================================
              VIDEO ERROR
          ================================================== */}

          {error && (

            <div className="error">

              <strong>
                Analysis Error
              </strong>

              <p>
                {error}
              </p>

            </div>

          )}


          {/* ==================================================
              VIDEO LOADING
          ================================================== */}

          {loading && (

            <div className="loading">

              <div className="spinner"></div>

              <strong>
                Analyzing your video
              </strong>

              <p>
                Whisper, BERT, ResNet50 and XGBoost
                are processing the video.
              </p>

            </div>

          )}

        </section>


        {/* ====================================================
            TEXT-BASED DETECTION CARD
        ==================================================== */}

        <section className="text-detection-card">

          <div className="section-heading">

            <div>

              <span className="detection-mode-label text-mode">
                TEXT-BASED DETECTION
              </span>

              <h2>
                Analyze Text
              </h2>

              <p className="description">

                Enter news text directly to analyze its
                textual patterns using BERT and a dedicated
                Text XGBoost classifier.

              </p>

            </div>

          </div>


          {/* ==================================================
              TEXT INPUT
          ================================================== */}

          <div className="text-input-wrapper">

            <label
              htmlFor="news-text"
              className="text-input-label"
            >
              News Text
            </label>

            <textarea
              id="news-text"
              className="news-textarea"
              value={textInput}
              onChange={(event) => {

                setTextInput(
                  event.target.value
                );

                setTextError("");

              }}
              placeholder="Enter the news text you want to analyze..."
              rows={9}
              disabled={textLoading}
            />

            <div className="text-input-footer">

              <span>
                {textInput.length} characters
              </span>

       

            </div>

          </div>


          {/* ==================================================
              TEXT ACTION BUTTONS
          ================================================== */}

          <div className="text-action-row">

            <button
              type="button"
              className="text-analyze-button"
              onClick={handleTextAnalyze}
              disabled={
                !textInput.trim() ||
                textLoading
              }
            >

              {textLoading ? (

                <>

                  <span className="button-spinner"></span>

                  Analyzing Text...

                </>

              ) : (

                <>

                  Analyze Text

                  <span className="button-arrow">

                    <FontAwesomeIcon
                      icon={faArrowRight}
                    />

                  </span>

                </>

              )}

            </button>


            <button
              type="button"
              className="text-clear-button"
              onClick={handleClearText}
              disabled={
                textLoading ||
                (
                  !textInput &&
                  !textPrediction &&
                  !textError
                )
              }
            >

              Clear

            </button>

          </div>


          {/* ==================================================
              TEXT ERROR
          ================================================== */}

          {textError && (

            <div className="error text-error">

              <strong>
                Text Analysis Error
              </strong>

              <p>
                {textError}
              </p>

            </div>

          )}


          {/* ==================================================
              TEXT LOADING
          ================================================== */}

          {textLoading && (

            <div className="loading text-loading">

              <div className="spinner"></div>

              <strong>
                Analyzing your text
              </strong>

              <p>
                BERT is extracting 768-dimensional text
                features and Text XGBoost is classifying
                the entered content.
              </p>

            </div>

          )}

        </section>


        {/* ====================================================
            TEXT RESULT CARD
        ==================================================== */}

        {textPrediction && (

          <section className="text-result-card">

            <div className="result-header">

              <div>

                <span className="detection-mode-label text-mode">
                  TEXT-BASED DETECTION
                </span>

                <h2>
                  Text Detection Result
                </h2>

                <p className="description">

                  The dedicated text-only detector has
                  completed the analysis of the entered text.

                </p>

              </div>

              <div className="result-complete">

                <FontAwesomeIcon
                  icon={faCheck}
                />

                {" "}Analysis Complete

              </div>

            </div>


            {/* =================================================
                TEXT DETECTION PANEL
            ================================================= */}

            <div
              className={
                `detection-panel ${
                  String(
                    textPrediction.label
                  ).toUpperCase() === "FAKE"
                    ? "fake"
                    : "real"
                }`
              }
            >

              <div className="detection-main">

                <span className="detection-caption">
                  TEXT DETECTION
                </span>

                <div className="detection-label">

                  {String(
                    textPrediction.label
                  ).toUpperCase()}

                </div>

                <p>
                  Classified using BERT + Text XGBoost
                </p>

              </div>


              <div className="detection-probability">

                <span>
                  Detection Probability
                </span>

                <strong>
                  {formatPercentage(
                    textDetectedProbability()
                  )}
                </strong>

                <small>

                  {String(
                    textPrediction.label
                  ).toUpperCase()}

                  {" "}probability

                </small>

              </div>

            </div>


            {/* =================================================
                TEXT EXPLANATION
            ================================================= */}

            <div
              className={
                `human-explanation ${
                  String(
                    textPrediction.label
                  ).toUpperCase() === "FAKE"
                    ? "fake-explanation"
                    : "real-explanation"
                }`
              }
            >

              <div className="explanation-title">

                <span className="explanation-icon">

                  <FontAwesomeIcon
                    icon={faLightbulb}
                  />

                </span>

                <h3>
                  Text Analysis Explanation
                </h3>

              </div>

              <p>
                {textHumanExplanation}
              </p>

            </div>


            {/* =================================================
                TEXT MODEL INFORMATION
            ================================================= */}

            <div className="text-model-info">

              <div className="technical-title">

                <div>

                 {/* <span className="technical-kicker">
                    TEXT PIPELINE
                  </span>

                  <h3>
                    Model Information
                  </h3>

                </div>

              </div>


              <div className="info-grid">

                <div>

                  <span>
                    Input Type
                  </span>

                  <strong>
                    Direct Text
                  </strong>

                </div>


                <div>

                  <span>
                    Text Model
                  </span>

                  <strong>
                    BERT
                  </strong>

                </div>


                <div>

                  <span>
                    Text Features
                  </span>

                  <strong>
                    {
                      textPrediction.feature_dimensions?.bert ??
                      textPrediction.text_feature_dimension ??
                      768
                    }
                  </strong>

                </div>


                <div>

                  <span>
                    Classifier
                  </span>

                  <strong>
                    Text XGBoost
                  </strong>

                </div>


                <div>

                  <span>
                    Real Probability
                  </span>

                  <strong>
                    {formatPercentage(
                      textPrediction.real_probability
                    )}
                  </strong>

                </div>


                <div>

                  <span>
                    Fake Probability
                  </span>

                  <strong>
                    {formatPercentage(
                      textPrediction.fake_probability
                    )}
                  </strong>

                </div>


                <div>

                  <span>
                    Confidence
                  </span>

                  <strong>
                    {formatPercentage(
                      textPrediction.confidence
                    )}
                  </strong>

                </div>


                <div>

                  <span>
                    Fake Threshold
                  </span>

                  <strong>
                    {Number(
                      textPrediction.threshold ?? 0.39
                    ).toFixed(2)}
                  </strong>
                 */}
                </div>

              </div>

            </div>


            {/* =================================================
                ANALYZED TEXT
            ================================================= */}

            <div className="analyzed-text-section">

              <div className="technical-title">

                <div>

                  <span className="technical-kicker">
                    TEXT INPUT
                  </span>

                  <h3>
                    Analyzed Text
                  </h3>

                </div>

              </div>


              <div className="analyzed-text-box">

                <FontAwesomeIcon
                  icon={faFileLines}
                  className="analyzed-text-icon"
                />

                <p>
                  {textPrediction.input_text ||
                    textInput}
                </p>

              </div>

            </div>


            {/* =================================================
                CLEAR TEXT RESULT
            ================================================= */}

            <div className="text-result-actions">

              <button
                type="button"
                className="text-clear-result-button"
                onClick={handleClearText}
              >

                <FontAwesomeIcon
                  icon={faRotateRight}
                />

                Analyze Another Text

              </button>

            </div>

          </section>

        )}


        {/* ====================================================
            VIDEO RESULT CARD
        ==================================================== */}

        {prediction && (

          <section className="result-card">

            <div className="result-header">

              <div>

                <h2>
                  Detection Result
                </h2>

                <p className="description">

                  The model has completed the
                  multimodal analysis of your video.

                </p>

              </div>

              <div className="result-complete">

                <FontAwesomeIcon
                  icon={faCheck}
                />

                {" "}Analysis Complete

              </div>

            </div>


            {/* =================================================
                DETECTION PANEL
            ================================================= */}

            <div
              className={
                `detection-panel ${
                  String(
                    prediction.label
                  ).toUpperCase() === "FAKE"
                    ? "fake"
                    : "real"
                }`
              }
            >

              <div className="detection-main">

                <span className="detection-caption">
                  DETECTION
                </span>

                <div className="detection-label">

                  {String(
                    prediction.label
                  ).toUpperCase()}

                </div>

                <p>
                  Detected classification
                </p>

              </div>


              <div className="detection-probability">

                <span>
                  Detection Probability
                </span>

                <strong>
                  {formatPercentage(
                    detectedProbability()
                  )}
                </strong>

                <small>

                  {String(
                    prediction.label
                  ).toUpperCase()}

                  {" "}probability

                </small>

              </div>

            </div>


            {/* =================================================
                HUMAN EXPLANATION
            ================================================= */}

            <div
              className={
                `human-explanation ${
                  String(
                    prediction.label
                  ).toUpperCase() === "FAKE"
                    ? "fake-explanation"
                    : "real-explanation"
                }`
              }
            >

              <div className="explanation-title">

                <span className="explanation-icon">

                  <FontAwesomeIcon
                    icon={faLightbulb}
                  />

                </span>

                <h3>
                  Why was this video classified this way?
                </h3>

              </div>

              <p>
                {humanExplanation}
              </p>

            </div>


            {/* =================================================
                TECHNICAL DETAILS
            ================================================= */}

            <details className="technical-details">

              <summary className="technical-summary">

                <span>
                  Technical Details
                </span>

                <span className="summary-hint">
                  SHAP • Evidence • Grad-CAM • Model
                </span>

              </summary>


              <div className="technical-content">

                {/* =============================================
                    EVIDENCE
                ============================================= */}

                <div className="evidence-section">

                  <div className="technical-title">

                    <div>

                      <span className="technical-kicker">
                        EXPLAINABILITY
                      </span>

                      <h3>
                        Evidence Analysis
                      </h3>

                    </div>

                  </div>


                  <div className="evidence-grid">

                    <div className="evidence-box">

                      <span>
                        Evidence Type
                      </span>

                      <strong
                        className={
                          `evidence-value evidence-${String(
                            evidenceType
                          )
                            .toLowerCase()
                            .replace(
                              /\s+/g,
                              "-"
                            )}`
                        }
                      >

                        {evidenceType}

                      </strong>

                    </div>


                    <div className="evidence-box">

                      <span>
                        Visual Contribution
                      </span>

                      <strong>

                        {Number(
                          explanations.visual_contribution || 0
                        ).toFixed(2)}

                        %

                      </strong>

                    </div>


                    <div className="evidence-box">

                      <span>
                        Text Contribution
                      </span>

                      <strong>

                        {Number(
                          explanations.text_contribution || 0
                        ).toFixed(2)}

                        %

                      </strong>

                    </div>

                  </div>


                  {explanations.explanation_note && (

                    <div className="evidence-note">

                      {explanations.explanation_note}

                    </div>

                  )}

                </div>


                {/* =============================================
                    SHAP
                ============================================= */}

                <div className="shap-section">

                  <div className="technical-title">

                    <div>

                      <span className="technical-kicker">
                        FEATURE ATTRIBUTION
                      </span>

                      <h3>
                        SHAP Explanation
                      </h3>

                    </div>

                    <span
                      className={
                        shap.available
                          ? "availability available"
                          : "availability unavailable"
                      }
                    >

                      {shap.available
                        ? "Available"
                        : "Not Available"}

                    </span>

                  </div>


                  {shap.available ? (

                    <>

                      <div className="shap-modality-grid">

                        <div className="shap-modality-box">

                          <span>
                            Visual Contribution
                          </span>

                          <strong>

                            {Number(
                              shap.visual_percentage || 0
                            ).toFixed(2)}

                            %

                          </strong>

                          <div className="progress-bar">

                            <div
                              className="progress-fill visual"
                              style={{
                                width:
                                  `${Math.min(
                                    Number(
                                      shap.visual_percentage || 0
                                    ),
                                    100
                                  )}%`
                              }}
                            />

                          </div>

                        </div>


                        <div className="shap-modality-box">

                          <span>
                            Text Contribution
                          </span>

                          <strong>

                            {Number(
                              shap.text_percentage || 0
                            ).toFixed(2)}

                            %

                          </strong>

                          <div className="progress-bar">

                            <div
                              className="progress-fill text"
                              style={{
                                width:
                                  `${Math.min(
                                    Number(
                                      shap.text_percentage || 0
                                    ),
                                    100
                                  )}%`
                              }}
                            />

                          </div>

                        </div>


                        <div className="shap-modality-box">

                          <span>
                            Dominant Modality
                          </span>

                          <strong>
                            {shap.dominant_modality || "-"}
                          </strong>

                        </div>

                      </div>


                      {Array.isArray(
                        shap.top_features
                      ) &&
                      shap.top_features.length > 0 && (

                        <div className="shap-features">

                          <h4>
                            Top Contributing Features
                          </h4>


                          {shap.top_features.map(
                            (
                              feature,
                              index
                            ) => (

                              <div
                                className="shap-feature"
                                key={
                                  feature.feature_index ??
                                  index
                                }
                              >

                                <div className="shap-feature-left">

                                  <span className="feature-rank">

                                    #{feature.rank || index + 1}

                                  </span>

                                  <div>

                                    <span className="shap-feature-name">

                                      {feature.feature ||
                                        "Feature"}

                                    </span>

                                    <small>

                                      {feature.modality ||
                                        "-"}

                                    </small>

                                  </div>

                                </div>


                                <div className="shap-feature-right">

                                  <span
                                    className={
                                      feature.direction ===
                                      "FAKE"
                                        ? "shap-fake"
                                        : feature.direction ===
                                          "REAL"
                                        ? "shap-real"
                                        : ""
                                    }
                                  >

                                    {feature.direction ||
                                      "NEUTRAL"}

                                  </span>

                                  <strong>

                                    {Number(
                                      feature.shap_value || 0
                                    ).toFixed(6)}

                                  </strong>

                                </div>

                              </div>

                            )
                          )}

                        </div>

                      )}

                    </>

                  ) : (

                    <div className="technical-unavailable">

                      SHAP explanation is not available
                      for this analysis.

                    </div>

                  )}

                </div>


                {/* =============================================
                    GRAD-CAM
                ============================================= */}

                <div className="gradcam-section">

                  <div className="technical-title">

                    <div>

                      <span className="technical-kicker">
                        VISUAL EXPLAINABILITY
                      </span>

                      <h3>
                        Grad-CAM Evidence
                      </h3>

                    </div>

                    <span
                      className={
                        gradcam.available
                          ? "availability available"
                          : "availability unavailable"
                      }
                    >

                      {gradcam.available
                        ? "Available"
                        : "Not Available"}

                    </span>

                  </div>


                  {gradcam.available ? (

                    <>

                      <div className="gradcam-info">

                        <div className="gradcam-info-box">

                          <span>
                            Target Layer
                          </span>

                          <strong>

                            {gradcam.target_layer ||
                              "ResNet50.layer4[-1]"}

                          </strong>

                        </div>


                        <div className="gradcam-info-box">

                          <span>
                            Frames Processed
                          </span>

                          <strong>

                            {gradcam.frames_processed ??
                              0}

                          </strong>

                        </div>


                        <div className="gradcam-info-box">

                          <span>
                            Average Target Score
                          </span>

                          <strong>

                            {Number(
                              gradcam.average_target_score ||
                                0
                            ).toFixed(4)}

                          </strong>

                        </div>

                      </div>


                      {Array.isArray(
                        gradcam.frames
                      ) &&
                      gradcam.frames.length > 0 ? (

                        <div className="gradcam-images">

                          {gradcam.frames.map(
                            (
                              frame,
                              index
                            ) => (

                              <div
                                className="gradcam-image-card"
                                key={
                                  `${frame.frame_number}-${index}`
                                }
                              >

                                <div className="gradcam-image-header">

                                  <strong>

                                    Frame{" "}
                                    {frame.frame_number}

                                  </strong>

                                  <span>

                                    Target probability:{" "}

                                    {formatPercentage(
                                      frame.target_probability
                                    )}

                                  </span>

                                </div>


                                <div className="gradcam-image-grid">

                                  {frame.original_url && (

                                    <div className="gradcam-image-wrapper">

                                      <img
                                        src={getGradcamUrl(
                                          frame.original_url
                                        )}
                                        alt={
                                          `Original frame ${frame.frame_number}`
                                        }
                                        loading="lazy"
                                      />

                                      <span>
                                        Original
                                      </span>

                                    </div>

                                  )}


                                  {frame.overlay_url && (

                                    <div className="gradcam-image-wrapper">

                                      <img
                                        src={getGradcamUrl(
                                          frame.overlay_url
                                        )}
                                        alt={
                                          `Grad-CAM overlay frame ${frame.frame_number}`
                                        }
                                        loading="lazy"
                                      />

                                      <span>
                                        Grad-CAM Overlay
                                      </span>

                                    </div>

                                  )}


                                  {frame.heatmap_url && (

                                    <div className="gradcam-image-wrapper">

                                      <img
                                        src={getGradcamUrl(
                                          frame.heatmap_url
                                        )}
                                        alt={
                                          `Grad-CAM heatmap frame ${frame.frame_number}`
                                        }
                                        loading="lazy"
                                      />

                                      <span>
                                        Heatmap
                                      </span>

                                    </div>

                                  )}

                                </div>


                                <div className="gradcam-score">

                                  <span>
                                    Target Score
                                  </span>

                                  <strong>

                                    {Number(
                                      frame.target_score || 0
                                    ).toFixed(4)}

                                  </strong>

                                </div>

                              </div>

                            )
                          )}

                        </div>

                      ) : (

                        <div className="technical-unavailable">

                          Grad-CAM was generated but no
                          visualization frames were returned.

                        </div>

                      )}

                    </>

                  ) : (

                    <div className="gradcam-unavailable">

                      <div className="unavailable-icon">

                        <FontAwesomeIcon
                          icon={faTriangleExclamation}
                        />

                      </div>

                      <div>

                        <strong>
                          Grad-CAM evidence is not available
                        </strong>

                        {gradcam.error && (

                          <p>
                            {gradcam.error}
                          </p>

                        )}

                      </div>

                    </div>

                  )}

                </div>


                {/* =============================================
                    MODEL INFORMATION
                ============================================= */}
{/*
                <div className="model-info">

                  <div className="technical-title">

                    <div>

                      <span className="technical-kicker">
                        PIPELINE
                      </span>

                      <h3>
                        Model Information
                      </h3>

                    </div>

                  </div>


                  <div className="info-grid">

                    <div>

                      <span>
                        Visual Model
                      </span>

                      <strong>
                        ResNet50
                      </strong>

                    </div>


                    <div>

                      <span>
                        Text Model
                      </span>

                      <strong>
                        BERT
                      </strong>

                    </div>


                    <div>

                      <span>
                        Speech Model
                      </span>

                      <strong>
                        Whisper
                      </strong>

                    </div>


                    <div>

                      <span>
                        Fusion Model
                      </span>

                      <strong>
                        XGBoost
                      </strong>

                    </div>


                    <div>

                      <span>
                        Visual Features
                      </span>

                      <strong>
                        {prediction.visual_feature_dimension ??
                          2048}
                      </strong>

                    </div>


                    <div>

                      <span>
                        Text Features
                      </span>

                      <strong>
                        {prediction.text_feature_dimension ??
                          768}
                      </strong>

                    </div>


                    <div>

                      <span>
                        Fusion Features
                      </span>

                      <strong>
                        {prediction.fusion_feature_dimension ??
                          2816}
                      </strong>

                    </div>


                    <div>

                      <span>
                        Fake Threshold
                      </span>

                      <strong>
                        {Number(
                          prediction.threshold ?? 0.3
                        ).toFixed(2)}
                      </strong>

                    </div>

                  </div>

                </div>*/}


                {/* =============================================
                    TRANSCRIPT
                ============================================= */}

                <div className="transcript">

                  <div className="technical-title">

                    <div>

                      <span className="technical-kicker">
                        SPEECH ANALYSIS
                      </span>

                      <h3>
                        Extracted Transcript
                      </h3>

                    </div>

                  </div>


                  <div className="transcript-box">

                    {prediction.transcript ||
                      "No transcript was returned."}

                  </div>

                </div>

              </div>

            </details>


            {/* =================================================
                ANALYZE ANOTHER
            ================================================= */}

            <div className="analyze-another-wrapper">

              <button
                type="button"
                className="analyze-another-button"
                onClick={handleAnalyzeAnother}
              >

                <span>

                  <FontAwesomeIcon
                    icon={faRotateRight}
                  />

                </span>

                Analyze Another Video

              </button>

            </div>

          </section>

        )}

      </main>


      {/* ======================================================
          FOOTER
      ====================================================== */}

      <footer>

        <p>
          TruthLens — Multimodal Fake News Video Detection
        </p>

     

      </footer>

    </div>

  );

}


/* ============================================================
   MAIN APPLICATION ROUTER
============================================================ */

function App() {

  return (

    <BrowserRouter>

      <Routes>

        {/* ==================================================
            USER LOGIN
        ================================================== */}

        <Route
          path="/login"
          element={
            <Login />
          }
        />


        {/* ==================================================
            USER REGISTER
        ================================================== */}

        <Route
          path="/register"
          element={
            <Register />
          }
        />


        {/* ==================================================
            USER HOME / DETECTION
        ================================================== */}

        <Route
          path="/home"
          element={
            <DetectionApp />
          }
        />


        {/* ==================================================
            ROOT
        ================================================== */}

        <Route
          path="/"
          element={
            <Navigate
              to="/login"
              replace
            />
          }
        />


        {/* ==================================================
            ADMIN LOGIN
        ================================================== */}

        <Route
          path="/admin/login"
          element={
            <AdminLogin />
          }
        />


        {/* ==================================================
            ADMIN ROOT
        ================================================== */}

        <Route
          path="/admin"
          element={
            <Navigate
              to="/admin/dashboard"
              replace
            />
          }
        />


        {/* ==================================================
            ADMIN DASHBOARD
        ================================================== */}

        <Route
          path="/admin/dashboard"
          element={
            <AdminDashboard />
          }
        />


        {/* ==================================================
            ADMIN PREDICTIONS
        ================================================== */}

        <Route
          path="/admin/predictions"
          element={
            <AdminPredictions />
          }
        />


        {/* ==================================================
            ADMIN USERS
        ================================================== */}

        <Route
          path="/admin/users"
          element={
            <AdminUsers />
          }
        />


        {/* ==================================================
            UNKNOWN ROUTES
        ================================================== */}

        <Route
          path="*"
          element={
            <Navigate
              to="/login"
              replace
            />
          }
        />

      </Routes>

    </BrowserRouter>

  );

}


export default App;