"""Tes tanpa koneksi internet atau API key untuk pagination Google Scholar."""
import unittest
from unittest.mock import patch
import sinkronisasi_scholar_lengkap as scholar


def sample_articles(start, count):
    return [
        {"title": "Publikasi " + str(i), "year": "2025",
         "publication": "Jurnal Contoh", "citation_id": "id-" + str(i),
         "cited_by": {"value": i}}
        for i in range(start, start + count)
    ]


def reply_for(start):
    if start == 0:
        return {"cited_by": {
                    "table": [{"citations": {"all": 123}}, {"h_index": {"all": 8}},
                              {"i10_index": {"all": 3}}],
                    "graph": [{"year": 2025, "citations": 19}]},
                "articles": sample_articles(0, 100)}
    if start == 100:
        return {"articles": sample_articles(100, 15)}
    raise AssertionError("Permintaan berlebih: " + str(start))


class ScholarFullTests(unittest.TestCase):
    def setUp(self):
        self.old = {
            "slug": "dedi",
            "scholar_url": "https://scholar.google.com/citations?user=16zyvPAAAAAJ&hl=id",
            "artikel_scholar": sample_articles(0, 8),
        }

    def test_all_articles_across_pages(self):
        def fake(author_id, start, key):
            self.assertEqual(author_id, "16zyvPAAAAAJ")
            self.assertEqual(key, "dummy-secret")
            return reply_for(start)
        with patch.object(scholar, "get_serpapi", side_effect=fake) as mocked, patch.object(scholar.time, "sleep"):
            updated = scholar.refresh_author(self.old, "dummy-secret")
        self.assertEqual(mocked.call_count, 2)
        self.assertEqual(len(updated["artikel_scholar"]), 115)
        self.assertEqual(updated["jumlah_artikel_scholar"], 115)
        self.assertTrue(updated["scholar_lengkap"])
        self.assertEqual(updated["metrik_scholar"]["sitasi"], 123)
        self.assertEqual(updated["sitasi_tahunan"]["2025"], 19)

    def test_dont_overwrite_when_article_count_drops(self):
        self.old["artikel_scholar"] = sample_articles(0, 130)
        with patch.object(scholar, "get_serpapi", side_effect=lambda author_id, start, key: reply_for(start)), patch.object(scholar.time, "sleep"):
            with self.assertRaisesRegex(RuntimeError, "lebih kecil"):
                scholar.refresh_author(self.old, "dummy-secret")

    def test_keep_articles_without_year(self):
        a = scholar.convert_article({"title": "Paper without year", "citation_id": "x"})
        self.assertEqual(a["judul"], "Paper without year")
        self.assertIsNone(a["tahun"])

    def test_invalid_profile_url_rejected(self):
        with self.assertRaises(ValueError):
            scholar.scholar_id_from_url("https://example.net/?user=abcdefghijkl")


if __name__ == "__main__":
    unittest.main()
