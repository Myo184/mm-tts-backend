document.getElementById('btn').addEventListener('click', async () => {
    const text = document.getElementById('text').value;
    const voice = document.getElementById('voice').value;
    const rate = document.getElementById('rate').value + '%';
    
    const btn = document.getElementById('btn');
    btn.innerText = "Generating...";
    btn.disabled = true;

    try {
        const response = await fetch("https://my-myanmar-tts.onrender.com/api/tts", {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({text, voice, rate, pitch: "+0Hz"})
        });

        const data = await response.json(); // Data ကို အမှန်ကန်ဆုံး ဖတ်ယူခြင်း
        
        // Audio
        const audio = document.getElementById('audio');
        audio.src = "data:audio/mp3;base64," + data.audio;
        
        // Downloads
        document.getElementById('dlMp3').href = audio.src;
        document.getElementById('dlMp3').download = "recap.mp3";
        
        const srtBlob = new Blob([data.srt], {type: 'text/plain'});
        document.getElementById('dlSrt').href = URL.createObjectURL(srtBlob);
        document.getElementById('dlSrt').download = "recap.srt";
        
        document.getElementById('result').classList.remove('hidden');
    } catch (e) {
        alert("Error: " + e.message);
    } finally {
        btn.innerText = "Generate";
        btn.disabled = false;
    }
});
