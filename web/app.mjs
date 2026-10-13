/* Local, exact cosine retrieval over user-provided numeric embeddings. */
export const STORAGE_KEY = "episodic-vector-memory-v1";

export function normalizeVector(vector) {
  if (!Array.isArray(vector) || vector.length < 1 || vector.length > 4096 ||
      vector.some(n => typeof n !== "number" || !Number.isFinite(n))) {
    throw new Error("Embedding must be a JSON array of 1–4096 finite numbers.");
  }
  const norm = Math.hypot(...vector);
  if (!Number.isFinite(norm) || norm === 0) {
    throw new Error("Embedding magnitude must be finite and nonzero.");
  }
  return vector.map(n => n / norm);
}

export function parseVector(value) {
  let parsed;
  try { parsed = JSON.parse(value); }
  catch { throw new Error("Enter a JSON numeric array, for example [1, 0, 0]."); }
  return normalizeVector(parsed);
}

function validMetadata(value) {
  if (value === null || !value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error("Metadata must be a JSON object.");
  }
  return JSON.parse(JSON.stringify(value));
}

export function makeEpisode(id, text, embedding, metadata = {}, timestamp = new Date().toISOString()) {
  if (typeof id !== "string" || !id.trim() || id.length > 128) {
    throw new Error("Episode ID must contain 1–128 characters.");
  }
  if (typeof text !== "string") throw new Error("Episode text must be a string.");
  if (typeof timestamp !== "string") throw new Error("Episode timestamp must be a string.");
  return { id, text, embedding: normalizeVector(embedding), metadata: validMetadata(metadata), timestamp };
}

export function upsertEpisode(episodes, episode) {
  if (episodes.length && episodes[0].embedding.length !== episode.embedding.length) {
    throw new Error("Embedding dimension does not match this collection.");
  }
  return [...episodes.filter(e => e.id !== episode.id), episode].sort((a, b) => a.id.localeCompare(b.id));
}

export function searchEpisodes(episodes, query, topK = 5, minSimilarity = -1) {
  const vector = normalizeVector(query);
  if (!Number.isInteger(topK) || topK < 1 || topK > 100) {
    throw new Error("Result limit must be between 1 and 100.");
  }
  if (typeof minSimilarity !== "number" || !Number.isFinite(minSimilarity) ||
      minSimilarity < -1 || minSimilarity > 1) {
    throw new Error("Minimum similarity must be between -1 and 1.");
  }
  if (episodes.length && episodes[0].embedding.length !== vector.length) {
    throw new Error("Query embedding dimension does not match stored vectors.");
  }
  return episodes.map(e => ({
    ...e, similarity: Math.max(-1, Math.min(1,
      e.embedding.reduce((total, n, i) => total + n * vector[i], 0)))
  })).filter(e => e.similarity >= minSimilarity)
    .sort((a, b) => b.similarity - a.similarity || a.id.localeCompare(b.id)).slice(0, topK);
}

export function importCollection(data) {
  if (!data || data.version !== 1 || !Array.isArray(data.episodes) ||
      data.episodes.length > 1000) {
    throw new Error("Expected version 1 JSON with at most 1000 episodes.");
  }
  let episodes = [];
  for (const input of data.episodes) {
    if (!input || typeof input !== "object") throw new Error("Invalid episode.");
    const item = makeEpisode(input.id, input.text, input.embedding,
                             input.metadata, input.timestamp);
    if (episodes.some(e => e.id === item.id)) throw new Error("Duplicate episode ID in import.");
    episodes = upsertEpisode(episodes, item);
  }
  if (data.dimension !== (episodes[0]?.embedding.length ?? null)) {
    throw new Error("Collection dimension does not match its records.");
  }
  return episodes;
}

export function exportCollection(episodes) {
  return { version: 1, dimension: episodes[0]?.embedding.length ?? null, episodes };
}

function init() {
  const byId = id => document.getElementById(id);
  const notice = byId("notice");
  let episodes = [];
  let results = [];

  function message(text, error = false) {
    notice.textContent = text;
    notice.dataset.error = String(error);
  }

  function persist(next) {
    const body = JSON.stringify(exportCollection(next));
    localStorage.setItem(STORAGE_KEY, body);
    episodes = next;
    render();
  }

  function itemCard(item, includeDelete = false) {
    const article = document.createElement("article");
    article.className = "episode";
    const head = document.createElement("div");
    head.className = "episode-header";
    const title = document.createElement("strong");
    title.textContent = item.id;
    head.append(title);
    if (Number.isFinite(item.similarity)) {
      const score = document.createElement("span");
      score.className = "score";
      score.textContent = "Cosine similarity: " + item.similarity.toFixed(4);
      head.append(score);
    }
    article.append(head);
    const p = document.createElement("p");
    p.textContent = item.text || "(no text)";
    article.append(p);
    const small = document.createElement("small");
    small.textContent = "Vector: [" + item.embedding.map(v => Number(v.toFixed(5))).join(", ") +
      "] · " + item.timestamp;
    article.append(small);
    if (includeDelete) {
      const button = document.createElement("button");
      button.className = "button secondary small";
      button.type = "button";
      button.textContent = "Delete " + item.id;
      button.addEventListener("click", () => {
        try { persist(episodes.filter(e => e.id !== item.id)); results = []; message("Episode deleted."); }
        catch (err) { message(err.message, true); }
      });
      article.append(button);
    }
    return article;
  }

  function render() {
    byId("count").textContent = String(episodes.length);
    byId("dimension").textContent = episodes[0]?.embedding.length ?? "—";
    byId("records").replaceChildren();
    if (!episodes.length) {
      const empty = document.createElement("p");
      empty.className = "muted";
      empty.textContent = "No episodes saved yet. Add the first one above.";
      byId("records").append(empty);
    }
    for (const episode of episodes) byId("records").append(itemCard(episode, true));
    const output = byId("matches");
    output.replaceChildren();
    for (const item of results) output.append(itemCard(item));
  }

  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) episodes = importCollection(JSON.parse(saved));
  } catch (err) {
    message("Saved collection could not be loaded: " + err.message, true);
  }
  render();

  byId("add-form").addEventListener("submit", event => {
    event.preventDefault();
    try {
      const rawMeta = byId("metadata").value.trim();
      const metadata = rawMeta ? JSON.parse(rawMeta) : {};
      const episode = makeEpisode(byId("episode-id").value.trim(), byId("episode-text").value,
                                  parseVector(byId("embedding").value), metadata);
      persist(upsertEpisode(episodes, episode));
      results = [];
      render();
      message("Episode saved on this browser and origin.");
    } catch (err) { message(err.message, true); }
  });

  byId("search-form").addEventListener("submit", event => {
    event.preventDefault();
    try {
      const query = parseVector(byId("query").value);
      results = searchEpisodes(episodes, query, Number(byId("top-k").value),
                               Number(byId("min-similarity").value));
      render();
      message(results.length ? "Found " + results.length + " matching episode(s)." : "No matches.");
    } catch (err) { message(err.message, true); }
  });

  byId("export").addEventListener("click", () => {
    try {
      const url = URL.createObjectURL(new Blob([JSON.stringify(exportCollection(episodes), null, 2)],
                                               { type: "application/json" }));
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "episodic-memory.json";
      document.body.append(anchor);
      anchor.click();
      anchor.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      message("Exported collection as JSON.");
    } catch (err) { message(err.message, true); }
  });

  byId("import").addEventListener("change", async event => {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      if (file.size > 1_000_000) throw new Error("Import file exceeds the 1 MB limit.");
      const imported = importCollection(JSON.parse(await file.text()));
      persist(imported);
      results = [];
      render();
      message("Imported " + imported.length + " episodes (replaced previous collection).");
    } catch (err) { message(err.message, true); }
    finally { event.target.value = ""; }
  });

  byId("clear").addEventListener("click", () => {
    if (!window.confirm("Delete all episodes stored in this browser?")) return;
    try { persist([]); results = []; render(); message("Local collection cleared."); }
    catch (err) { message(err.message, true); }
  });
}
if (typeof document !== "undefined") init();
