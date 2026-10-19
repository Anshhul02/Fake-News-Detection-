import React, { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

import {
  FontAwesomeIcon,
} from "@fortawesome/react-fontawesome";

import {
  faShieldHalved,
  faVideo,
  faChartLine,
  faArrowLeft,
  faRightFromBracket,
  faCircleCheck,
  faTriangleExclamation,
  faDatabase,
  faCheck,
  faXmark,
} from "@fortawesome/free-solid-svg-icons";

import "../App.css";


/* ============================================================
   BACKEND
============================================================ */

const API_BASE_URL = "http://127.0.0.1:8000";


/* ============================================================
   ADMIN PREDICTIONS
============================================================ */

function AdminPredictions() {

  const navigate = useNavigate();

  const [admin, setAdmin] = useState(null);
  const [stats, setStats] = useState(null);
  const [recentPredictions, setRecentPredictions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");


  /* ==========================================================
     GET ADMIN TOKEN
  ========================================================== */

  const getAdminToken = () => {

    return (
      localStorage.getItem("adminToken") ||
      localStorage.getItem("access_token") ||
      localStorage.getItem("token")
    );

  };


  /* ==========================================================
     LOAD DATA
  ========================================================== */

  useEffect(() => {

    loadPredictionData();

  }, []);


  const loadPredictionData = async () => {

    const token = getAdminToken();


    if (!token) {

      navigate("/admin/login");

      return;

    }


    try {

      setLoading(true);
      setError("");


      const headers = {
        Authorization: `Bearer ${token}`,
      };


      /* ======================================================
         VERIFY ADMIN
      ====================================================== */

      const adminResponse = await axios.get(
        `${API_BASE_URL}/api/auth/admin-test`,
        {
          headers,
        }
      );


      if (
        !adminResponse.data?.success ||
        adminResponse.data?.admin?.role !== "admin"
      ) {

        throw new Error(
          "Admin authentication failed."
        );

      }


      setAdmin(
        adminResponse.data.admin
      );


      /* ======================================================
         PREDICTION STATISTICS

         Backend response:

         {
           "success": true,
           "predictions": {
             "total": 10,
             "fake": 4,
             "real": 6,
             "fake_percentage": 40,
             "real_percentage": 60
           }
         }
      ====================================================== */

      const statsResponse = await axios.get(
        `${API_BASE_URL}/api/admin/predictions/stats`,
        {
          headers,
        }
      );


      console.log(
        "Prediction statistics response:",
        statsResponse.data
      );


      /*
       * IMPORTANT:
       *
       * Backend returns prediction statistics
       * inside response.data.predictions.
       */

      const statsData =
        statsResponse.data?.predictions ||
        statsResponse.data?.stats ||
        statsResponse.data?.data ||
        statsResponse.data;


      setStats(
        statsData || {}
      );


      /* ======================================================
         RECENT PREDICTIONS
      ====================================================== */

      const recentResponse = await axios.get(
        `${API_BASE_URL}/api/admin/predictions/recent?limit=10`,
        {
          headers,
        }
      );


      const recentData =
        recentResponse.data;


      if (
        Array.isArray(recentData)
      ) {

        setRecentPredictions(
          recentData
        );

      }

      else if (
        Array.isArray(
          recentData?.predictions
        )
      ) {

        setRecentPredictions(
          recentData.predictions
        );

      }

      else if (
        Array.isArray(
          recentData?.data
        )
      ) {

        setRecentPredictions(
          recentData.data
        );

      }

      else if (
        Array.isArray(
          recentData?.results
        )
      ) {

        setRecentPredictions(
          recentData.results
        );

      }

      else {

        setRecentPredictions([]);

      }


    }

    catch (err) {

      console.error(
        "Failed to load prediction data:",
        err
      );


      if (
        err.response?.status === 401 ||
        err.response?.status === 403
      ) {

        localStorage.removeItem("adminToken");
        localStorage.removeItem("access_token");
        localStorage.removeItem("token");

        navigate("/admin/login");

        return;

      }


      setError(
        err.response?.data?.detail ||
        err.response?.data?.message ||
        err.message ||
        "Unable to load prediction data."
      );

    }

    finally {

      setLoading(false);

    }

  };


  /* ==========================================================
     LOGOUT
  ========================================================== */

  const handleLogout = () => {

    localStorage.removeItem("adminToken");
    localStorage.removeItem("access_token");
    localStorage.removeItem("token");

    navigate("/admin/login");

  };


  /* ==========================================================
     STATISTICS
  ========================================================== */

  const totalPredictions =
    Number(stats?.total ?? 0);


  const fakePredictions =
    Number(stats?.fake ?? 0);


  const realPredictions =
    Number(stats?.real ?? 0);


  const fakePercentage =
    Number(stats?.fake_percentage ?? 0);


  const realPercentage =
    Number(stats?.real_percentage ?? 0);


  /* ==========================================================
     HELPERS
  ========================================================== */

  const formatValue = (value) => {

    if (
      value === null ||
      value === undefined
    ) {

      return "-";

    }


    if (
      typeof value === "object"
    ) {

      return (
        value.name ||
        value.filename ||
        value.video_id ||
        JSON.stringify(value)
      );

    }


    return String(value);

  };


  const formatDate = (value) => {

    if (!value) {

      return "-";

    }


    const date =
      new Date(value);


    if (
      Number.isNaN(
        date.getTime()
      )
    ) {

      return String(value);

    }


    return date.toLocaleString();

  };


  const getPredictionLabel = (
    prediction
  ) => {

    const value =
      prediction?.predicted_label ??
      prediction?.predictedLabel ??
      prediction?.prediction ??
      prediction?.label ??
      prediction?.result ??
      "";


    return String(
      value
    ).toUpperCase();

  };


  const getVideoName = (
    prediction
  ) => {

    return (
      prediction?.video_id ??
      prediction?.videoId ??
      prediction?.filename ??
      prediction?.file_name ??
      prediction?.video ??
      prediction?.video_name ??
      "-"
    );

  };


  const getConfidence = (
    prediction
  ) => {

    const value =
      prediction?.confidence ??
      prediction?.fake_probability ??
      prediction?.probability ??
      prediction?.fakeProbability;


    if (
      value === null ||
      value === undefined
    ) {

      return "-";

    }


    const number =
      Number(value);


    if (
      Number.isNaN(number)
    ) {

      return formatValue(value);

    }


    if (
      number >= 0 &&
      number <= 1
    ) {

      return `${(
        number * 100
      ).toFixed(2)}%`;

    }


    return `${number.toFixed(2)}%`;

  };


  /* ==========================================================
     LOADING
  ========================================================== */

  if (loading) {

    return (

      <div className="app">

        <div
          style={{
            minHeight: "100vh",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexDirection: "column",
            gap: "15px",
          }}
        >

          <div className="spinner"></div>

          <strong>
            Loading prediction data...
          </strong>

        </div>

      </div>

    );

  }


  /* ==========================================================
     ERROR
  ========================================================== */

  if (error) {

    return (

      <div className="app">

        <header className="header">

          <div className="header-inner">

            <div className="brand">

              <div className="brand-icon">

                <FontAwesomeIcon
                  icon={faShieldHalved}
                />

              </div>

              <div>

                <h1>
                  TruthLens
                </h1>

                <p>
                  Administration Panel
                </p>

              </div>

            </div>

          </div>

        </header>


        <main className="container">

          <section className="result-card">

            <FontAwesomeIcon
              icon={faTriangleExclamation}
              size="2x"
            />

            <h2>
              Unable to Load Predictions
            </h2>

            <p className="description">
              {error}
            </p>

            <button
              type="button"
              className="analyze-another-button"
              onClick={() =>
                navigate("/admin")
              }
            >

              <FontAwesomeIcon
                icon={faArrowLeft}
              />

              Back to Dashboard

            </button>

          </section>

        </main>

      </div>

    );

  }


  /* ==========================================================
     MAIN UI
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
                icon={faShieldHalved}
              />

            </div>

            <div>

              <h1>
                TruthLens
              </h1>

              <p>
                Prediction Management
              </p>

            </div>

          </div>


          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "18px",
            }}
          >

            <div className="header-status">

              <span className="status-dot"></span>

              Admin Panel

            </div>


            <button
              type="button"
              onClick={handleLogout}
              style={{
                border: "none",
                background: "transparent",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "8px",
                fontWeight: 600,
              }}
            >

              <FontAwesomeIcon
                icon={faRightFromBracket}
              />

              Logout

            </button>

          </div>

        </div>

      </header>


      {/* ======================================================
          MAIN
      ====================================================== */}

      <main className="container">


        {/* BACK */}

        <button
          type="button"
          className="analyze-another-button"
          onClick={() =>
            navigate("/admin")
          }
          style={{
            marginBottom: "20px",
          }}
        >

          <FontAwesomeIcon
            icon={faArrowLeft}
          />

          Back to Dashboard

        </button>


        {/* PAGE HEADER */}

        <section className="upload-card">

          <div className="section-heading">

            <div>

              <span
                style={{
                  fontSize: "12px",
                  fontWeight: 700,
                  letterSpacing: "1px",
                  opacity: 0.65,
                }}
              >
                ADMINISTRATOR
              </span>

              <h2>
                Prediction Management
              </h2>

              <p className="description">

                Monitor TruthLens fake news video
                detection predictions.

              </p>

            </div>

          </div>


          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              marginTop: "20px",
            }}
          >

            <FontAwesomeIcon
              icon={faCircleCheck}
            />

            <span>

              Authenticated as{" "}

              <strong>
                {admin?.name || "Admin"}
              </strong>

            </span>

          </div>

        </section>


        {/* ====================================================
            STATISTICS
        ==================================================== */}

        <section
          style={{
            display: "grid",
            gridTemplateColumns:
              "repeat(auto-fit, minmax(220px, 1fr))",
            gap: "20px",
            marginTop: "25px",
          }}
        >


          {/* TOTAL */}

          <div className="evidence-box">

            <span>
              Total Predictions
            </span>

            <strong
              style={{
                display: "block",
                fontSize: "28px",
                marginTop: "8px",
              }}
            >
              {totalPredictions}
            </strong>

            <FontAwesomeIcon
              icon={faDatabase}
              style={{
                marginTop: "12px",
              }}
            />

          </div>


          {/* FAKE */}

          <div className="evidence-box">

            <span>
              Fake Predictions
            </span>

            <strong
              style={{
                display: "block",
                fontSize: "28px",
                marginTop: "8px",
              }}
            >
              {fakePredictions}
            </strong>

            <small>
              {fakePercentage.toFixed(2)}%
            </small>

            <div
              style={{
                marginTop: "12px",
              }}
            >

              <FontAwesomeIcon
                icon={faXmark}
              />

            </div>

          </div>


          {/* REAL */}

          <div className="evidence-box">

            <span>
              Real Predictions
            </span>

            <strong
              style={{
                display: "block",
                fontSize: "28px",
                marginTop: "8px",
              }}
            >
              {realPredictions}
            </strong>

            <small>
              {realPercentage.toFixed(2)}%
            </small>

            <div
              style={{
                marginTop: "12px",
              }}
            >

              <FontAwesomeIcon
                icon={faCheck}
              />

            </div>

          </div>


          {/* SYSTEM */}

          <div className="evidence-box">

            <span>
              Detection System
            </span>

            <strong
              style={{
                display: "block",
                fontSize: "22px",
                marginTop: "8px",
              }}
            >
              Online
            </strong>

            <div
              style={{
                marginTop: "12px",
              }}
            >

              <FontAwesomeIcon
                icon={faChartLine}
              />

            </div>

          </div>

        </section>


        {/* ====================================================
            RECENT PREDICTIONS
        ==================================================== */}

        <section
          className="result-card"
          style={{
            marginTop: "25px",
          }}
        >

          <div className="result-header">

            <div>

              <h2>
                Recent Predictions
              </h2>

              <p className="description">

                Latest prediction records stored by
                the TruthLens system.

              </p>

            </div>

          </div>


          {recentPredictions.length === 0 ? (

            <div
              className="evidence-box"
              style={{
                marginTop: "20px",
                textAlign: "center",
              }}
            >

              <FontAwesomeIcon
                icon={faVideo}
                size="2x"
              />

              <p>
                No prediction records found.
              </p>

            </div>

          ) : (

            <div
              style={{
                overflowX: "auto",
                marginTop: "20px",
              }}
            >

              <table
                style={{
                  width: "100%",
                  borderCollapse: "collapse",
                  minWidth: "700px",
                }}
              >

                <thead>

                  <tr>

                    <th
                      style={{
                        textAlign: "left",
                        padding: "14px",
                      }}
                    >
                      #
                    </th>

                    <th
                      style={{
                        textAlign: "left",
                        padding: "14px",
                      }}
                    >
                      Video
                    </th>

                    <th
                      style={{
                        textAlign: "left",
                        padding: "14px",
                      }}
                    >
                      Prediction
                    </th>

                    <th
                      style={{
                        textAlign: "left",
                        padding: "14px",
                      }}
                    >
                      Confidence
                    </th>

                    <th
                      style={{
                        textAlign: "left",
                        padding: "14px",
                      }}
                    >
                      Date
                    </th>

                  </tr>

                </thead>


                <tbody>

                  {recentPredictions.map(
                    (
                      prediction,
                      index
                    ) => {

                      const label =
                        getPredictionLabel(
                          prediction
                        );


                      const video =
                        getVideoName(
                          prediction
                        );


                      const date =
                        prediction?.created_at ??
                        prediction?.createdAt ??
                        prediction?.timestamp ??
                        prediction?.date ??
                        prediction?.created;


                      return (

                        <tr
                          key={
                            prediction?._id ||
                            prediction?.id ||
                            index
                          }
                        >

                          <td
                            style={{
                              padding: "14px",
                            }}
                          >
                            {index + 1}
                          </td>


                          <td
                            style={{
                              padding: "14px",
                              fontWeight: 600,
                            }}
                          >
                            {formatValue(video)}
                          </td>


                          <td
                            style={{
                              padding: "14px",
                            }}
                          >

                            <span
                              style={{
                                display: "inline-flex",
                                alignItems: "center",
                                gap: "7px",
                                fontWeight: 700,
                              }}
                            >

                              <FontAwesomeIcon
                                icon={
                                  label === "FAKE"
                                    ? faXmark
                                    : faCheck
                                }
                              />

                              {label || "-"}

                            </span>

                          </td>


                          <td
                            style={{
                              padding: "14px",
                            }}
                          >

                            {getConfidence(
                              prediction
                            )}

                          </td>


                          <td
                            style={{
                              padding: "14px",
                            }}
                          >

                            {formatDate(
                              date
                            )}

                          </td>

                        </tr>

                      );

                    }
                  )}

                </tbody>

              </table>

            </div>

          )}

        </section>


      </main>


      {/* ======================================================
          FOOTER
      ====================================================== */}

      <footer>

        <p>
          TruthLens — Prediction Management
        </p>

        <p>
          ResNet50 • Whisper • BERT • XGBoost
        </p>

      </footer>

    </div>

  );

}


export default AdminPredictions;