// ============================================================
// ATUL MAHAISKAR PORTFOLIO
// CONTACT FORM JAVASCRIPT
// PRODUCTION CONTACT API
// ============================================================

document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector(".contact-form");

    if (!form) {
        console.error("Contact form not found.");
        return;
    }

    // ========================================================
    // PRODUCTION FLASK API
    // ========================================================

    const API_URL =
        "https://atul-mahaiskar-backend.onrender.com/api/contact";

    // ========================================================
    // CREATE NOTIFICATION
    // ========================================================

    function showNotification(message, type = "success") {
        const existing =
            document.querySelector(".contact-notification");

        if (existing) {
            existing.remove();
        }

        const notification =
            document.createElement("div");

        notification.className =
            `contact-notification ${type}`;

        const icon =
            type === "success"
                ? "fa-circle-check"
                : "fa-circle-exclamation";

        notification.innerHTML = `
            <div class="notification-icon">
                <i class="fa-solid ${icon}"></i>
            </div>

            <div class="notification-content">
                <strong>
                    ${
                        type === "success"
                            ? "Message Sent"
                            : "Something went wrong"
                    }
                </strong>

                <span>
                    ${message}
                </span>
            </div>

            <button
                class="notification-close"
                type="button"
                aria-label="Close notification">

                <i class="fa-solid fa-xmark"></i>

            </button>
        `;

        document.body.appendChild(notification);

        requestAnimationFrame(() => {
            notification.classList.add("show");
        });

        const closeButton =
            notification.querySelector(
                ".notification-close"
            );

        if (closeButton) {
            closeButton.addEventListener(
                "click",
                () => {
                    closeNotification(notification);
                }
            );
        }

        setTimeout(() => {
            closeNotification(notification);
        }, 5000);
    }

    // ========================================================
    // CLOSE NOTIFICATION
    // ========================================================

    function closeNotification(notification) {
        if (!notification) {
            return;
        }

        notification.classList.remove("show");

        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 350);
    }

    // ========================================================
    // FORM SUBMIT
    // ========================================================

    form.addEventListener(
        "submit",
        async (event) => {
            event.preventDefault();

            // ------------------------------------------------
            // FORM ELEMENTS
            // ------------------------------------------------

            const nameInput =
                document.getElementById("name");

            const emailInput =
                document.getElementById("email");

            const messageInput =
                document.getElementById("message");

            const button =
                form.querySelector(
                    ".send-message-btn"
                );

            if (
                !nameInput ||
                !emailInput ||
                !messageInput ||
                !button
            ) {
                console.error(
                    "Contact form elements are missing."
                );

                showNotification(
                    "The contact form could not be loaded correctly.",
                    "error"
                );

                return;
            }

            // ------------------------------------------------
            // VALUES
            // ------------------------------------------------

            const name =
                nameInput.value.trim();

            const email =
                emailInput.value.trim();

            const message =
                messageInput.value.trim();

            // ------------------------------------------------
            // VALIDATION
            // ------------------------------------------------

            if (!name) {
                showNotification(
                    "Please enter your name.",
                    "error"
                );

                nameInput.focus();
                return;
            }

            if (!email) {
                showNotification(
                    "Please enter your email.",
                    "error"
                );

                emailInput.focus();
                return;
            }

            // Basic email validation
            const emailPattern =
                /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

            if (!emailPattern.test(email)) {
                showNotification(
                    "Please enter a valid email address.",
                    "error"
                );

                emailInput.focus();
                return;
            }

            if (!message) {
                showNotification(
                    "Please enter your message.",
                    "error"
                );

                messageInput.focus();
                return;
            }

            // ------------------------------------------------
            // ORIGINAL BUTTON
            // ------------------------------------------------

            const originalButtonHTML =
                button.innerHTML;

            // ------------------------------------------------
            // DISABLE BUTTON
            // ------------------------------------------------

            button.disabled = true;

            button.innerHTML = `
                <i
                    class="fa-solid fa-spinner fa-spin"
                    style="margin-right: 8px;">
                </i>

                Sending...
            `;

            try {
                console.log(
                    "Sending contact request to:",
                    API_URL
                );

                // --------------------------------------------
                // SEND REQUEST
                // --------------------------------------------

                const response =
                    await fetch(
                        API_URL,
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body: JSON.stringify({
                                name: name,
                                email: email,
                                message: message
                            })
                        }
                    );

                // --------------------------------------------
                // READ RESPONSE SAFELY
                // --------------------------------------------

                let result = {};

                const contentType =
                    response.headers.get(
                        "content-type"
                    );

                if (
                    contentType &&
                    contentType.includes(
                        "application/json"
                    )
                ) {
                    result =
                        await response.json();
                } else {
                    const text =
                        await response.text();

                    console.error(
                        "Non-JSON backend response:",
                        text
                    );

                    result = {
                        success: false,
                        message:
                            "The backend returned an unexpected response."
                    };
                }

                console.log(
                    "Contact API response:",
                    result
                );

                // =================================================
                // SUCCESS
                // =================================================

                if (
                    response.ok &&
                    result.success === true &&
                    result.email_sent === true
                ) {
                    form.reset();

                    button.innerHTML = `
                        <i
                            class="fa-solid fa-check"
                            style="margin-right: 8px;">
                        </i>

                        Message Sent
                    `;

                    showNotification(
                        "Thank you! Your message has been received and the email notification was sent successfully.",
                        "success"
                    );

                    setTimeout(() => {
                        button.innerHTML =
                            originalButtonHTML;

                        button.disabled = false;
                    }, 2500);

                    return;
                }

                // =================================================
                // MESSAGE SAVED BUT EMAIL FAILED
                // =================================================

                if (
                    result.success === true &&
                    result.email_sent === false
                ) {
                    console.warn(
                        "Message saved but email delivery failed.",
                        result
                    );

                    showNotification(
                        result.message ||
                        "Your message was received, but the email notification could not be sent.",
                        "error"
                    );

                    button.innerHTML =
                        originalButtonHTML;

                    button.disabled = false;

                    return;
                }

                // =================================================
                // BACKEND ERROR
                // =================================================

                if (
                    response.status === 502
                ) {
                    showNotification(
                        result.message ||
                        "Your message could not be delivered by the email service. Please try again later.",
                        "error"
                    );

                    button.innerHTML =
                        originalButtonHTML;

                    button.disabled = false;

                    return;
                }

                // =================================================
                // SERVER ERROR
                // =================================================

                if (
                    response.status >= 500
                ) {
                    showNotification(
                        "The server is temporarily unavailable. Please try again in a moment.",
                        "error"
                    );

                    button.innerHTML =
                        originalButtonHTML;

                    button.disabled = false;

                    return;
                }

                // =================================================
                // OTHER API ERROR
                // =================================================

                throw new Error(
                    result.message ||
                    "Unable to send the message."
                );

            } catch (error) {
                console.error(
                    "Contact form error:",
                    error
                );

                // =================================================
                // NETWORK / RENDER ERROR
                // =================================================

                if (
                    error instanceof TypeError
                ) {
                    showNotification(
                        "Unable to connect to the portfolio server. Please try again in a moment.",
                        "error"
                    );
                } else {
                    showNotification(
                        error.message ||
                        "Unable to send the message. Please try again.",
                        "error"
                    );
                }

                button.innerHTML =
                    originalButtonHTML;

                button.disabled = false;
            }
        }
    );
});