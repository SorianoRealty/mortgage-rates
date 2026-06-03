// update-rates.js
// Runs in GitHub Actions every Thursday.
// Fetches Freddie Mac PMMS 30Y and 15Y rates from FRED, writes rates.json.
// FHA / VA are estimated client-side as spreads off the 30Y, so we don't store them here.

const fs = require('fs');

const FRED_KEY = process.env.FRED_API_KEY;
if (!FRED_KEY) {
  console.error('Missing FRED_API_KEY env var.');
  process.exit(1);
}

const FRED_BASE = 'https://api.stlouisfed.org/fred/series/observations';
// We fetch ~60 weeks of history so the page can show ~1Y trend + 52w yearly delta
const LIMIT = 60;

async function fetchSeries(seriesId) {
  const url = `${FRED_BASE}?series_id=${seriesId}&api_key=${FRED_KEY}`
            + `&file_type=json&sort_order=desc&limit=${LIMIT}`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`FRED ${seriesId} returned HTTP ${res.status}: ${await res.text()}`);
  }
  const data = await res.json();
  return data.observations
    .filter(o => o.value !== '.')
    .map(o => ({ date: o.date, value: parseFloat(o.value) }))
    .reverse(); // chronological
}

(async () => {
  try {
    const [hist30, hist15] = await Promise.all([
      fetchSeries('MORTGAGE30US'),
      fetchSeries('MORTGAGE15US'),
    ]);

    const out = {
      updated: new Date().toISOString(),
      latestDate: hist30[hist30.length - 1].date,
      rate30: hist30,
      rate15: hist15,
    };

    fs.writeFileSync('rates.json', JSON.stringify(out, null, 2) + '\n');
    console.log(`Wrote rates.json — 30Y latest ${hist30.at(-1).value}%, 15Y latest ${hist15.at(-1).value}% (as of ${out.latestDate}).`);
  } catch (err) {
    console.error('Update failed:', err);
    process.exit(1);
  }
})();
