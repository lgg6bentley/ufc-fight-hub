document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll(".fighter-stats").forEach((stat) => {
    setTimeout(() => {
        stat.classList.add("show-stats");
    }, 500); // Delays animation slightly for dramatic effect!
});
    // ✅ Fetch Fighters Data
    fetch('http://localhost:3000/fighters')
        .then(response => response.json())
        .then(fighters => {
            const fightersList = document.getElementById('fighters-list');
            if (fightersList) {
                fightersList.innerHTML = '';
                fighters.forEach(fighter => {
                    const div = document.createElement('div');
                    div.className = 'fighter';
                    const imagePath = fighter.image_url ? fighter.image_url : "images/default.jpg";

                    div.innerHTML = `
                        <img src="${imagePath}" alt="${fighter.name}">
                        <h2>${fighter.name}</h2>
                        <p><strong>Weight Class:</strong> ${fighter.weight_class}</p>
                        <p><strong>Record:</strong> ${fighter.wins}W - ${fighter.losses}L - ${fighter.draws}D</p>
                    `;
                    fightersList.appendChild(div);
                });
            }
        })
        .catch(error => console.error('Error fetching fighters:', error));

    // ✅ Fetch Upcoming Fights from Local Database
    fetch('http://localhost:3000/upcoming-fights')
        .then(response => response.json())
        .then(fights => {
            const upcomingList = document.getElementById('upcoming-fights');
            if (upcomingList) {
                upcomingList.innerHTML = '';
                fights.forEach(fight => {
                    const div = document.createElement('div');
                    div.className = 'fight-card';

                    div.innerHTML = `
                        <h2>${fight.fighter1} vs. ${fight.fighter2}</h2>
                        <p><strong>Event:</strong> ${fight.event_name}</p>
                        <p><strong>Date:</strong> ${fight.date}</p>
                        <p><strong>Location:</strong> ${fight.location}</p>
                        <p><strong>Weight Class:</strong> ${fight.weight_class}</p>
                    `;
                    upcomingList.appendChild(div);
                });
            }
        })
        .catch(error => console.error('Error fetching upcoming fights:', error));

    // ✅ Fetch Real-Time Fight Card from UFC Stats API
    fetch('https://api.ufcstats.com/upcoming-fights')
        .then(response => response.json())
        .then(fights => {
            console.log("Fetched Fight Data:", fights);

            if (!Array.isArray(fights)) {
                console.error("Error: Expected an array but got", typeof fights);
                return;
            }

            const upcomingList = document.getElementById('upcoming-fights');
            if (upcomingList) {
                upcomingList.innerHTML = '';

                fights.forEach(fight => {
                    const div = document.createElement('div');
                    div.className = 'fight-card';

                    div.innerHTML = `
                        <h2>${fight.fighter1} vs. ${fight.fighter2}</h2>
                        <p><strong>Event:</strong> ${fight.event_name}</p>
                        <p><strong>Date:</strong> ${fight.date}</p>
                        <p><strong>Location:</strong> ${fight.location}</p>
                        <p><strong>Weight Class:</strong> ${fight.weight_class}</p>
                    `;
                    upcomingList.appendChild(div);
                });
            }
        })
        .catch(error => console.error('Error fetching UFC fight card:', error));

    // ✅ Fetch Fight Card from Backend (`fight-card`)
    fetch('http://localhost:3000/fight-card')
        .then(response => response.json())
        .then(fights => {
            console.log("Fetched Backend Fight Data:", fights);

            const upcomingList = document.getElementById('upcoming-fights');
            if (upcomingList) {
                upcomingList.innerHTML = '';

                fights.forEach(fight => {
                    const div = document.createElement('div');
                    div.className = 'fight-card';

                    div.innerHTML = `
                        <h2>${fight.fighter1} vs. ${fight.fighter2}</h2>
                        <p><strong>Event:</strong> ${fight.event_name}</p>
                        <p><strong>Date:</strong> ${fight.date}</p>
                        <p><strong>Location:</strong> ${fight.location}</p>
                        <p><strong>Weight Class:</strong> ${fight.weight_class}</p>
                    `;
                    upcomingList.appendChild(div);
                });
            }
        })
        .catch(error => console.error('Error fetching backend fight card:', error));
});

fetch('/fight-card')
    .then(response => response.json())
    .then(fights => {
        const fightContainer = document.getElementById("fight-card");

        fights.forEach(fight => {
            fightContainer.innerHTML += `
                <div class="fight-card">
                    <div class="fighter">
                        <img src="${fight.fighter1_image}" alt="${fight.fighter1}" class="fighter-img">
                        <span class="fighter-name">${fight.fighter1}</span>
                    </div>
                    <div class="vs">vs.</div>
                    <div class="fighter">
                        <img src="${fight.fighter2_image}" alt="${fight.fighter2}" class="fighter-img">
                        <span class="fighter-name">${fight.fighter2}</span>
                    </div>
                </div>
            `;
        });
    })
    .catch(error => console.error("Error loading fight card:", error));