
const fs = require('fs');
const path = require('path');

const enPath = '/Users/yoogeon/n8n/packages/frontend/@n8n/i18n/src/locales/en.json';
const koPath = '/Users/yoogeon/n8n/packages/frontend/@n8n/i18n/src/locales/ko.json';

const en = JSON.parse(fs.readFileSync(enPath, 'utf8'));
const ko = JSON.parse(fs.readFileSync(koPath, 'utf8'));

function flatten(obj, prefix = '', res = {}) {
    for (const key in obj) {
        if (typeof obj[key] === 'object' && obj[key] !== null) {
            flatten(obj[key], prefix + key + '.', res);
        } else {
            res[prefix + key] = obj[key];
        }
    }
    return res;
}

const enFlat = flatten(en);
const koFlat = flatten(ko);

const missingInKo = [];
const untranslated = [];

for (const key in enFlat) {
    if (!koFlat.hasOwnProperty(key)) {
        missingInKo.push(key);
    } else if (koFlat[key] === enFlat[key] && typeof enFlat[key] === 'string' && enFlat[key].length > 3 && !enFlat[key].startsWith('@:') && !enFlat[key].includes('{')) {
        // Simple heuristic: exact match, length > 3, not a reference, not a variable only string
        // This might have false positives (proper names etc), but good for a start.
        untranslated.push({key, value: koFlat[key]});
    }
}

console.log('--- Missing Keys in KO ---');
missingInKo.forEach(k => console.log(k));

console.log('--- Potentially Untranslated in KO (Exact Match) ---');
untranslated.forEach(i => console.log(`${i.key}: ${i.value}`));
