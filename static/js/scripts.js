document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('query_form').addEventListener('submit', searchPapers);
    document.getElementById('podcast_form').addEventListener('submit', generatePodcast);
});

async function searchPapers(event) {
    event.preventDefault();
    const queryString = document.getElementById('query_string').value;
    const response = await fetch('/search_papers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query_string: queryString })
    });
    const papers = await response.json();
    if (response.ok) {
        displayPapers(papers);
    } else {
        alert('No papers found for the given query.');
    }
}

function displayPapers(papers) {
    const papersList = document.getElementById('papers_list');
    papersList.innerHTML = '';
    
    const select = document.createElement('select');
    select.name = 'paper';
    select.id = 'paper_select';
    
    papers.forEach(paper => {
        const option = document.createElement('option');
        option.value = paper.id;
        option.textContent = `${paper.title} by ${paper.authors.join(', ')}`;
        select.appendChild(option);
    });
    
    papersList.appendChild(select);
}

async function generatePodcast(event) {
    event.preventDefault();
    var selectedPaperId = document.getElementById('paper_select').value;
    var selectedPaperTitle = document.getElementById('paper_select').options[document.getElementById('paper_select').selectedIndex].text;

    const response = await fetch('/generate_podcast', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ paper_id: selectedPaperId, paper_title: selectedPaperTitle })
    });

    const podcast = await response.json();
    if (response.ok) {
        displayPodcast(podcast);  // Corrected function name
    } else {
        alert('Error generating podcast: ' + podcast.error);
    }
}

function displayPodcast(podcast) {
    const podcastsList = document.getElementById('podcasts_list');
    podcastsList.innerHTML = '';  // Clear previous list if any

    const li = document.createElement('li');
    li.innerHTML = `
        <strong>${podcast.title}</strong>
        <p>${podcast.transcript}</p>
        <audio controls>
            <source src="${podcast.audio_url}" type="audio/mpeg">
            Your browser does not support the audio element.
        </audio>
    `;
    podcastsList.appendChild(li);
}

