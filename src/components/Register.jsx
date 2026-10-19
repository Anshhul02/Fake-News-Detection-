
import React, { useState } from "react";
import axios from "axios";
import { Link, useNavigate } from "react-router-dom";

const API_BASE_URL = "http://127.0.0.1:8000";

function Register() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

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
    setSuccess("");
  };

  // ============================================================
  // REGISTER
  // ============================================================

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");
    setSuccess("");

    // ----------------------------------------------------------
    // VALIDATION
    // ----------------------------------------------------------

    if (
      !formData.name ||
      !formData.email ||
      !formData.password ||
      !formData.confirmPassword
    ) {
      setError(
        "Please fill in all fields."
      );
      return;
    }

    if (formData.name.trim().length < 2) {
      setError(
        "Name must contain at least 2 characters."
      );
      return;
    }

    if (formData.password.length < 6) {
      setError(
        "Password must contain at least 6 characters."
      );
      return;
    }

    if (
      formData.password !==
      formData.confirmPassword
    ) {
      setError(
        "Passwords do not match."
      );
      return;
    }

    // ----------------------------------------------------------
    // API REQUEST
    // ----------------------------------------------------------

    setLoading(true);

    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/auth/register`,
        {
          name: formData.name.trim(),
          email: formData.email.trim().toLowerCase(),
          password: formData.password,
        }
      );

      if (!response.data?.success) {
        throw new Error(
          "Registration was unsuccessful."
        );
      }

      // --------------------------------------------------------
      // SAVE TOKEN IF BACKEND RETURNS ONE
      // --------------------------------------------------------

      const token =
        response.data.access_token ||
        response.data.token;

      const user =
        response.data.user;

      if (token) {
        localStorage.setItem(
          "token",
          token
        );

        localStorage.setItem(
          "access_token",
          token
        );
      }

      if (user) {
        localStorage.setItem(
          "user",
          JSON.stringify(user)
        );
      }

      // --------------------------------------------------------
      // SUCCESS
      // --------------------------------------------------------

      setSuccess(
        "Registration successful. Redirecting..."
      );

      // Give the user a moment to see the success message.
      setTimeout(() => {
        navigate("/home");
      }, 700);

    } catch (error) {
      console.error(
        "Registration failed:",
        error
      );

      if (error.response?.data?.detail) {
        setError(
          typeof error.response.data.detail === "string"
            ? error.response.data.detail
            : "Registration failed."
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
            Create Account
          </h2>

          <p>
            Create your TruthLens account to get started.
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
            SUCCESS
        ====================================================== */}

        {success && (
          <div className="auth-success">
            {success}
          </div>
        )}

        {/* ======================================================
            FORM
        ====================================================== */}

        <form
          onSubmit={handleSubmit}
          className="auth-form"
        >

          {/* NAME */}

          <div className="form-group">

            <label htmlFor="name">
              Full Name
            </label>

            <input
              id="name"
              name="name"
              type="text"
              placeholder="Enter your name"
              value={formData.name}
              onChange={handleChange}
              autoComplete="name"
              disabled={loading}
            />

          </div>

          {/* EMAIL */}

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

          {/* PASSWORD */}

          <div className="form-group">

            <label htmlFor="password">
              Password
            </label>

            <input
              id="password"
              name="password"
              type="password"
              placeholder="Create a password"
              value={formData.password}
              onChange={handleChange}
              autoComplete="new-password"
              disabled={loading}
            />

          </div>

          {/* CONFIRM PASSWORD */}

          <div className="form-group">

            <label htmlFor="confirmPassword">
              Confirm Password
            </label>

            <input
              id="confirmPassword"
              name="confirmPassword"
              type="password"
              placeholder="Confirm your password"
              value={formData.confirmPassword}
              onChange={handleChange}
              autoComplete="new-password"
              disabled={loading}
            />

          </div>

          {/* SUBMIT */}

          <button
            type="submit"
            className="auth-submit"
            disabled={loading}
          >

            {loading
              ? "Creating Account..."
              : "Create Account"}

          </button>

        </form>

        {/* ======================================================
            LOGIN LINK
        ====================================================== */}

        <div className="auth-footer">

          <span>
            Already have an account?
          </span>

          <Link to="/">
            Sign In
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

export default Register;
