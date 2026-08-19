// ============================================================
// PATHPROBE-AI DASHBOARD
// Frontend Controller
// ============================================================

let lossChart = null;
let delayChart = null;
let throughputChart = null;


// ============================================================
// INITIALIZATION
// ============================================================

document.addEventListener("DOMContentLoaded", () => {

    setupNavigation();

    loadDashboard();

});


// ============================================================
// LOAD DASHBOARD DATA
// ============================================================

async function loadDashboard() {

    try {

        const response = await fetch("/api/dashboard", {
            cache: "no-store"
        });

        if (!response.ok) {
            throw new Error(
                `Dashboard API returned ${response.status}`
            );
        }

        const data = await response.json();

        console.log("PathProbe-AI dashboard data:", data);

        updateOverview(data);

        updateInvestigation(data);

        updateNetworkCharts(data);

        updateAdaptiveProbing(data);

        updateEvaluation(data);

    }
    catch (error) {

        console.error(
            "Dashboard loading error:",
            error
        );

        showDashboardError(error);

    }

}


// ============================================================
// OVERVIEW
// ============================================================

function updateOverview(data) {

    const project =
        data.project || {};

    const investigation =
        data.investigation || {};

    const diagnosis =
        investigation.diagnosis ||
        "UNKNOWN";

    const confidence =
        Number(investigation.confidence || 0);

    const probes =
        investigation.probes || 0;

    const reduction =
        investigation.probe_reduction || 0;

    const environment =
        investigation.environment ||
        "—";


    setText(
        "diagnosis",
        diagnosis
    );

    setText(
        "diagnosisEnvironment",
        `Environment ${environment}`
    );

    setText(
        "confidence",
        `${Math.round(confidence * 100)}%`
    );

    setText(
        "probes",
        probes
    );

    setText(
        "probeReduction",
        `${reduction}% reduction`
    );


    const updated =
        data.final_evaluation?.generated_at ||
        investigation.timestamp;

    if (updated) {

        const date =
            new Date(updated);

        setText(
            "lastUpdated",
            `Updated ${date.toLocaleString()}`
        );

    }

}


// ============================================================
// INVESTIGATION
// ============================================================

function updateInvestigation(data) {

    const investigation =
        data.investigation || {};

    const diagnosis =
        investigation.diagnosis ||
        "UNKNOWN";

    const confidence =
        Number(
            investigation.confidence || 0
        );

    const environment =
        investigation.environment ||
        "—";

    const probes =
        investigation.probes ||
        0;

    const reduction =
        investigation.probe_reduction ||
        0;


    setText(
        "bigDiagnosis",
        diagnosis
    );

    setText(
        "confidenceBadge",
        `${Math.round(confidence * 100)}% CONFIDENCE`
    );

    setText(
        "environment",
        environment
    );

    setText(
        "investigationProbes",
        probes
    );

    setText(
        "investigationReduction",
        `${reduction}%`
    );


    // Diagnosis visual state

    const diagnosisElements = [
        document.getElementById("diagnosis"),
        document.getElementById("bigDiagnosis")
    ];

    diagnosisElements.forEach(element => {

        if (!element) return;

        element.classList.remove(
            "diagnosis-normal",
            "diagnosis-rate-limited",
            "diagnosis-delay"
        );

        if (diagnosis === "NORMAL") {

            element.classList.add(
                "diagnosis-normal"
            );

        }

        else if (
            diagnosis === "RATE_LIMITED"
        ) {

            element.classList.add(
                "diagnosis-rate-limited"
            );

        }

        else if (
            diagnosis === "DELAY"
        ) {

            element.classList.add(
                "diagnosis-delay"
            );

        }

    });

}


// ============================================================
// NETWORK SIGNATURE CHARTS
// ============================================================

function updateNetworkCharts(data) {

    const environments =
        data.environments || {};

    const labels = [
        "10",
        "25",
        "50",
        "100",
        "200",
        "500"
    ];


    const environmentOrder = [
        "E0",
        "E1",
        "E2"
    ];


    const names = {
        E0: "E0 NORMAL",
        E1: "E1 RATE LIMITED",
        E2: "E2 DELAY"
    };


    const datasetsLoss = [];
    const datasetsDelay = [];
    const datasetsThroughput = [];


    environmentOrder.forEach(
        environment => {

            const observations =
                environments[environment] || [];


            datasetsLoss.push({

                label:
                    names[environment],

                data:
                    observations.map(
                        item => item.loss
                    ),

                tension: 0.25,

                borderWidth: 2,

                pointRadius: 4

            });


            datasetsDelay.push({

                label:
                    names[environment],

                data:
                    observations.map(
                        item => item.delay
                    ),

                tension: 0.25,

                borderWidth: 2,

                pointRadius: 4

            });


            datasetsThroughput.push({

                label:
                    names[environment],

                data:
                    observations.map(
                        item => item.throughput
                    ),

                tension: 0.25,

                borderWidth: 2,

                pointRadius: 4

            });

        }
    );


    const commonOptions = {

        responsive: true,

        maintainAspectRatio: false,

        interaction: {
            mode: "index",
            intersect: false
        },

        plugins: {

            legend: {
                display: true
            },

            tooltip: {
                enabled: true
            }

        },

        scales: {

            x: {

                title: {
                    display: true,
                    text: "Probe Rate (packets/sec)"
                }

            },

            y: {

                beginAtZero: true

            }

        }

    };


    // -------------------------
    // PACKET LOSS
    // -------------------------

    const lossCanvas =
        document.getElementById(
            "lossChart"
        );

    if (lossCanvas) {

        if (lossChart) {
            lossChart.destroy();
        }

        lossChart =
            new Chart(
                lossCanvas,
                {

                    type: "line",

                    data: {

                        labels,

                        datasets:
                            datasetsLoss

                    },

                    options: {

                        ...commonOptions,

                        scales: {

                            x: {

                                title: {
                                    display: true,
                                    text:
                                        "Probe Rate (packets/sec)"
                                }

                            },

                            y: {

                                beginAtZero: true,

                                title: {
                                    display: true,
                                    text:
                                        "Packet Loss (%)"
                                }

                            }

                        }

                    }

                }
            );

    }


    // -------------------------
    // DELAY
    // -------------------------

    const delayCanvas =
        document.getElementById(
            "delayChart"
        );

    if (delayCanvas) {

        if (delayChart) {
            delayChart.destroy();
        }

        delayChart =
            new Chart(
                delayCanvas,
                {

                    type: "line",

                    data: {

                        labels,

                        datasets:
                            datasetsDelay

                    },

                    options: {

                        ...commonOptions,

                        scales: {

                            x: {

                                title: {
                                    display: true,
                                    text:
                                        "Probe Rate (packets/sec)"
                                }

                            },

                            y: {

                                beginAtZero: true,

                                title: {
                                    display: true,
                                    text:
                                        "Average Delay (ms)"
                                }

                            }

                        }

                    }

                }
            );

    }


    // -------------------------
    // THROUGHPUT
    // -------------------------

    const throughputCanvas =
        document.getElementById(
            "throughputChart"
        );

    if (throughputCanvas) {

        if (throughputChart) {
            throughputChart.destroy();
        }

        throughputChart =
            new Chart(
                throughputCanvas,
                {

                    type: "line",

                    data: {

                        labels,

                        datasets:
                            datasetsThroughput

                    },

                    options: {

                        ...commonOptions,

                        scales: {

                            x: {

                                title: {
                                    display: true,
                                    text:
                                        "Probe Rate (packets/sec)"
                                }

                            },

                            y: {

                                beginAtZero: true,

                                title: {
                                    display: true,
                                    text:
                                        "Throughput (Mbps)"
                                }

                            }

                        }

                    }

                }
            );

    }

}


// ============================================================
// ADAPTIVE VS FIXED
// ============================================================

function updateAdaptiveProbing(data) {

    const adaptive =
        data.final_evaluation?.adaptive_vs_fixed ||
        {};

    const results =
        data.adaptive_results ||
        [];


    // -------------------------
    // Comparison rows
    // -------------------------

    const container =
        document.getElementById(
            "comparisonRows"
        );


    if (container) {

        container.innerHTML = "";


        results.forEach(result => {

            const row =
                document.createElement("div");

            row.className =
                "comparison-row";


            row.innerHTML = `

                <span>
                    ${result.environment}
                </span>

                <span>
                    ${result.actual}
                </span>

                <span>
                    ${result.adaptive}
                    <small>
                        (${result.adaptive_probes} probes)
                    </small>
                </span>

                <span>
                    ${result.fixed}
                    <small>
                        (${result.fixed_probes} probes)
                    </small>
                </span>

            `;


            container.appendChild(row);

        });

    }


    // -------------------------
    // Efficiency
    // -------------------------

    const reduction =
        Number(
            adaptive.probe_reduction_percent || 0
        );

    const adaptiveAverage =
        Number(
            adaptive.adaptive_average_probes || 0
        );

    const fixedAverage =
        Number(
            adaptive.fixed_average_probes || 0
        );


    setText(
        "savingValue",
        `${reduction.toFixed(2)}%`
    );

    setText(
        "adaptiveAvg",
        adaptiveAverage.toFixed(2)
    );

    setText(
        "fixedAvg",
        fixedAverage.toFixed(2)
    );

}


// ============================================================
// FINAL EVALUATION
// ============================================================

function updateEvaluation(data) {

    const evaluation =
        data.final_evaluation || {};


    const adaptive =
        evaluation.adaptive_vs_fixed ||
        {};

    const robustness =
        evaluation.robustness ||
        {};

    const perturbation =
        evaluation.perturbation ||
        {};

    const endToEnd =
        evaluation.end_to_end ||
        {};


    setText(
        "adaptiveAccuracy",
        `${Number(
            adaptive.adaptive_accuracy_percent || 0
        ).toFixed(2)}%`
    );


    setText(
        "robustnessAccuracy",
        `${Number(
            robustness.accuracy_percent || 0
        ).toFixed(2)}%`
    );


    setText(
        "perturbationAccuracy",
        `${Number(
            perturbation.accuracy_percent || 0
        ).toFixed(2)}%`
    );


    setText(
        "endToEndAccuracy",
        `${Number(
            endToEnd.accuracy_percent || 0
        ).toFixed(2)}%`
    );


    setText(
        "overallAccuracy",
        `${Number(
            evaluation.overall_accuracy_percent || 0
        ).toFixed(2)}%`
    );

}


// ============================================================
// NAVIGATION
// ============================================================

function setupNavigation() {

    const navItems =
        document.querySelectorAll(
            ".nav-item"
        );

    const sections =
        document.querySelectorAll(
            "main section[id]"
        );


    // Smooth navigation

    navItems.forEach(item => {

        item.addEventListener(
            "click",
            event => {

                event.preventDefault();

                const href =
                    item.getAttribute("href");

                if (!href) return;

                const target =
                    document.querySelector(
                        href
                    );

                if (!target) return;

                target.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });

            }
        );

    });


    // Automatically highlight active section

    const observer =
        new IntersectionObserver(
            entries => {

                entries.forEach(entry => {

                    if (
                        entry.isIntersecting
                    ) {

                        navItems.forEach(
                            item => {

                                item.classList.remove(
                                    "active"
                                );

                            }
                        );


                        const active =
                            document.querySelector(
                                `.nav-item[href="#${entry.target.id}"]`
                            );


                        if (active) {

                            active.classList.add(
                                "active"
                            );

                        }

                    }

                });

            },
            {

                root: null,

                threshold: 0.25,

                rootMargin:
                    "-80px 0px -50% 0px"

            }
        );


    sections.forEach(
        section =>
            observer.observe(section)
    );

}


// ============================================================
// ERROR DISPLAY
// ============================================================

function showDashboardError(error) {

    const status =
        document.querySelector(
            ".system-status strong"
        );

    if (status) {

        status.textContent =
            "BACKEND ERROR";

    }


    console.error(
        "PathProbe-AI:",
        error
    );

}


// ============================================================
// HELPER
// ============================================================

function setText(
    id,
    value
) {

    const element =
        document.getElementById(id);

    if (element) {

        element.textContent =
            value;

    }

}


// ============================================================
// AUTO REFRESH
// ============================================================

// Refresh dashboard every 30 seconds.

setInterval(
    () => {

        loadDashboard();

    },
    30000
);
