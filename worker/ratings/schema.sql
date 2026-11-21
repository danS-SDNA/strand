-- One rating per phone per place: overall stars (optional) and the things it was good for.
CREATE TABLE IF NOT EXISTS ratings (
  device TEXT NOT NULL,
  place  TEXT NOT NULL,
  stars  INTEGER,            -- 1..5, or NULL when only tags were given
  tags   TEXT NOT NULL,      -- comma list from the fixed set
  ts     INTEGER NOT NULL,
  PRIMARY KEY (device, place)
);
CREATE INDEX IF NOT EXISTS ratings_place ON ratings (place);
-- Writes per phone per day, to stop scripted flooding.
CREATE TABLE IF NOT EXISTS daily (
  device TEXT NOT NULL,
  day    TEXT NOT NULL,
  n      INTEGER NOT NULL,
  PRIMARY KEY (device, day)
);
