let empleos = [];
let grafico = null;

window.onload = async function () {
    const response = await fetch("/datos");
    empleos = await response.json();

    if (empleos.length === 0) {
        document.getElementById("mensaje").innerText =
            "No hay datos. Ejecuta primero python main.py";
        return;
    }

    cargarFiltros();
    document.getElementById("mensaje").innerText = "Datos cargados correctamente.";
    mostrarEmpleos();
};

function cargarFiltros() {
    const selectCategoria = document.getElementById("filtroCategoria");
    const selectFuente = document.getElementById("filtroFuente");

    const categorias = [...new Set(empleos.map(e => e.categoria))];
    const fuentes = [...new Set(empleos.map(e => e.fuente))];

    categorias.forEach(categoria => {
        const option = document.createElement("option");
        option.value = categoria;
        option.textContent = categoria;
        selectCategoria.appendChild(option);
    });

    fuentes.forEach(fuente => {
        const option = document.createElement("option");
        option.value = fuente;
        option.textContent = fuente;
        selectFuente.appendChild(option);
    });
}

function mostrarEmpleos() {
    const categoria = document.getElementById("filtroCategoria").value;
    const fuente = document.getElementById("filtroFuente").value;
    const riesgo = document.getElementById("filtroRiesgo").value;

    let filtrados = empleos;

    if (fuente !== "Todas") {
        filtrados = filtrados.filter(e => e.fuente === fuente);
    }

    if (categoria !== "Todas") {
        filtrados = filtrados.filter(e => e.categoria === categoria);
    }

    if (riesgo !== "Todos") {
        filtrados = filtrados.filter(e => e.nivel_riesgo === riesgo);
    }

    actualizarMetricas(filtrados);
    actualizarGrafico(filtrados);
    renderizarOfertas(filtrados);
}

function actualizarMetricas(datos) {
    document.getElementById("total").innerText = datos.length;
    document.getElementById("alto").innerText = datos.filter(e => e.nivel_riesgo === "Alto").length;
    document.getElementById("medio").innerText = datos.filter(e => e.nivel_riesgo === "Medio").length;
    document.getElementById("bajo").innerText = datos.filter(e => e.nivel_riesgo === "Bajo").length;
}

function actualizarGrafico(datos) {
    const alto = datos.filter(e => e.nivel_riesgo === "Alto").length;
    const medio = datos.filter(e => e.nivel_riesgo === "Medio").length;
    const bajo = datos.filter(e => e.nivel_riesgo === "Bajo").length;

    const ctx = document.getElementById("graficoRiesgo");

    if (grafico) {
        grafico.destroy();
    }

    grafico = new Chart(ctx, {
        type: "bar",
        data: {
            labels: ["Alto", "Medio", "Bajo"],
            datasets: [{
                label: "Cantidad de ofertas",
                data: [alto, medio, bajo],
                backgroundColor: ["#dc2626", "#f59e0b", "#16a34a"]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { precision: 0 }
                }
            }
        }
    });
}

function renderizarOfertas(datos) {
    const contenedor = document.getElementById("contenedor");

    contenedor.innerHTML = `
        <h2 class="titulo-ofertas">Ofertas de trabajo analizadas</h2>
    `;

    if (datos.length === 0) {
        contenedor.innerHTML += `
            <div class="oferta">No hay ofertas para este filtro.</div>
        `;
        return;
    }

    datos.forEach(e => {
        const div = document.createElement("div");
        div.className = "oferta";

        div.innerHTML = `
            <h2>${e.titulo}</h2>
            <p><strong>Empresa:</strong> ${e.empresa}</p>
            <p><strong>Fuente:</strong> ${e.fuente}</p>
            <p><strong>Categoría:</strong> ${e.categoria}</p>
            <p><strong>Ubicación:</strong> ${e.ubicacion}</p>
            <p><strong>Salario:</strong> ${e.salario}</p>
            <p><strong>Puntaje de riesgo:</strong> ${e.riesgo}</p>
            <p><strong>Nivel de riesgo:</strong>
                <span class="etiqueta riesgo-${e.nivel_riesgo}">${e.nivel_riesgo}</span>
            </p>
            <p><strong>Razones:</strong> ${e.razones}</p>
            <p class="descripcion"><strong>Descripción:</strong><br>${e.descripcion}</p>
            <p><a href="${e.url}" target="_blank">Ver oferta original</a></p>
        `;

        contenedor.appendChild(div);
    });
}
