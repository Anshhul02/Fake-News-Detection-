import React, { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

import {
  FontAwesomeIcon,
} from "@fortawesome/react-fontawesome";

import {
  faShieldHalved,
  faVideo,
  faUsers,
  faChartLine,
  faArrowRight,
  faRightFromBracket,
  faCircleCheck,
  faTriangleExclamation,
  faMagnifyingGlass,
  faDatabase,
} from "@fortawesome/free-solid-svg-icons";

import "../App.css";


/* ============================================================
   BACKEND
============================================================ */

const API_BASE_URL = "http://127.0.0.1:8000";


/* ============================================================
   ADMIN DASHBOARD
============================================================ */

function AdminDashboard() {

  const navigate = useNavigate();

  const [admin, setAdmin] = useState(null);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");


  /* ==========================================================
     GET TOKEN
  ========================================================== */

  const getToken = () => {

    return (
      localStorage.getItem("adminToken") ||
      localStorage.getItem("access_token") ||
      localStorage.getItem("token")
    );

  };


  /* ==========================================================
     VERIFY ADMIN + LOAD DASHBOARD
  ========================================================== */

  useEffect(() => {

    loadDashboard();

  }, []);


  const loadDashboard = async () => {

    const token = getToken();


    /* --------------------------------------------------------
       NO TOKEN
    -------------------------------------------------------- */

    if (!token) {

      navigate("/admin/login");

      return;

    }


    try {

      /* ======================================================
         VERIFY ADMIN
      ====================================================== */

      const adminResponse = await axios.get(
        `${API_BASE_URL}/api/auth/admin-test`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
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
         DASHBOARD REQUEST
         Kept so backend authentication/dashboard endpoint
         continues to be verified.
      ====================================================== */

      await axios.get(
        `${API_BASE_URL}/api/admin/dashboard`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );


    } catch (err) {

      console.error(
        "Admin dashboard loading failed:",
        err
      );


      /* ------------------------------------------------------
         UNAUTHORIZED / EXPIRED TOKEN
      ------------------------------------------------------ */

      if (
        err.response?.status === 401 ||
        err.response?.status === 403
      ) {

        localStorage.removeItem(
          "adminToken"
        );

        localStorage.removeItem(
          "access_token"
        );

        localStorage.removeItem(
          "token"
        );

        setError(
          "Your admin session is invalid or expired."
        );


        setTimeout(() => {

          navigate("/admin/login");

        }, 1200);


        return;

      }


      /* ------------------------------------------------------
         OTHER ERROR
      ------------------------------------------------------ */

      setError(
        err.response?.data?.detail ||
        err.message ||
        "Unable to load admin dashboard."
      );

    } finally {

      setLoading(false);

    }

  };


  /* ==========================================================
     LOGOUT
  ========================================================== */

  const handleLogout = () => {

    localStorage.removeItem(
      "adminToken"
    );

    localStorage.removeItem(
      "access_token"
    );

    localStorage.removeItem(
      "token"
    );

    localStorage.removeItem(
      "adminUser"
    );

    localStorage.removeItem(
      "user"
    );

    navigate(
      "/admin/login",
      {
        replace: true,
      }
    );

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
            Loading admin dashboard...
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

        <div
          style={{
            minHeight: "100vh",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexDirection: "column",
            gap: "15px",
            padding: "30px",
            textAlign: "center",
          }}
        >

          <FontAwesomeIcon
            icon={faTriangleExclamation}
            size="2x"
          />

          <strong>
            {error}
          </strong>

        </div>

      </div>

    );

  }


  /* ==========================================================
     RENDER
  ========================================================== */

  return (

    <div className="app">


      {/* ======================================================
          HEADER
      ====================================================== */}

      <header className="header">

        <div className="header-inner">


          {/* BRAND */}

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


          {/* ADMIN */}

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

       


        {/* ====================================================
            WELCOME
        ==================================================== */}

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
                Welcome, {admin?.name || "Admin"}
              </h2>

              <p className="description">

                Manage the TruthLens fake news video
                detection system from one place.

              </p>

            </div>

          </div>


          {/* ADMIN INFORMATION */}

          <div
            style={{
              display: "grid",
              gridTemplateColumns:
                "repeat(auto-fit, minmax(220px, 1fr))",
              gap: "15px",
              marginTop: "25px",
            }}
          >

            <div className="evidence-box">

              <span>
                Administrator
              </span>

              <strong>
                {admin?.name || "-"}
              </strong>

            </div>


            <div className="evidence-box">

              <span>
                Email
              </span>

              <strong>
                {admin?.email || "-"}
              </strong>

            </div>


            <div className="evidence-box">

              <span>
                Role
              </span>

              <strong>
                {admin?.role || "admin"}
              </strong>

            </div>

          </div>

        </section>


        {/* ====================================================
            SYSTEM STATUS
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

          {/* AUTHENTICATION */}

          <div className="evidence-box">

            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >

              <div>

                <span>
                  Authentication
                </span>

                <strong
                  style={{
                    display: "block",
                    fontSize: "22px",
                    marginTop: "8px",
                  }}
                >
                  Verified
                </strong>

              </div>

              <FontAwesomeIcon
                icon={faCircleCheck}
                size="lg"
              />

            </div>

          </div>


          {/* AI PIPELINE */}

          <div className="evidence-box">

            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >

              <div>

                <span>
                  AI Pipeline
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

              </div>

              <FontAwesomeIcon
                icon={faChartLine}
                size="lg"
              />

            </div>

          </div>


          {/* DATABASE */}

          <div className="evidence-box">

            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >

              <div>

                <span>
                  Database
                </span>

                <strong
                  style={{
                    display: "block",
                    fontSize: "22px",
                    marginTop: "8px",
                  }}
                >
                  Connected
                </strong>

              </div>

              <FontAwesomeIcon
                icon={faDatabase}
                size="lg"
              />

            </div>

          </div>

        </section>


        {/* ====================================================
            ADMIN ACTIONS
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
                Administration
              </h2>

              <p className="description">

                Access the main TruthLens management
                functions.

              </p>

            </div>

          </div>


          <div
            style={{
              display: "grid",
              gridTemplateColumns:
                "repeat(auto-fit, minmax(250px, 1fr))",
              gap: "18px",
              marginTop: "20px",
            }}
          >


            {/* PREDICTIONS */}

            <button
              type="button"
              className="analyze-another-button"
              onClick={() =>
                navigate("/admin/predictions")
              }
            >

              <FontAwesomeIcon
                icon={faMagnifyingGlass}
              />

              View Predictions

              <FontAwesomeIcon
                icon={faArrowRight}
              />

            </button>


            {/* USERS */}

            <button
              type="button"
              className="analyze-another-button"
              onClick={() =>
                navigate("/admin/users")
              }
            >

              <FontAwesomeIcon
                icon={faUsers}
              />

              Manage Users

              <FontAwesomeIcon
                icon={faArrowRight}
              />

            </button>


            {/* DETECTION */}

            <button
              type="button"
              className="analyze-another-button"
              onClick={() =>
                navigate("/")
              }
            >

              <FontAwesomeIcon
                icon={faVideo}
              />

              Open Detection

              <FontAwesomeIcon
                icon={faArrowRight}
              />

            </button>

          </div>

        </section>


        {/* ====================================================
            PIPELINE INFORMATION
        ==================================================== 

        <section
          className="upload-card"
          style={{
            marginTop: "25px",
          }}
        >

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
                AI PIPELINE
              </span>

              <h2>
                TruthLens Detection Architecture
              </h2>

            </div>

          </div>


          <div
            style={{
              display: "grid",
              gridTemplateColumns:
                "repeat(auto-fit, minmax(180px, 1fr))",
              gap: "15px",
              marginTop: "20px",
            }}
          */}

            {/* VISUAL 

            <div className="evidence-box">

              <span>
                Visual
              </span>

              <strong>
                ResNet50
              </strong>

              <small>
                2048 features
              </small>

            </div>

*/}
            {/* SPEECH 

            <div className="evidence-box">

              <span>
                Speech
              </span>

              <strong>
                Whisper
              </strong>

              <small>
                Audio transcription
              </small>

            </div>

*/}
            {/* TEXT 

            <div className="evidence-box">

              <span>
                Text
              </span>

              <strong>
                BERT
              </strong>

              <small>
                768 features
              </small>

            </div>
*/}

            {/* FUSION 

            <div className="evidence-box">

              <span>
                Fusion
              </span>

              <strong>
                XGBoost
              </strong>

              <small>
                2816 fused features
              </small>

            </div>

          </div>

        </section>


      </main>
*/}

      {/* ======================================================
          FOOTER
      ====================================================== */}

      <footer>

        <p>
          TruthLens — Administration Panel
        </p>

        <p>
          ResNet50 • Whisper • BERT • XGBoost
        </p>

      </footer>

    </div>

  );

}


export default AdminDashboard;