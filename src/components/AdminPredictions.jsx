
import React, { useEffect, useState } from "react";
import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:8000";

function AdminPredictions() {

  const [stats, setStats] = useState(null);
  const [predictions, setPredictions] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // ============================================================
  // GET ADMIN TOKEN
  // ============================================================

  const getToken = () => {
    return (
      localStorage.getItem("adminToken") ||
      localStorage.getItem("access_token") ||
      localStorage.getItem("token")
    );
  };

  // ============================================================
  // LOAD PREDICTION DATA
  // ============================================================

  const loadPredictions = async () => {

    setLoading(true);
    setError("");

    const token = getToken();

    if (!token) {
      setError(
        "Admin authentication token was not found."
      );

      setLoading(false);
      return;
    }

    const config = {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    };

    try {

      const [
        statsResponse,
        recentResponse,
      ] = await Promise.all([

        axios.get(
          `${API_BASE_URL}/api/admin/predictions/stats`,
          config
        ),

        axios.get(
          `${API_BASE_URL}/api/admin/predictions/recent?limit=20`,
          config
        ),

      ]);

      console.log(
        "PREDICTION STATISTICS:",
        statsResponse.data
      );

      console.log(
        "RECENT PREDICTIONS:",
        recentResponse.data
      );

      if (!statsResponse.data?.success) {
        throw new Error(
          "Prediction statistics could not be loaded."
        );
      }

      if (!recentResponse.data?.success) {
        throw new Error(
          "Recent predictions could not be loaded."
        );
      }

      setStats(
        statsResponse.data.predictions
      );

      setPredictions(
        Array.isArray(
          recentResponse.data.predictions
        )
          ? recentResponse.data.predictions
          : []
      );

    }

    catch (error) {

      console.error(
        "Failed to load predictions:",
        error
      );

      if (error.response?.status === 401) {

        setError(
          "Your admin session has expired. Please login again."
        );

      }

      else if (error.response?.status === 403) {

        setError(
          "Admin access required."
        );

      }

      else if (error.response?.data?.detail) {

        setError(
          error.response.data.detail
        );

      }

      else if (error.message) {

        setError(
          error.message
        );

      }

      else {

        setError(
          "Unable to load prediction data."
        );

      }

    }

    finally {
      setLoading(false);
    }
  };

  // ============================================================
  // LOAD DATA ON PAGE OPEN
  // ============================================================

  useEffect(() => {
    loadPredictions();
  }, []);

  // ============================================================
  // FORMAT DATE
  // ============================================================

  const formatDate = (value) => {

    if (!value) {
      return "-";
    }

    try {

      return new Date(value).toLocaleString();

    }

    catch {
      return String(value);
    }
  };

  // ============================================================
  // GET LABEL
  // ============================================================

  const getLabel = (prediction) => {

    return (
      prediction.label ||
      prediction.predicted_label ||
      prediction.result ||
      "UNKNOWN"
    )
      .toString()
      .toUpperCase();
  };

  // ============================================================
  // GET VIDEO NAME
  // ============================================================

  const getVideoName = (prediction) => {

    return (
      prediction.video_id ||
      prediction.filename ||
      prediction.video_name ||
      prediction.file_name ||
      "-"
    );
  };

  // ============================================================
  // GET PROBABILITY
  // ============================================================

  const getProbability = (prediction) => {

    const label = getLabel(prediction);

    let value;

    if (label === "FAKE") {

      value =
        prediction.fake_probability ??
        prediction.fakeProbability;

    } else if (label === "REAL") {

      value =
        prediction.real_probability ??
        prediction.realProbability;

    } else {

      value =
        prediction.confidence ??
        prediction.probability;
    }

    if (
      value === undefined ||
      value === null
    ) {
      return "-";
    }

    const number = Number(value);

    if (Number.isNaN(number)) {
      return "-";
    }

    return `${(number * 100).toFixed(2)}%`;
  };

  // ============================================================
  // RENDER
  // ============================================================

  return (

    <div className="admin-predictions-page">

      {/* ======================================================
          HEADER
      ====================================================== */}

      <div className="admin-page-header">

        <div>

          <span className="admin-page-kicker">
            DETECTION ANALYTICS
          </span>

          <h1>
            Predictions
          </h1>

          <p>
            Monitor TruthLens fake-news video detection
            activity and recent prediction results.
          </p>

        </div>

        <button
          type="button"
          className="admin-refresh-button"
          onClick={loadPredictions}
          disabled={loading}
        >
          {loading
            ? "Loading..."
            : "Refresh"}
        </button>

      </div>

      {/* ======================================================
          ERROR
      ====================================================== */}

      {error && (

        <div className="admin-error">
          {error}
        </div>

      )}

      {/* ======================================================
          LOADING
      ====================================================== */}

      {loading && !stats && (

        <div className="admin-loading">

          <div className="admin-spinner"></div>

          <p>
            Loading prediction data...
          </p>

        </div>

      )}

      {/* ======================================================
          STATISTICS
      ====================================================== */}

      {stats && (

        <div className="admin-prediction-stats">

          {/* TOTAL */}

          <div className="admin-stat-card">

            <div className="admin-stat-icon">
              📊
            </div>

            <div>

              <span>
                Total Predictions
              </span>

              <strong>
                {stats.total ?? 0}
              </strong>

            </div>

          </div>

          {/* FAKE */}

          <div className="admin-stat-card fake-stat">

            <div className="admin-stat-icon">
              ⚠
            </div>

            <div>

              <span>
                Fake Detected
              </span>

              <strong>
                {stats.fake ?? 0}
              </strong>

              <small>
                {Number(
                  stats.fake_percentage ?? 0
                ).toFixed(2)}
                %
              </small>

            </div>

          </div>

          {/* REAL */}

          <div className="admin-stat-card real-stat">

            <div className="admin-stat-icon">
              ✓
            </div>

            <div>

              <span>
                Real Detected
              </span>

              <strong>
                {stats.real ?? 0}
              </strong>

              <small>
                {Number(
                  stats.real_percentage ?? 0
                ).toFixed(2)}
                %
              </small>

            </div>

          </div>

        </div>

      )}

      {/* ======================================================
          DISTRIBUTION
      ====================================================== */}

      {stats && (

        <div className="admin-distribution-card">

          <div className="admin-section-heading">

            <div>

              <span className="admin-page-kicker">
                RESULT DISTRIBUTION
              </span>

              <h2>
                Fake vs Real
              </h2>

            </div>

          </div>

          <div className="distribution-bar">

            <div
              className="distribution-fake"
              style={{
                width: `${Math.min(
                  Number(
                    stats.fake_percentage ?? 0
                  ),
                  100
                )}%`,
              }}
            />

            <div
              className="distribution-real"
              style={{
                width: `${Math.min(
                  Number(
                    stats.real_percentage ?? 0
                  ),
                  100
                )}%`,
              }}
            />

          </div>

          <div className="distribution-legend">

            <span>
              <i className="legend-fake"></i>
              Fake —{" "}
              {Number(
                stats.fake_percentage ?? 0
              ).toFixed(2)}
              %
            </span>

            <span>
              <i className="legend-real"></i>
              Real —{" "}
              {Number(
                stats.real_percentage ?? 0
              ).toFixed(2)}
              %
            </span>

          </div>

        </div>

      )}

      {/* ======================================================
          RECENT PREDICTIONS
      ====================================================== */}

      <div className="admin-table-card">

        <div className="admin-section-heading">

          <div>

            <span className="admin-page-kicker">
              HISTORY
            </span>

            <h2>
              Recent Predictions
            </h2>

          </div>

          <span className="prediction-count">
            {predictions.length} records
          </span>

        </div>

        {predictions.length === 0 ? (

          <div className="admin-empty">

            <div className="admin-empty-icon">
              📭
            </div>

            <h3>
              No predictions found
            </h3>

            <p>
              Prediction results will appear here
              after videos are analyzed.
            </p>

          </div>

        ) : (

          <div className="prediction-table-wrapper">

            <table className="prediction-table">

              <thead>

                <tr>

                  <th>
                    Video
                  </th>

                  <th>
                    Result
                  </th>

                  <th>
                    Probability
                  </th>

                  <th>
                    Date
                  </th>

                </tr>

              </thead>

              <tbody>

                {predictions.map(
                  (prediction, index) => {

                    const label =
                      getLabel(
                        prediction
                      );

                    return (

                      <tr
                        key={
                          prediction.id ||
                          prediction._id ||
                          index
                        }
                      >

                        <td>

                          <strong>
                            {getVideoName(
                              prediction
                            )}
                          </strong>

                        </td>

                        <td>

                          <span
                            className={
                              label === "FAKE"
                                ? "prediction-badge fake"
                                : label === "REAL"
                                ? "prediction-badge real"
                                : "prediction-badge"
                            }
                          >
                            {label}
                          </span>

                        </td>

                        <td>

                          {getProbability(
                            prediction
                          )}

                        </td>

                        <td>

                          {formatDate(
                            prediction.created_at ||
                            prediction.createdAt ||
                            prediction.timestamp
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

      </div>

    </div>

  );
}

export default AdminPredictions;
