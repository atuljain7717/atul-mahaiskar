/* =========================================================
   ATUL MAHAISKAR PORTFOLIO
   MAIN.JS

   AI Core • Parallax • Cursor Glow
   Magnetic Buttons • Mobile Safety
========================================================= */

document.addEventListener("DOMContentLoaded", () => {

    /* =====================================================
       ELEMENTS
    ===================================================== */

    const hero = document.querySelector(".hero");
    const core = document.querySelector(".ai-core");
    const orbit = document.querySelector(".hero-orbit");
    const buttons = document.querySelectorAll(".hero-buttons .btn");


    /* =====================================================
       SAFETY
    ===================================================== */

    if (!hero) {
        return;
    }


    /* =====================================================
       REDUCED MOTION
    ===================================================== */

    const reducedMotion = window.matchMedia(
        "(prefers-reduced-motion: reduce)"
    ).matches;

    if (reducedMotion) {
        return;
    }


    /* =====================================================
       DEVICE CHECK
    ===================================================== */

    const isTouchDevice =
        window.matchMedia("(hover: none)").matches;


    /* =====================================================
       PARALLAX STATE
    ===================================================== */

    let targetX = 0;
    let targetY = 0;

    let currentX = 0;
    let currentY = 0;


    /* =====================================================
       MOUSE MOVE
    ===================================================== */

    if (!isTouchDevice) {

        hero.addEventListener("mousemove", (event) => {

            const rect = hero.getBoundingClientRect();

            if (!rect.width || !rect.height) {
                return;
            }

            const mouseX =
                (event.clientX - rect.left) / rect.width;

            const mouseY =
                (event.clientY - rect.top) / rect.height;


            /*
             * Keep the movement subtle.
             */

            targetX = (mouseX - 0.5) * 18;
            targetY = (mouseY - 0.5) * 18;


            /* ---------------------------------------------
               CURSOR GLOW
            --------------------------------------------- */

            hero.style.setProperty(
                "--mouse-x",
                `${targetX * 8}px`
            );

            hero.style.setProperty(
                "--mouse-y",
                `${targetY * 8}px`
            );

        });


        /* =================================================
           MOUSE LEAVE
        ================================================= */

        hero.addEventListener("mouseleave", () => {

            targetX = 0;
            targetY = 0;

            hero.style.setProperty(
                "--mouse-x",
                "0px"
            );

            hero.style.setProperty(
                "--mouse-y",
                "0px"
            );

        });

    }


    /* =====================================================
       ANIMATION LOOP
    ===================================================== */

    function animate() {

        /*
         * Smooth interpolation.
         */

        currentX +=
            (targetX - currentX) * 0.05;

        currentY +=
            (targetY - currentY) * 0.05;


        /* =================================================
           AI CORE PARALLAX
        ================================================= */

        if (core) {

            core.style.setProperty(
                "--parallax-x",
                `${currentX * 0.45}px`
            );

            core.style.setProperty(
                "--parallax-y",
                `${currentY * 0.45}px`
            );


            /* ---------------------------------------------
               3D TILT
            --------------------------------------------- */

            core.style.setProperty(
                "--tilt-x",
                `${-currentY * 0.15}deg`
            );

            core.style.setProperty(
                "--tilt-y",
                `${currentX * 0.15}deg`
            );

        }


        /* =================================================
           OUTER ORBIT PARALLAX
        ================================================= */

        if (orbit) {

            orbit.style.setProperty(
                "--orbit-x",
                `${currentX * 0.25}px`
            );

            orbit.style.setProperty(
                "--orbit-y",
                `${currentY * 0.25}px`
            );

        }


        requestAnimationFrame(animate);

    }


    /* =====================================================
       START ANIMATION
    ===================================================== */

    animate();


    /* =====================================================
       MAGNETIC BUTTONS
    ===================================================== */

    if (!isTouchDevice) {

        buttons.forEach((button) => {

            button.addEventListener("mousemove", (event) => {

                const rect =
                    button.getBoundingClientRect();

                const x =
                    event.clientX -
                    rect.left -
                    rect.width / 2;

                const y =
                    event.clientY -
                    rect.top -
                    rect.height / 2;


                const moveX = x * 0.08;
                const moveY = y * 0.08;


                button.style.setProperty(
                    "--button-x",
                    `${moveX}px`
                );

                button.style.setProperty(
                    "--button-y",
                    `${moveY}px`
                );

            });


            button.addEventListener("mouseleave", () => {

                button.style.setProperty(
                    "--button-x",
                    "0px"
                );

                button.style.setProperty(
                    "--button-y",
                    "0px"
                );

            });

        });

    }


    /* =====================================================
       WINDOW RESIZE SAFETY
    ===================================================== */

    window.addEventListener("resize", () => {

        targetX = 0;
        targetY = 0;

    });

});