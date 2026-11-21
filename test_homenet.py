"""Offline checks for homenet's parsers and block edits. Run: python3 -m unittest test_homenet"""
import importlib.machinery, importlib.util, pathlib, tempfile, unittest

_p = pathlib.Path(__file__).with_name("homenet")
_spec = importlib.util.spec_from_loader("homenet", importlib.machinery.SourceFileLoader("homenet", str(_p)))
hn = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hn)

CADDY = """{
\tadmin 127.0.0.1:2019
}
:80 {
\trespond "ok"
}
# a comment { with a brace
alpha.home.arpa {
\ttls internal
\thandle_path /api/* {
\t\treverse_proxy 10.0.0.1:81 {
\t\t\theader_up Host {host}
\t\t}
\t}
\treverse_proxy 10.0.0.1:80
}
b.home.arpa, c.home.arpa {
\treverse_proxy @m https://10.0.0.2:8443
}
"""

DNS = """[ 192.168.1.3 alpha.home.arpa, 192.168.1.20 vault.home.arpa vault ]
#homenet-dnsmasq
address=/media.home.arpa/192.168.1.3
host-record=sec.home.arpa,192.168.1.3
# cname=old.home.arpa,alpha.home.arpa
"""


class T(unittest.TestCase):
    def test_caddy_sites(self):
        s = hn.parse_caddy(CADDY)
        self.assertEqual(set(s), {"alpha.home.arpa", "b.home.arpa", "c.home.arpa"})
        self.assertEqual(s["alpha.home.arpa"]["backend"], "10.0.0.1:81")
        self.assertEqual(s["c.home.arpa"]["backend"], "https://10.0.0.2:8443")

    def test_dns(self):
        hosts, names, wild = hn.parse_dns(DNS)
        self.assertEqual(len(hosts), 2)
        self.assertEqual(names["vault.home.arpa"], ("192.168.1.20", "pihole"))
        self.assertEqual(names["sec.home.arpa"][1], "dnsmasq")
        self.assertNotIn("old.home.arpa", names)
        self.assertEqual(hn.taken_by("x.media.home.arpa", names, wild, {}), "dnsmasq wildcard address=/media.home.arpa/")

    def test_block_roundtrip(self):
        added = CADDY.rstrip("\n") + "\n\n" + hn.block("new.home.arpa", "10.0.0.9:4400")
        s = hn.parse_caddy(added)
        self.assertTrue(s["new.home.arpa"]["managed"])
        self.assertFalse(s["alpha.home.arpa"]["managed"])
        removed = hn.block_re("new.home.arpa").sub("\n", added, count=1).rstrip("\n") + "\n"
        self.assertEqual(removed, CADDY)

    def test_names(self):
        self.assertEqual(hn.norm_name("Foo"), "foo.home.arpa")
        self.assertEqual(hn.norm_name("a.b.home.arpa."), "a.b.home.arpa")
        for bad in ("-x", "a_b", "x..y"):
            with self.assertRaises(SystemExit):
                hn.norm_name(bad)
        hn.DEFAULT_HOST = "10.0.0.5"
        self.assertEqual(hn.norm_backend("4400"), "10.0.0.5:4400")

    def test_config(self):
        self.addCleanup(setattr, hn, "ZONE", hn.ZONE)
        cfg = ('default_host = "10.0.0.5"\napp_ports = [8000, 8099]\n[pihole]\nip = "10.0.0.2"\nrun = ""\n'
               '[caddy]\nip = "10.0.0.3"\nrun = ""\ncaddyfile = "/etc/caddy/Caddyfile"\n')

        def load(text):
            with tempfile.NamedTemporaryFile("w", suffix=".toml") as f:
                f.write(text); f.flush()
                return hn.load_config(f.name)
        self.assertIn("missing 'caddy'", load(cfg.split("[caddy]")[0]))
        self.assertIn("not a valid DNS name", load('domain = "bad_name"\n' + cfg))
        self.assertIsNone(load('domain = "Lan"\n' + cfg))
        self.assertEqual(hn.norm_name("notes"), "notes.lan")
        self.assertIsNone(hn.OPEN_PORTS)


if __name__ == "__main__":
    unittest.main()
