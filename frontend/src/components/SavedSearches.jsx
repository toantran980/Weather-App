import { useEffect, useState } from "react";

export default function SavedSearches({ place, locationName, fahrenheit, api, jsonRequest, formatTemperature }) {
  const [dateRange, setDateRange] = useState({ start: "", end: "", note: "" });
  const [savedSearches, setSavedSearches] = useState([]);
  const [message, setMessage] = useState("");
  const temperature = (value) => formatTemperature(value, fahrenheit);

  async function refresh() {
    try {
      setSavedSearches(await api("/api/searches"));
    } catch {
      // The saved searches list is optional until the backend is ready
    }
  }

  useEffect(() => { refresh(); }, []);

  async function saveSearch() {
    if (!place) return setMessage("Search for a location first.");
    try {
      await api("/api/searches", jsonRequest("POST", {
        location: place,
        start_date: dateRange.start,
        end_date: dateRange.end,
        note: dateRange.note,
      }));
      setMessage("Saved.");
      refresh();
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function editSearch(record) {
    const startDate = prompt("Start date (YYYY-MM-DD)", record.start_date);
    const endDate = startDate && prompt("End date (YYYY-MM-DD)", record.end_date);
    const note = endDate && prompt("Note", record.note);
    if (!startDate || !endDate || note === null) return;
    try {
      await api(`/api/searches/${record.id}`, jsonRequest("PUT", { start_date: startDate, end_date: endDate, note }));
      refresh();
    } catch (error) {
      alert(error.message);
    }
  }

  async function deleteSearch(searchId) {
    if (!confirm("Delete this saved search?")) return;
    try {
      await api(`/api/searches/${searchId}`, { method: "DELETE" });
    } catch (error) {
      alert(error.message);
    }
    refresh();
  }

  function averageTemperature(record, key) {
    return record.temps.reduce((total, day) => total + day[key], 0) / record.temps.length;
  }

  return (
    <>
      <section className="panel save-panel">
        <div className="section-heading">
          <div><p className="eyebrow">KEEP A RECORD</p><h2>Save a date range</h2></div>
          {place && <span className="section-note">{locationName || place}</span>}
        </div>
        <div className="save-form">
          <label><span>From</span><input type="date" aria-label="Start date" value={dateRange.start} onChange={(event) => setDateRange({ ...dateRange, start: event.target.value })} /></label>
          <label><span>To</span><input type="date" aria-label="End date" value={dateRange.end} onChange={(event) => setDateRange({ ...dateRange, end: event.target.value })} /></label>
          <label className="note-field"><span>Note <em>optional</em></span><input placeholder="Add a note" value={dateRange.note} onChange={(event) => setDateRange({ ...dateRange, note: event.target.value })} /></label>
          <button className="button button-primary" type="button" onClick={saveSearch}>Save search</button>
        </div>
        {message && <p className="inline-message" role="status">{message}</p>}
      </section>

      <section className="panel saved-panel">
        <div className="section-heading">
          <div><p className="eyebrow">YOUR WEATHER NOTES</p><h2>Saved searches</h2></div>
          <form className="export-form" action="/api/export" method="get">
            <label className="visually-hidden" htmlFor="export-format">Export format</label>
            <select id="export-format" name="format" defaultValue="csv"><option value="csv">CSV</option><option value="json">JSON</option></select>
            <button className="export-link" type="submit"><span aria-hidden="true">↓</span> Export</button>
          </form>
        </div>
        {savedSearches.length === 0 ? <p className="empty-state">No saved searches yet. Save a location and date range to see it here.</p> : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Location</th><th>Dates</th><th>Avg high / low</th><th>Note</th><th><span className="visually-hidden">Actions</span></th></tr></thead>
              <tbody>{savedSearches.map((record) => (
                <tr key={record.id}>
                  <td>{record.name}</td><td>{record.start_date} to {record.end_date}</td>
                  <td>{temperature(averageTemperature(record, "max_c"))} / {temperature(averageTemperature(record, "min_c"))}</td>
                  <td>{record.note}</td>
                  <td><div className="row-actions"><button className="text-button" onClick={() => editSearch(record)}>Edit</button><button className="text-button danger-button" onClick={() => deleteSearch(record.id)}>Delete</button></div></td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        )}
      </section>
    </>
  );
}
