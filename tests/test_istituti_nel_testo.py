"""Prove del riconoscitore degli istituti.  python -m unittest discover -s tests"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from istituti_nel_testo import codici_dap, pertinente  # noqa: E402


class Istituti(unittest.TestCase):
    def certi(self, t):
        return codici_dap(t)[0]

    def test_soprannomi_senza_contesto(self):
        self.assertEqual(self.certi("Nuova protesta a Poggioreale ieri sera."), ["FF01"])
        self.assertEqual(self.certi("Visita a San Vittore e a Regina Coeli."), ["BB01", "EE02"])
        self.assertEqual(self.certi("Il caso di Marassi"), ["AA02"])

    def test_nomi_comuni_senza_contesto(self):
        for t in ["Un'opera di Verdi alla Scala.", "L'Opera di Roma riapre.", "All'alba di ieri.",
                  "Il fermo è stato convalidato.", "Il Fermo calcio vince.", "Una massa di persone.",
                  "La Augusta Perusia.", "Il porto di Augusta.", "Trani, la cattedrale sul mare.",
                  "Come è noto, il governo...", "Paola Cortellesi al cinema.", "Isili festeggia il patrono."]:
            self.assertEqual(self.certi(t), [], t)

    def test_nomi_comuni_con_contesto(self):
        self.assertEqual(self.certi("Nel carcere di Opera un detenuto..."), ["BB39"])
        self.assertEqual(self.certi("la casa di reclusione di Augusta"), ["KK05"])
        self.assertEqual(self.certi("detenuti trasferiti a Isili"), ["LL05"])
        self.assertEqual(self.certi("Rivolta nel carcere di Fermo"), ["EE16"])
        self.assertEqual(self.certi("Milano Opera, reparto di alta sicurezza"), ["BB39"])

    def test_nome_piu_lungo(self):
        self.assertEqual(self.certi("carcere di Massa Marittima"), ["DD22"])
        self.assertEqual(self.certi("carcere di Massa"), ["AA08"])

    def test_ambigui(self):
        certi, ambigui = codici_dap("Sovraffollamento nel carcere di Roma")
        self.assertEqual(certi, [])
        self.assertIn("EE02", ambigui)
        certi, ambigui = codici_dap("a Rebibbia")
        self.assertEqual(certi, [])
        self.assertEqual(len(ambigui), 4)
        self.assertEqual(codici_dap("nel carcere di Trani femminile")[0], ["FF36"])
        self.assertEqual(sorted(codici_dap("nel carcere di Trani")[1]), ["FF15", "FF36"])

    def test_pertinenza(self):
        self.assertTrue(pertinente("Nuovo suicidio in carcere a Torino"))
        self.assertTrue(pertinente("circolare del DAP sui trasferimenti"))
        self.assertFalse(pertinente("Il dap del frigorifero"))
        self.assertFalse(pertinente("Partita di calcio a Napoli"))


if __name__ == "__main__":
    unittest.main()
