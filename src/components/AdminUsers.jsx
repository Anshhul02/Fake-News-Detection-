
import React, { useEffect, useState } from "react";
import axios from "axios";


// ============================================================
// BACKEND
// ============================================================

const API_BASE_URL = "http://127.0.0.1:8000";


// ============================================================
// ADMIN USERS
// ============================================================

function AdminUsers() {

  const [stats, setStats] = useState(null);

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
// LOAD USER STATISTICS
// ============================================================

  const loadUserStats = async () => {

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


    try {

      const response = await axios.get(
        `${API_BASE_URL}/api/admin/users/stats`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );


      console.log(
        "ADMIN USER STATISTICS:",
        response.data
      );


      if (!response.data?.success) {

        throw new Error(
          "Unable to load user statistics."
        );
      }


      setStats(
        response.data.users
      );

    }

    catch (error) {

      console.error(
        "Failed to load admin users:",
        error
      );


      if (
        error.response?.status === 401
      ) {

        setError(
          "Your admin session has expired. Please login again."
        );

      }

      else if (
        error.response?.status === 403
      ) {

        setError(
          "Admin access required."
        );

      }

      else if (
        error.response?.data?.detail
      ) {

        setError(
          error.response.data.detail
        );

      }

      else {

        setError(
          "Unable to load user statistics."
        );

      }

    }

    finally {

      setLoading(false);

    }

  };


// ============================================================
// LOAD ON PAGE OPEN
// ============================================================

  useEffect(() => {

    loadUserStats();

  }, []);


// ============================================================
// RENDER
// ============================================================

  return (

    <div className="admin-users-page">

      {/* ======================================================
          HEADER
      ====================================================== */}

      <div className="admin-page-header">

        <div>

          <span className="admin-page-kicker">
            ADMINISTRATION
          </span>

          <h1>
            Users
          </h1>

          <p>
            Monitor TruthLens user accounts and
            administrator accounts.
          </p>

        </div>


        <button
          type="button"
          className="admin-refresh-button"
          onClick={loadUserStats}
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
            Loading user statistics...
          </p>

        </div>

      )}


      {/* ======================================================
          STATISTICS
      ====================================================== */}

      {stats && (

        <div className="admin-stats-grid">


          {/* TOTAL USERS */}

          <div className="admin-stat-card">

            <div className="admin-stat-icon">
              👥
            </div>

            <div>

              <span>
                Total Users
              </span>

              <strong>
                {stats.total ?? 0}
              </strong>

            </div>

          </div>


          {/* NORMAL USERS */}

          <div className="admin-stat-card">

            <div className="admin-stat-icon">
              👤
            </div>

            <div>

              <span>
                Registered Users
              </span>

              <strong>
                {stats.normal_users ?? 0}
              </strong>

            </div>

          </div>


          {/* ADMINS */}

          <div className="admin-stat-card">

            <div className="admin-stat-icon">
              🛡️
            </div>

            <div>

              <span>
                Administrators
              </span>

              <strong>
                {stats.admins ?? 0}
              </strong>

            </div>

          </div>

        </div>

      )}


      {/* ======================================================
          INFORMATION
      ====================================================== */}

      <div className="admin-information-card">

        <div>

          <span className="admin-page-kicker">
            ACCOUNT MANAGEMENT
          </span>

          <h2>
            User Management
          </h2>

          <p>
            The current backend provides authenticated
            user statistics. Individual user listing,
            editing and deletion can be added later
            through protected admin endpoints.
          </p>

        </div>

      </div>

    </div>

  );

}


export default AdminUsers;

