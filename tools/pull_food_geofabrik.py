"""Cafés, pubs, bars and restaurants from OpenStreetMap (ODbL) via Geofabrik's daily Greater London extract.

    python -X utf8 tools/pull_food_geofabrik.py      # -> data/raw/osm-food.json (then run tools/pull_food.py)

Used when the Overpass API is unreachable. Only the points-of-interest layers are read out of the
208 MB zip, using HTTP range requests, and parsed with a minimal shapefile/dBASE reader (points, and
polygons reduced to the centre of their bounding box). Writes the same shape Overpass returns, so
tools/pull_food.py turns either into site/data/food.json.
"""
import io, json, pathlib, struct, sys, urllib.request, zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "osm-food.json"
URL = "https://download.geofabrik.de/europe/united-kingdom/england/greater-london-latest-free.shp.zip"
UA = "strand-prototype/0.1 (dan.s@systemsdna.com)"
WANT = {"cafe", "pub", "bar", "restaurant", "biergarten"}


class RangeFile(io.RawIOBase):
    """A read-only, seekable view of a remote file, fetched in blocks with HTTP Range."""
    def __init__(self, url):
        self.url = url; self.pos = 0; self.cache = {}
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=60) as r:
            self.url = r.geturl(); self.size = int(r.headers["Content-Length"])
    def seekable(self): return True
    def readable(self): return True
    def tell(self): return self.pos
    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else self.pos + off if whence == 1 else self.size + off
        return self.pos
    def read(self, n=-1):
        if n < 0: n = self.size - self.pos
        n = min(n, self.size - self.pos)
        if n <= 0: return b""
        req = urllib.request.Request(self.url, headers={"User-Agent": UA, "Range": f"bytes={self.pos}-{self.pos + n - 1}"})
        with urllib.request.urlopen(req, timeout=300) as r:
            b = r.read()
        self.pos += len(b)
        return b
    def readinto(self, b):
        d = self.read(len(b)); b[:len(d)] = d; return len(d)


def dbf_rows(data):
    n, hlen, rlen = struct.unpack("<IHH", data[4:12])
    fields, off = [], 32
    while data[off] != 0x0D:
        name = data[off:off + 11].split(b"\0")[0].decode(); flen = data[off + 16]
        fields.append((name, flen)); off += 32
    for i in range(n):
        rec = data[hlen + i * rlen: hlen + (i + 1) * rlen]; p = 1; row = {}
        for name, flen in fields:
            row[name] = rec[p:p + flen].decode("utf-8", "replace").strip(); p += flen
        yield row


def shp_points(data):
    p = 100
    while p < len(data):
        _, clen = struct.unpack(">ii", data[p:p + 8]); body = data[p + 8:p + 8 + clen * 2]; p += 8 + clen * 2
        t = struct.unpack("<i", body[:4])[0]
        if t == 1:
            yield struct.unpack("<dd", body[4:20])
        elif t in (3, 5):
            x0, y0, x1, y1 = struct.unpack("<dddd", body[4:36]); yield ((x0 + x1) / 2, (y0 + y1) / 2)
        else:
            yield (None, None)


def main():
    rf = RangeFile(URL)
    print(f"extract {rf.size/1e6:.0f} MB; reading only the points-of-interest layers", flush=True)
    z = zipfile.ZipFile(io.BufferedReader(rf, buffer_size=1 << 20))
    elements = []
    for layer in ("gis_osm_pois_free_1", "gis_osm_pois_a_free_1"):
        names = {n.rsplit(".", 1)[-1]: n for n in z.namelist() if n.startswith(layer + ".")}
        dbf = z.read(names["dbf"]); shp = z.read(names["shp"])
        print(f"  {layer}: dbf {len(dbf)/1e6:.1f} MB, shp {len(shp)/1e6:.1f} MB", flush=True)
        for row, (x, y) in zip(dbf_rows(dbf), shp_points(shp)):
            if row.get("fclass") in WANT and row.get("name") and x is not None:
                elements.append({"type": "geofabrik", "id": row["osm_id"], "lat": y, "lon": x,
                                 "tags": {"amenity": row["fclass"], "name": row["name"]}})
    RAW.write_text(json.dumps({"elements": elements}), encoding="utf-8")
    print(f"{len(elements)} venues written to {RAW}")


if __name__ == "__main__":
    main()
