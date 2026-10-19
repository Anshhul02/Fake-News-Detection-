
import React, { useState } from "react";
import axios from "axios";
import { useNavigate, Link } from "react-router-dom";

const API_BASE_URL = "http://127.0.0.1:8000";

function Login() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // ============================================================
  // HANDLE INPUT
  // ============================================================

  const handleChange = (event) => {
    const { name, value } = event.target;

    setFormData((previous) => ({
      ...previous,
      [name]: value,
    }));

    setError("");
  };

  // ============================================================
  // LOGIN
  // ============================================================

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");

    if (!formData.email || !formData.password) {
      setError("Please enter your email and password.");
      return;
    }

    setLoading(true);

    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/auth/login`,
        {
          email: formData.email,
          password: formData.password,
        }
      );

      if (!response.data?.success) {
        throw new Error(
          "Login was unsuccessful."
        );
      }

      const token =
        response.data.access_token ||
        response.data.token;

      const user =
        response.data.user;

      if (!token || !user) {
        throw new Error(
          "Invalid login response from server."
        );
      }

      // --------------------------------------------------------
      // STORE AUTHENTICATION
      // --------------------------------------------------------

      localStorage.setItem(
        "token",
        token
      );

      localStorage.setItem(
        "access_token",
        token
      );

      localStorage.setItem(
        "user",
        JSON.stringify(user)
      );

      // --------------------------------------------------------
      // ROLE-BASED REDIRECTION
      // --------------------------------------------------------

      if (user.role === "admin") {
        navigate("/admin/dashboard");
      } else {
        navigate("/home");
      }

    } catch (error) {
      console.error(
        "Login failed:",
        error
      );

      if (error.response?.data?.detail) {
        setError(
          typeof error.response.data.detail === "string"
            ? error.response.data.detail
            : "Login failed."
        );
      } else if (error.message) {
        setError(error.message);
      } else {
        setError(
          "Unable to connect to the server."
        );
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">

      <div className="auth-card">

        {/* ======================================================
            BRAND
        ====================================================== */}

        <div className="auth-brand">

          <div className="auth-brand-icon">
            🔎
          </div>

          <h1>
            TruthLens
          </h1>

          <p>
            Multimodal Fake News Video Detection
          </p>

        </div>

        {/* ======================================================
            TITLE
        ====================================================== */}

        <div className="auth-heading">

          <h2>
            Welcome Back
          </h2>

          <p>
            Sign in to continue to TruthLens.
          </p>

        </div>

        {/* ======================================================
            ERROR
        ====================================================== */}

        {error && (
          <div className="auth-error">
            {error}
          </div>
        )}

        {/* ======================================================
            FORM
        ====================================================== */}

        <form
          onSubmit={handleSubmit}
          className="auth-form"
        >

          <div className="form-group">

            <label htmlFor="email">
              Email Address
            </label>

            <input
              id="email"
              name="email"
              type="email"
              placeholder="Enter your email"
              value={formData.email}
              onChange={handleChange}
              autoComplete="email"
              disabled={loading}
            />

          </div>

          <div className="form-group">

            <label htmlFor="password">
              Password
            </label>

            <input
              id="password"
              name="password"
              type="password"
              placeholder="Enter your password"
              value={formData.password}
              onChange={handleChange}
              autoComplete="current-password"
              disabled={loading}
            />

          </div>

          <button
            type="submit"
            className="auth-submit"
            disabled={loading}
          >

            {loading
              ? "Signing in..."
              : "Sign In"}

          </button>

        </form>

        {/* ======================================================
            REGISTER
        ====================================================== */}

        <div className="auth-footer">

          <span>
            Don't have an account?
          </span>

          <Link to="/register">
            Create Account
          </Link>

        </div>

        {/* ======================================================
            ADMIN LOGIN
        ====================================================== */}

        <div className="admin-login-link">

          <Link to="/admin/login">
            Admin Login
          </Link>

        </div>

      </div>

    </div>
  );
}

export default Login;

