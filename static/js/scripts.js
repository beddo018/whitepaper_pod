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
    const selectedPaperId = document.getElementById('paper_select').value;
    const selectedPaperTitle = document.getElementById('paper_select').options[document.getElementById('paper_select').selectedIndex].text;
    
    // Show loading state
    const loadingDiv = document.createElement('div');
    loadingDiv.id = 'loading_indicator';
    loadingDiv.innerHTML = 'Processing paper... This may take a few minutes.';
    document.getElementById('podcasts_list').appendChild(loadingDiv);

    try {
        const response = await fetch('/generate_podcast', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                paper_id: selectedPaperId, 
                paper_title: selectedPaperTitle 
            })
        });

        const result = await response.json();
        if (response.ok) {
            // Start polling for task status
            pollTaskStatus(result.task_id);
        } else {
            throw new Error(result.error || 'Failed to start processing');
        }
    } catch (error) {
        alert('Error generating podcast: ' + error.message);
        document.getElementById('loading_indicator').remove();
    }
}

async function pollTaskStatus(taskId) {
    try {
        const response = await fetch(`/task_status/${taskId}`);
        const result = await response.json();
        
        if (result.status === 'processing') {
            // Continue polling
            setTimeout(() => pollTaskStatus(taskId), 5000); // Poll every 5 seconds
        } else if (result.error) {
            throw new Error(result.error);
        } else {
            // Task completed successfully
            document.getElementById('loading_indicator').remove();
            displayPodcast(result);
        }
    } catch (error) {
        alert('Error checking task status: ' + error.message);
        document.getElementById('loading_indicator').remove();
    }
}

function displayPodcast(podcast) {
    const podcastsList = document.getElementById('podcasts_list');
    
    const li = document.createElement('li');
    li.className = 'podcast-item';
    li.innerHTML = `
        <div class="podcast-header">
            <h3>${podcast.title}</h3>
            <span class="timestamp">${new Date().toLocaleString()}</span>
        </div>
        <div class="podcast-content">
            <div class="transcript">${podcast.transcript}</div>
            <audio controls>
                <source src="${podcast.audio_url}" type="audio/mpeg">
                Your browser does not support the audio element.
            </audio>
        </div>
    `;
    podcastsList.insertBefore(li, podcastsList.firstChild);
}