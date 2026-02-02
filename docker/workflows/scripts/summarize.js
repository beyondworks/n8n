/*
 * Smart Summarizer Script
 * Usage: echo "text" | node summarize.js
 *
 * This script currently performs a basic extractive summary.
 * To use with Ollama local LLM:
 * 1. Ensure Ollama is running (e.g., http://host.docker.internal:11434)
 * 2. Pull a model: `ollama pull llama3`
 * 3. Uncomment the Ollama section below and comment out the basic logic.
 */

const fs = require('fs');
const http = require('http');

// Read input from stdin
let inputData = '';

process.stdin.setEncoding('utf8');

process.stdin.on('data', function (chunk) {
	inputData += chunk;
});

process.stdin.on('end', function () {
	if (!inputData || inputData.trim().length === 0) {
		console.log(JSON.stringify({ summary: '' }));
		return;
	}

	// --- MODE 1: Basic Extractive Summary (Default) ---
	const basicSummary = performBasicSummary(inputData);
	console.log(JSON.stringify({ summary: basicSummary }));

	// --- MODE 2: Ollama LLM Summary (Uncomment to use) ---
	// performOllamaSummary(inputData).then(summary => {
	//     console.log(JSON.stringify({ summary: summary }));
	// }).catch(err => {
	//     console.error(err);
	//     // Fallback to basic summary
	//     console.log(JSON.stringify({ summary: performBasicSummary(inputData), error: "Ollama failed" }));
	// });
});

function performBasicSummary(text) {
	// Split into sentences and take the first few
	const sentences = text.split(/(?<=[.!?])\s+/);
	// Take up to 3 sentences or 500 chars
	let summary = '';
	for (const sent of sentences) {
		if ((summary + sent).length > 500) break;
		summary += sent + ' ';
		if (summary.split('.').length > 5) break;
	}
	return summary.trim() + ' (Summarized by Local Script)';
}

// Helper: Call Ollama
function performOllamaSummary(text) {
	return new Promise((resolve, reject) => {
		const postData = JSON.stringify({
			model: 'llama3', // Change model as needed
			prompt: 'Summarize the following text in 3 bullet points, in Korean:\n\n' + text,
			stream: false,
		});

		const options = {
			hostname: 'host.docker.internal', // Access host from container
			port: 11434,
			path: '/api/generate',
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				'Content-Length': Buffer.byteLength(postData),
			},
		};

		const req = http.request(options, (res) => {
			let data = '';
			res.on('data', (chunk) => {
				data += chunk;
			});
			res.on('end', () => {
				try {
					const json = JSON.parse(data);
					if (json.response) {
						resolve(json.response);
					} else {
						reject(new Error('No response from Ollama'));
					}
				} catch (e) {
					reject(e);
				}
			});
		});

		req.on('error', (e) => {
			reject(e);
		});

		req.write(postData);
		req.end();
	});
}
