import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";


// ============================================================
// BACKEND
// ============================================================

const API_BASE_URL = "http://127.0.0.1:8000";


// ============================================================
// ADMIN LOGIN
// ============================================================

function AdminLogin() {

  const navigate = useNavigate();

  const [email, setEmail] = useState("");

  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");


// ============================================================
// LOGIN HANDLER
// ============================================================

  const handleLogin = async (event) => {

    event.preventDefault();

    setError("");

    // --------------------------------------------------------
    // Validation
    // --------------------------------------------------------

    if (!email.trim()) {

      setError("Please enter your admin email.");

      return;
    }

    if (!password) {

      setError("Please enter your password.");

      return;
    }


    setLoading(true);


    try {

      // ------------------------------------------------------
      // Send login request
      // ------------------------------------------------------

      const response = await axios.post(
        `${API_BASE_URL}/api/auth/login`,
        {
          email: email.trim().toLowerCase(),
          password: password,
        }
      );


      console.log(
        "ADMIN LOGIN RESPONSE:",
        response.data
      );


      // ------------------------------------------------------
      // Check successful response
      // ------------------------------------------------------

      if (!response.data?.success) {

        throw new Error(
          "Admin login was not successful."
        );
      }


      // ------------------------------------------------------
      // Get returned user
      // ------------------------------------------------------

      const user =
        response.data?.user;


      if (!user) {

        throw new Error(
          "User information was not returned."
        );
      }


      // ------------------------------------------------------
      // IMPORTANT:
      // Only allow admin accounts
      // ------------------------------------------------------

      if (
        String(user.role).toLowerCase() !== "admin"
      ) {

        setError(
          "Access denied. This account is not an administrator."
        );

        return;
      }


      // ------------------------------------------------------
      // Get token
      // ------------------------------------------------------

      const token =
        response.data?.access_token ||
        response.data?.token;


      if (!token) {

        throw new Error(
          "Authentication token was not returned."
        );
      }


      // ------------------------------------------------------
      // Store admin authentication
      // ------------------------------------------------------

      localStorage.setItem(
        "adminToken",
        token
      );


      localStorage.setItem(
        "adminUser",
        JSON.stringify(user)
      );


      // ------------------------------------------------------
      // Optional general authentication storage
      // ------------------------------------------------------

      localStorage.setItem(
        "token",
        token
      );


      localStorage.setItem(
        "user",
        JSON.stringify(user)
      );


      // ------------------------------------------------------
      // Go to admin dashboard
      // ------------------------------------------------------

      navigate(
        "/admin/dashboard",
        {
          replace: true
        }
      );

    }

    catch (error) {

      console.error(
        "Admin login error:",
        error
      );


      // ------------------------------------------------------
      // Backend error
      // ------------------------------------------------------

      if (
        error.response?.data?.detail
      ) {

        const detail =
          error.response.data.detail;


        if (typeof detail === "string") {

          setError(detail);

        }

        else {

          setError(
            "Unable to login. Please check your credentials."
          );

        }

      }

      else if (error.message) {

        setError(
          error.message
        );

      }

      else {

        setError(
          "Unable to connect to the authentication server."
        );

      }

    }

    finally {

      setLoading(false);

    }

  };


// ============================================================
// RENDER
// ============================================================

  return (

    <div className="admin-login-page">

      <div className="admin-login-card">


        {/* ==================================================
            HEADER
        ================================================== */}

        <div className="admin-login-header">

          <div className="admin-login-icon">
            🔐
          </div>

          <h1>
            Admin Login
          </h1>

          <p>
            Sign in to access the TruthLens administration panel.
          </p>

        </div>


        {/* ==================================================
            ERROR
        ================================================== */}

        {error && (

          <div className="admin-login-error">

            {error}

          </div>

        )}


        {/* ==================================================
            FORM
        ================================================== */}

        <form
          onSubmit={handleLogin}
          className="admin-login-form"
        >


          {/* ==================================================
              EMAIL
          ================================================== */}

          <div className="admin-form-group">

            <label htmlFor="admin-email">
              Admin Email
            </label>

            <input
              id="admin-email"
              type="email"
              placeholder="admin@truthlens.com"
              value={email}
              onChange={(event) =>
                setEmail(event.target.value)
              }
              autoComplete="email"
              disabled={loading}
            />

          </div>


          {/* ==================================================
              PASSWORD
          ================================================== */}

          <div className="admin-form-group">

            <label htmlFor="admin-password">
              Password
            </label>

            <input
              id="admin-password"
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(event) =>
                setPassword(event.target.value)
              }
              autoComplete="current-password"
              disabled={loading}
            />

          </div>


          {/* ==================================================
              LOGIN BUTTON
          ================================================== */}

          <button
            type="submit"
            className="admin-login-button"
            disabled={loading}
          >

            {loading
              ? "Signing in..."
              : "Admin Login"
            }

          </button>

        </form>

      </div>

    </div>

  );

}


export default AdminLogin;