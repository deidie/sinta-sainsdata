"""Tests for independent Scopus records including books without GARUDA/DOI."""
import unittest
from ambil_naskah_scopus_author_id import document, merge

class ScopusIndependentTest(unittest.TestCase):
    def test_book_without_doi(self):
        item=document({"eid":"2-s2.0-12345678901","dc:title":"Example Research Handbook",
          "prism:isbn":"9781234567897","prism:aggregationType":"Book",
          "subtypeDescription":"Book","prism:coverDate":"2025-01-01"}, "58996427700")
        self.assertIsNotNone(item)
        self.assertIsNone(item["doi"])
        self.assertEqual(item["isbn"],["9781234567897"])
        self.assertEqual(item["kategori_tampilan"],"buku_atau_bab_buku")
        self.assertEqual(item["scopus_eid"],"2-s2.0-12345678901")

    def test_chapter_without_doi(self):
        item=document({"eid":"2-s2.0-12345678902","dc:title":"Example Chapter",
          "prism:isbn":[{"$":"9781234567897"}],"prism:aggregationType":"Book",
          "subtypeDescription":"Book Chapter","prism:coverDate":"2024-08-12"}, "58190434200")
        self.assertEqual(item["isbn"],["9781234567897"])
        self.assertIsNone(item["doi"])
        self.assertEqual(item["kategori_tampilan"],"buku_atau_bab_buku")

    def test_shared_eid_not_double_counted(self):
        src={"eid":"2-s2.0-12345678903","dc:title":"Example Shared Paper","prism:doi":"10.1234/example",
             "prism:aggregationType":"Journal","prism:coverDate":"2023-12-12"}
        result=merge([document(src,"58996427700"),document(src,"58190434200")])
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]["scopus_author_ids"],["58190434200","58996427700"])

    def test_distinct_chapters_same_book_isbn_not_merged(self):
        book={"dc:title":"Book Chapter Example","prism:isbn":"9781234567897",
              "prism:aggregationType":"Book","subtypeDescription":"Book Chapter"}
        a=document({**book,"eid":"2-s2.0-12345678904"},"57222343067")
        b=document({**book,"eid":"2-s2.0-12345678905"},"57222343067")
        self.assertEqual(len(merge([a,b])),2)

if __name__=="__main__":unittest.main()
