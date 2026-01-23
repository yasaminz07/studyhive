// ===== Scroll reveal =====
const reveals = document.querySelectorAll(".reveal");

function revealOnScroll() {
    const windowHeight = window.innerHeight;
    reveals.forEach(el => {
        const top = el.getBoundingClientRect().top;
        if (top < windowHeight - 100) {
            el.classList.add("visible");
        }
    });
}

window.addEventListener("scroll", revealOnScroll);
revealOnScroll();

// ===== Accordion =====
document.querySelectorAll(".accordion").forEach(card => {
    card.addEventListener("click", () => {
        card.classList.toggle("open");
    });
});

// ===== Animated counters =====
const counters = document.querySelectorAll(".stat-number");
let countersStarted = false;

function startCounters() {
    if (countersStarted) return;

    const statsSection = document.querySelector(".about-stats");
    if (!statsSection) return;

    const rect = statsSection.getBoundingClientRect();
    if (rect.top < window.innerHeight) {
        countersStarted = true;

        counters.forEach(counter => {
            const target = +counter.dataset.target;
            let current = 0;
            const step = target / 60;

            function update() {
                current += step;
                if (current < target) {
                    counter.innerText = Math.floor(current);
                    requestAnimationFrame(update);
                } else {
                    counter.innerText = target;
                }
            }
            update();
        });
    }
}

window.addEventListener("scroll", startCounters);
startCounters();
