import React, { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

import {
  FontAwesomeIcon,
} from "@fortawesome/react-fontawesome";

import {
  faShieldHalved,
  faUsers,
  faUserShield,
  faUser,
  faArrowLeft,
  faRightFromBracket,
  faCircleCheck,
  faTriangleExclamation,
  faEnvelope,
  faCalendar,
} from "@fortawesome/free-solid-svg-icons";

import "../App.css";


/* ============================================================
   BACKEND
============================================================ */

const API_BASE_URL = "http://127.0.0.1:8000";


/* ============================================================
   ADMIN USERS
============================================================ */

function AdminUsers() {

  const navigate = useNavigate();

  const [admin, setAdmin] = useState(null);

  const [stats, setStats] = useState(null);

  const [users, setUsers] = useState([]);

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
     LOAD USERS + STATISTICS
  ========================================================== */

  useEffect(() => {

    loadUserData();

  }, []);


  const loadUserData = async () => {

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
         USER STATISTICS
      ====================================================== */

      const statsResponse = await axios.get(

        `${API_BASE_URL}/api/admin/users/stats`,

        {
          headers,
        }

      );


      console.log(
        "User statistics response:",
        statsResponse.data
      );


      const statsData =
        statsResponse.data?.users ||
        statsResponse.data?.stats ||
        statsResponse.data?.data ||
        statsResponse.data;


      setStats(
        statsData || {}
      );


      /* ======================================================
         ALL USERS
      ====================================================== */

      const usersResponse = await axios.get(

        `${API_BASE_URL}/api/admin/users?limit=100`,

        {
          headers,
        }

      );


      console.log(
        "Users response:",
        usersResponse.data
      );


      const usersData =
        usersResponse.data?.users ||
        usersResponse.data?.data ||
        usersResponse.data?.results ||
        [];


      if (Array.isArray(usersData)) {

        setUsers(usersData);

      } else {

        setUsers([]);

      }


    }

    catch (err) {

      console.error(
        "Failed to load user data:",
        err
      );


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

        navigate("/admin/login");

        return;

      }


      setError(

        err.response?.data?.detail ||

        err.response?.data?.message ||

        err.message ||

        "Unable to load users."

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

    localStorage.removeItem(
      "adminToken"
    );

    localStorage.removeItem(
      "access_token"
    );

    localStorage.removeItem(
      "token"
    );

    navigate("/admin/login");

  };


  /* ==========================================================
     STATISTICS
  ========================================================== */

  const totalUsers =
    Number(
      stats?.total ??
      users.length ??
      0
    );


  const totalAdmins =
    Number(
      stats?.admins ??
      users.filter(
        user =>
          String(
            user?.role || ""
          ).toLowerCase() === "admin"
      ).length
    );


  const regularUsers =
    Number(
      stats?.normal_users ??
      users.filter(
        user =>
          String(
            user?.role || ""
          ).toLowerCase() === "user"
      ).length
    );


  /* ==========================================================
     FORMAT DATE
  ========================================================== */

  const formatDate = (value) => {

    if (!value) {

      return "-";

    }


    const date = new Date(value);


    if (
      Number.isNaN(
        date.getTime()
      )
    ) {

      return String(value);

    }


    return date.toLocaleString();

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
            Loading users...
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
              Unable to Load Users
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
                User Management
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
                User Management
              </h2>

              <p className="description">

                View all TruthLens registered
                users and administrators.

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
            USER STATISTICS
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
              Total Users
            </span>

            <strong
              style={{
                display: "block",
                fontSize: "28px",
                marginTop: "8px",
              }}
            >

              {totalUsers}

            </strong>

            <div
              style={{
                marginTop: "12px",
              }}
            >

              <FontAwesomeIcon
                icon={faUsers}
              />

            </div>

          </div>


          {/* ADMINS */}

          <div className="evidence-box">

            <span>
              Administrators
            </span>

            <strong
              style={{
                display: "block",
                fontSize: "28px",
                marginTop: "8px",
              }}
            >

              {totalAdmins}

            </strong>

            <div
              style={{
                marginTop: "12px",
              }}
            >

              <FontAwesomeIcon
                icon={faUserShield}
              />

            </div>

          </div>


          {/* REGULAR USERS */}

          <div className="evidence-box">

            <span>
              Regular Users
            </span>

            <strong
              style={{
                display: "block",
                fontSize: "28px",
                marginTop: "8px",
              }}
            >

              {regularUsers}

            </strong>

            <div
              style={{
                marginTop: "12px",
              }}
            >

              <FontAwesomeIcon
                icon={faUser}
              />

            </div>

          </div>

        </section>


        {/* ====================================================
            ALL USERS
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
                Registered Users
              </h2>

              <p className="description">

                All user accounts currently stored
                in the TruthLens database.

              </p>

            </div>

          </div>


          {users.length === 0 ? (

            <div
              className="evidence-box"
              style={{
                marginTop: "20px",
                textAlign: "center",
              }}
            >

              <FontAwesomeIcon
                icon={faUsers}
                size="2x"
              />

              <p>
                No users found.
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
                  minWidth: "800px",
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
                      User
                    </th>

                    <th
                      style={{
                        textAlign: "left",
                        padding: "14px",
                      }}
                    >
                      Email
                    </th>

                    <th
                      style={{
                        textAlign: "left",
                        padding: "14px",
                      }}
                    >
                      Role
                    </th>

                    <th
                      style={{
                        textAlign: "left",
                        padding: "14px",
                      }}
                    >
                      Created
                    </th>

                  </tr>

                </thead>


                <tbody>

                  {users.map(
                    (
                      user,
                      index
                    ) => {

                      const role =
                        String(
                          user?.role ||
                          "user"
                        ).toLowerCase();


                      const isAdmin =
                        role === "admin";


                      return (

                        <tr
                          key={
                            user?.id ||
                            user?._id ||
                            index
                          }
                        >

                          {/* NUMBER */}

                          <td
                            style={{
                              padding: "14px",
                            }}
                          >

                            {index + 1}

                          </td>


                          {/* USER */}

                          <td
                            style={{
                              padding: "14px",
                              fontWeight: 600,
                            }}
                          >

                            <div
                              style={{
                                display: "flex",
                                alignItems: "center",
                                gap: "10px",
                              }}
                            >

                              <FontAwesomeIcon
                                icon={
                                  isAdmin
                                    ? faUserShield
                                    : faUser
                                }
                              />

                              <span>
                                {
                                  user?.name ||
                                  "-"
                                }
                              </span>

                            </div>

                          </td>


                          {/* EMAIL */}

                          <td
                            style={{
                              padding: "14px",
                            }}
                          >

                            <span
                              style={{
                                display: "inline-flex",
                                alignItems: "center",
                                gap: "8px",
                              }}
                            >

                              <FontAwesomeIcon
                                icon={faEnvelope}
                              />

                              {
                                user?.email ||
                                "-"
                              }

                            </span>

                          </td>


                          {/* ROLE */}

                          <td
                            style={{
                              padding: "14px",
                            }}
                          >

                            <span
                              style={{
                                display: "inline-flex",
                                alignItems: "center",
                                gap: "8px",
                                fontWeight: 700,
                              }}
                            >

                              <FontAwesomeIcon
                                icon={
                                  isAdmin
                                    ? faUserShield
                                    : faUser
                                }
                              />

                              {isAdmin
                                ? "ADMIN"
                                : "USER"}

                            </span>

                          </td>


                          {/* DATE */}

                          <td
                            style={{
                              padding: "14px",
                            }}
                          >

                            <span
                              style={{
                                display: "inline-flex",
                                alignItems: "center",
                                gap: "8px",
                              }}
                            >

                              <FontAwesomeIcon
                                icon={faCalendar}
                              />

                              {formatDate(
                                user?.created_at ??
                                user?.createdAt
                              )}

                            </span>

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
          TruthLens — User Management
        </p>

        <p>

          Administrator:{" "}

          {admin?.email || "-"}

        </p>

      </footer>

    </div>

  );

}


export default AdminUsers;