/* ================= BRAND SELECTOR JAVASCRIPT ================= */

// Data for different car brands and their models
const brandData = {
    'chevrolet': {
        name: 'CHEVROLET',
        models: [
            { name: "Malibu XL", img: "malibu.png" },
            { name: "Cobalt", img: "cobalt.jpg" },
            { name: "Tahoe", img: "tahoe.jpg" },
            { name: "Damas", img: "damas.png" },
            { name: "Tracker", img: "tracker.png" },
            { name: "Onix", img: "onix.png" },
            { name: "Spark", img: "spark.jpg" },
            { name: "Captiva", img: "captiva.jpg" },
            { name: "Nexia", img: "nexia3.png" },
            { name: "Equinox", img: "equinox.png" },
            { name: "Traverse", img: "traverse.png" }
        ]
    },
    'kia': {
        name: 'KIA',
        models: [
            { name: "Optima", img: "optima.jpg" },
            { name: "Sportage", img: "sportage.jpg" },
            { name: "Sorento", img: "sorento.jpg" },
            { name: "Cerato", img: "cerato.jpg" }
        ]
    },
    'skoda': {
        name: 'SKODA',
        models: [
            { name: "Octavia", img: "octavia.jpg" },
            { name: "Fabia", img: "fabia.jpg" },
            { name: "Superb", img: "superb.jpg" }
        ]
    },
    'jac': {
        name: 'JAC',
        models: [
            { name: "T40", img: "t40.jpg" },
            { name: "S2", img: "s2.jpg" },
            { name: "J8", img: "j8.jpg" }
        ]
    },
    'jetour': {
        name: 'JETOUR',
        models: [
            { name: "T-Sport", img: "t-sport.jpg" },
            { name: "X95", img: "x95.jpg" },
            { name: "X70", img: "x70.jpg" }
        ]
    },
    'honqi': {
        name: 'HONQI',
        models: [
            { name: "H1", img: "h1.jpg" },
            { name: "H2", img: "h2.jpg" },
            { name: "H6", img: "h6.jpg" }
        ]
    }
};

let currentBrand = 'chevrolet';
let currentPage = 1;
const perPage = 6;

const panel = document.querySelector(".model-panel");
const carImage = document.getElementById("carImage");
const brandTitle = document.getElementById("brandTitle");

// ================= RENDER MODELS =================

function renderModels() {
    const list = document.getElementById("modelList");
    list.innerHTML = "";

    const models = brandData[currentBrand].models;
    const start = (currentPage - 1) * perPage;
    const end = start + perPage;

    const pageItems = models.slice(start, end);

    pageItems.forEach((model, index) => {
        const btn = document.createElement("button");
        btn.className = "model-btn";
        btn.innerText = model.name;

        btn.onclick = () => {
            carImage.src = "{% static 'images/' %}" + model.img;

            document.querySelectorAll(".model-btn")
                .forEach(b => b.classList.remove("active"));

            btn.classList.add("active");
        };

        // Birinchi model avtomatik tanlanadi
        if (index === 0) {
            btn.classList.add("active");
            carImage.src = "{% static 'images/' %}" + model.img;
        }

        list.appendChild(btn);
    });

    renderPagination();
}

// ================= PAGINATION =================

function renderPagination() {
    const models = brandData[currentBrand].models;
    const totalPages = Math.ceil(models.length / perPage);
    const container = document.getElementById("categoryPagination");

    container.innerHTML = "";

    for (let i = 1; i <= totalPages; i++) {
        const btn = document.createElement("button");
        btn.innerText = i;
        btn.className = "page-btn";

        if (i === currentPage) {
            btn.classList.add("active");
        }

        btn.onclick = () => {
            currentPage = i;
            renderModels();
        };

        container.appendChild(btn);
    }
}

// ================= BRAND SELECTION =================

function selectBrand(el) {
    // Get brand index from position
    const brandItems = Array.from(document.querySelectorAll(".brand-item"));
    const brandIndex = brandItems.indexOf(el);
    const brands = Object.keys(brandData);

    // Agar shu brand allaqachon active va panel ochiq bo'lsa → yopamiz
    if (el.classList.contains("active") && panel.classList.contains("active")) {
        panel.classList.remove("active");
        el.classList.remove("active");
        return;
    }

    // Boshqa brand bosilsa
    document.querySelectorAll(".brand-item")
        .forEach(b => b.classList.remove("active"));

    el.classList.add("active");

    el.scrollIntoView({
        behavior: "smooth",
        block: "center"
    });

    // Set current brand
    if (brandIndex >= 0 && brandIndex < brands.length) {
        currentBrand = brands[brandIndex];
        brandTitle.innerText = brandData[currentBrand].name;
    }

    currentPage = 1;
    renderModels();

    panel.classList.add("active");
}

// ================= PANEL YOPISH =================

function closePanel() {
    panel.classList.remove("active");
    document.querySelectorAll(".brand-item")
        .forEach(b => b.classList.remove("active"));
}

// ================= INIT =================

// Set initial brand title
brandTitle.innerText = brandData[currentBrand].name;
renderModels();

