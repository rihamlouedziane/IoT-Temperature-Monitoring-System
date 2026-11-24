
document.addEventListener("DOMContentLoaded", function () {

    const temperatureCanvas = document.getElementById("temperatureChart");
    const humidityCanvas = document.getElementById("humidityChart");

    if (typeof Chart === "undefined") {
        console.error("Chart.js n'est pas chargé.");
        return;
    }

    if (!temperatureCanvas || !humidityCanvas) {
        console.error("Les graphiques sont introuvables.");
        return;
    }

    const labels = JSON.parse(
        document.getElementById("labels-data").textContent
    );

    const temperatures = JSON.parse(
        document.getElementById("temperature-data").textContent
    );

    const humidites = JSON.parse(
        document.getElementById("humidity-data").textContent
    );

    const dates = JSON.parse(
        document.getElementById("dates-data").textContent
    );

    function creerGraphique(canvas, titre, valeurs, couleur, unite) {

        return new Chart(canvas.getContext("2d"), {
            type: "bar",

            data: {
                labels: labels,

                datasets: [{
                    label: titre,
                    data: valeurs,
                    backgroundColor: couleur,
                    borderColor: couleur,
                    borderWidth: 1,
                    borderRadius: 5,
                    maxBarThickness: 35
                }]
            },

            options: {
                responsive: true,
                maintainAspectRatio: false,

                plugins: {
                    legend: {
                        display: false
                    },

                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                return titre + " : " +
                                    context.parsed.y + unite;
                            }
                        }
                    }
                },

                scales: {
                    x: {
                        title: {
                            display: true,
                            text: "Heure / Date"
                        },

                        ticks: {
                            autoSkip: true,
                            maxTicksLimit: 24,
                            maxRotation: 45,
                            minRotation: 0
                        }
                    },

                    y: {
                        beginAtZero: titre === "Humidité",
                        title: {
                            display: true,
                            text: titre + " (" + unite + ")"
                        }
                    }
                },

                onClick: function (event, elements) {

                    if (elements.length === 0) {
                        return;
                    }

                    const index = elements[0].index;
                    const date = dates[index];

                    if (date) {
                        window.location.href = "/jour/" + date + "/";
                    }
                }
            }
        });
    }

    // Graphique de température
    creerGraphique(
        temperatureCanvas,
        "Température",
        temperatures,
        "rgba(239, 125, 65, 0.75)",
        " °C"
    );

    // Graphique d'humidité
    creerGraphique(
        humidityCanvas,
        "Humidité",
        humidites,
        "rgba(45, 145, 210, 0.75)",
        " %"
    );

});
