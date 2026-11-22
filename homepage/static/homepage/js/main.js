// Небольшое поведение интерфейса: год в подвале и поиск по таблицам.

const yearElement = document.getElementById("current-year");

if (yearElement) {
    yearElement.textContent = new Date().getFullYear();
}

// Поле с атрибутом data-filter-table скрывает строки таблицы,
// в тексте которых нет введённой подстроки.
document.querySelectorAll("[data-filter-table]").forEach((input) => {
    const table = document.getElementById(input.dataset.filterTable);
    if (!table) {
        return;
    }
    input.addEventListener("input", () => {
        const query = input.value.trim().toLowerCase();
        table.querySelectorAll("tbody tr").forEach((row) => {
            row.hidden = !row.textContent.toLowerCase().includes(query);
        });
    });
});
