
// ============================================================
// ATUL MAHAISKAR PORTFOLIO
// CONTACT FORM JAVASCRIPT
// PREMIUM SUCCESS / ERROR NOTIFICATION
// ============================================================

document.addEventListener("DOMContentLoaded", () => {

    const form = document.querySelector(".contact-form");

    if (!form) {
        console.error("Contact form not found.");
        return;
    }


    // ========================================================
    // FLASK API
    // ========================================================

    const API_URL ="https://atul-mahaiskar-backend.onrender.com/api/contact";


    // ========================================================
    // CREATE NOTIFICATION
    // ========================================================

    function showNotification(message, type = "success") {

        // Remove existing notification
        const existing =
            document.querySelector(".contact-notification");

        if (existing) {
            existing.remove();
        }


        // Create notification
        const notification =
            document.createElement("div");

        notification.className =
            `contact-notification ${type}`;


        // Icon
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


        document.body.appendChild(
            notification
        );


        // Small delay for animation
        requestAnimationFrame(() => {

            notification.classList.add(
                "show"
            );

        });


        // Close button
        const closeButton =
            notification.querySelector(
                ".notification-close"
            );

        closeButton.addEventListener(
            "click",
            () => {

                closeNotification(
                    notification
                );

            }
        );


        // Auto close
        setTimeout(() => {

            closeNotification(
                notification
            );

        }, 5000);

    }


    // ========================================================
    // CLOSE NOTIFICATION
    // ========================================================

    function closeNotification(
        notification
    ) {

        if (!notification) {
            return;
        }

        notification.classList.remove(
            "show"
        );

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
                // RESPONSE
                // --------------------------------------------

                const result =
                    await response.json();


                console.log(
                    "Contact API response:",
                    result
                );


                // --------------------------------------------
                // SUCCESS
                // --------------------------------------------

                if (
                    response.ok &&
                    result.success
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
                        "Thank you! Your message has been received successfully. I'll get back to you soon.",
                        "success"
                    );


                    setTimeout(() => {

                        button.innerHTML =
                            originalButtonHTML;

                        button.disabled = false;

                    }, 2500);


                    return;

                }


                // --------------------------------------------
                // API ERROR
                // --------------------------------------------

                throw new Error(
                    result.message ||
                    "Unable to send the message."
                );


            } catch (error) {

                console.error(
                    "Contact form error:",
                    error
                );


                showNotification(
                    "Unable to send the message. Please try again.",
                    "error"
                );


                button.innerHTML =
                    originalButtonHTML;

                button.disabled = false;

            }

        }
    );

});


