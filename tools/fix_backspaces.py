"""Replace stray backspace characters (an escaping slip in earlier patches) with the regex word boundary they meant."""
import pathlib
p = pathlib.Path(__file__).resolve().parents[1] / "site" / "index.html"
s = p.read_text(encoding="utf-8")
n = s.count(chr(8))
s = s.replace(chr(8), chr(92) + "b")
p.write_text(s, encoding="utf-8")
print("replaced", n, "backspace characters; left:", s.count(chr(8)))
