import { meals } from '../api.js';

export async function render(container) {
    container.innerHTML = `
        <div class="meals-view">
            <header class="view-header">
                <h1>Meal Planner</h1>
            </header>
            <div class="meals-grid" id="meals-container">
                <!-- Days of the week -->
            </div>
        </div>
    `;

    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    const mealData = await meals.list();

    const containerDiv = document.getElementById('meals-container');
    containerDiv.innerHTML = days.map(day => {
        const dayMeals = mealData.filter(m => m.day_of_week === day);
        return `
            <div class="card day-card">
                <h3>${day}</h3>
                <div class="day-meals">
                    ${dayMeals.map(m => `
                        <div class="meal-item">
                            <span class="type">${m.meal_type}:</span>
                            <span class="desc">${m.description}</span>
                        </div>
                    `).join('') || '<p class="muted">No meals planned</p>'}
                </div>
            </div>
        `;
    }).join('');
}
