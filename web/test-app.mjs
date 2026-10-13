import test from "node:test";
import assert from "node:assert/strict";
import {
  normalizeVector, parseVector, makeEpisode, upsertEpisode,
  searchEpisodes, importCollection, exportCollection
} from "./app.mjs";

test("normalizes finite nonzero vectors and rejects invalid input", () => {
  assert.deepEqual(normalizeVector([3, 4]), [0.6, 0.8]);
  assert.throws(() => parseVector("[0, 0]"), /nonzero/);
  assert.throws(() => parseVector("[NaN, 1]"), /JSON/);
  assert.throws(() => normalizeVector([Infinity]), /finite/);
  assert.throws(() => normalizeVector([true]), /numbers/);
});

test("upsert and exact cosine ordering", () => {
  let records = [];
  records = upsertEpisode(records, makeEpisode("opposite", "", [-1, 0]));
  records = upsertEpisode(records, makeEpisode("same", "similar episode", [1, 0]));
  records = upsertEpisode(records, makeEpisode("orthogonal", "", [0, 1]));
  const matches = searchEpisodes(records, [1, 0], 2);
  assert.deepEqual(matches.map(m => m.id), ["same", "orthogonal"]);
  assert.equal(matches[0].similarity, 1);
  assert.deepEqual(searchEpisodes(records, [1, 0], 5, 0.5).map(m => m.id), ["same"]);
  assert.throws(() => searchEpisodes(records, [0, 1, 1]), /dimension/);
  assert.throws(() => upsertEpisode(records, makeEpisode("bad", "", [1, 2, 3])), /dimension/);
});

test("JSON export/import round trip and malformed import rejection", () => {
  const items = [makeEpisode("1", "<img src=x onerror=alert(1)>", [1, 2], {label:"safe"})];
  const serialized = exportCollection(items);
  assert.deepEqual(importCollection(serialized), items);
  assert.throws(() => importCollection({...serialized, dimension: 3}), /dimension/);
  assert.throws(() => importCollection({...serialized, episodes: [...items, ...items]}), /Duplicate/);
  assert.throws(() => importCollection({version:2, episodes:[]}), /version 1/);
});

test("upserting an existing ID replaces rather than appends", () => {
  const first = makeEpisode("repeat", "old", [1, 2]);
  const result = upsertEpisode([first], makeEpisode("repeat", "new", [2, 1]));
  assert.equal(result.length, 1);
  assert.equal(result[0].text, "new");
});
