
/* =========================================
   CONFIGURATION
========================================= */

const API_URL =
    "http://127.0.0.1:8000/recommend";


/* =========================================
   ELEMENTS
========================================= */

const recommendButton =
    document.getElementById(
        "recommendButton"
    );


const queryInput =
    document.getElementById(
        "query"
    );


const daysInput =
    document.getElementById(
        "days"
    );


const budgetInput =
    document.getElementById(
        "budget"
    );


const tripTypeInput =
    document.getElementById(
        "trip-type"
    );


const travellerInput =
    document.getElementById(
        "traveller"
    );


const activitiesInput =
    document.getElementById(
        "activities"
    );


const loading =
    document.getElementById(
        "loading"
    );


const results =
    document.getElementById(
        "results"
    );


const recommendation =
    document.getElementById(
        "recommendation"
    );


const planAgain =
    document.getElementById(
        "planAgain"
    );


/* =========================================
   GENERATE TRAVEL PLAN
========================================= */

recommendButton.addEventListener(
    "click",
    async function () {

        const query =
            queryInput.value.trim();


        /* Validate query */

        if (!query) {

            alert(
                "Please describe your travel requirements."
            );

            queryInput.focus();

            return;
        }


        /* =====================================
           BUILD COMPLETE QUERY
        ===================================== */

        let fullQuery = query;


        if (daysInput.value) {

            fullQuery +=
                `\n\nNumber of days: ${daysInput.value}`;

        }


        if (budgetInput.value) {

            fullQuery +=
                `\nBudget: ${budgetInput.value}`;

        }


        if (tripTypeInput.value) {

            fullQuery +=
                `\nTrip type: ${tripTypeInput.value}`;

        }


        if (travellerInput.value) {

            fullQuery +=
                `\nTraveller type: ${travellerInput.value}`;

        }


        if (activitiesInput.value.trim()) {

            fullQuery +=
                `\nPreferred activities: ${activitiesInput.value.trim()}`;

        }


        /* =====================================
           UI - LOADING
        ===================================== */

        loading.classList.remove(
            "hidden"
        );


        results.classList.add(
            "hidden"
        );


        recommendButton.disabled =
            true;


        recommendButton.querySelector(
            "span:last-child"
        ).textContent =
            "Generating...";


        try {


            /* =================================
               SEND REQUEST TO FASTAPI
            ================================= */

            const response =
                await fetch(
                    API_URL,
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body:
                            JSON.stringify({
                                query:
                                    fullQuery
                            })
                    }
                );


            /* =================================
               CHECK RESPONSE
            ================================= */

            if (!response.ok) {

                let errorMessage =
                    `Server returned ${response.status}`;


                try {

                    const errorData =
                        await response.json();


                    if (
                        errorData.detail
                    ) {

                        errorMessage =
                            errorData.detail;

                    }

                } catch (error) {

                    /* Ignore JSON parsing error */

                }


                throw new Error(
                    errorMessage
                );
            }


            /* =================================
               READ RESPONSE
            ================================= */

            const data =
                await response.json();


            if (
                !data.recommendation
            ) {

                throw new Error(
                    "No recommendation was returned by the server."
                );

            }


            /* =================================
               RENDER MARKDOWN
            ================================= */

            if (
                typeof marked !==
                "undefined"
            ) {

                recommendation.innerHTML =
                    marked.parse(
                        data.recommendation
                    );

            } else {

                /*
                 * Fallback if Markdown library
                 * is unavailable.
                 */

                recommendation.textContent =
                    data.recommendation;

            }


            /* =================================
               SHOW RESULTS
            ================================= */

            results.classList.remove(
                "hidden"
            );


            setTimeout(
                function () {

                    results.scrollIntoView({
                        behavior: "smooth",
                        block: "start"
                    });

                },
                100
            );


        } catch (error) {


            /* =================================
               ERROR HANDLING
            ================================= */

            console.error(
                "Travel RAG Error:",
                error
            );


            alert(
                "Unable to generate your travel plan.\n\n"
                + error.message
                + "\n\n"
                + "Make sure FastAPI and the RAG backend are running."
            );


        } finally {


            /* =================================
               RESET UI
            ================================= */

            loading.classList.add(
                "hidden"
            );


            recommendButton.disabled =
                false;


            recommendButton.querySelector(
                "span:last-child"
            ).textContent =
                "Generate Travel Plan";

        }

    }
);


/* =========================================
   PLAN ANOTHER TRIP
========================================= */

planAgain.addEventListener(
    "click",
    function () {

        results.classList.add(
            "hidden"
        );


        document
            .getElementById("planner")
            .scrollIntoView({
                behavior: "smooth"
            });

    }
);


/* =========================================
   ENTER KEY SUPPORT
========================================= */

queryInput.addEventListener(
    "keydown",
    function (event) {

        /*
         * Ctrl + Enter generates
         * the recommendation.
         */

        if (
            event.ctrlKey &&
            event.key === "Enter"
        ) {

            recommendButton.click();

        }

    }
);
