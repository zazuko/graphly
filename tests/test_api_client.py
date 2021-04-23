# -*- coding: utf-8 -*-
import pytest
from graphly.api_client import SparqlClient


class Test_SparqlClient(object):

    @classmethod
    def setup_class(cls):

        url = "https://ld.zazuko.com/query"
        cls.client = SparqlClient(url)


    test_data = [
        ({"a": "b"}, "PREFIX a: b\n"),
        ({"schema": "<http://schema.org/>", "cube": "<https://cube.link/>"}, "PREFIX schema: <http://schema.org/>\nPREFIX cube: <https://cube.link/>\n"),
    ]
    @pytest.mark.parametrize("input, expected", test_data)
    def test_normalize_prefixes(self, input, expected):

        actual = self.client._normalize_prefixes(input)
        assert actual == expected

    def test_add_prefixes_to_empty(self):

        input = {"France": "Paris", "Italy": "Rome"}
        self.client.add_prefixes(input)
        assert self.client.prefixes == input

    def test_add_prefixes_to_existing(self):

        input = {"Spain": "Madrid"}
        self.client.add_prefixes(input)

        expected = {"France": "Paris", "Italy": "Rome", "Spain": "Madrid"}

        assert input.items() <= self.client.prefixes.items()
        assert self.client.prefixes == expected

    def test_add_prefixes_overwrite(self):

        input = {"Spain": "Barcelona"}
        expected = {"France": "Paris", "Italy": "Rome", "Spain": "Barcelona"}

        self.client.add_prefixes(input)
        assert self.client.prefixes == expected

    def test_remove_prefixes_matching_value(self):

        input = {"Spain": "Barcelona"}
        expected = {"France": "Paris", "Italy": "Rome"}

        self.client.remove_prefixes(input)
        assert self.client.prefixes == expected

    def test_remove_prefixes_mismatching_value(self):

        input = {"France": "Lyon"}
        expected = {"Italy": "Rome"}

        self.client.remove_prefixes(input)
        assert self.client.prefixes == expected

    def test_remove_prefixes_nonexisting_key(self):

        input = {"Here is": "Some nonexistent prefix"}
        expected = {"Italy": "Rome"}

        self.client.remove_prefixes(input)
        assert self.client.prefixes == expected


    def test_format_query_no_init_prefixes_no_prefixes_to_add(self):

        self.client.prefixes = dict()
        input = "Some SPARQL query"
        actual = self.client._format_query(input)
        assert actual == input

    def test_format_query_no_init_prefixes_has_prefixes_to_add(self):

        self.client.prefixes = {"schema": "<http://schema.org/>", "cube": "<https://cube.link/>"}
        input = "Some SPARQL query"
        expected = (
            "PREFIX schema: <http://schema.org/>\n"
            "PREFIX cube: <https://cube.link/>\n"
            "Some SPARQL query"
        )
        actual = self.client._format_query(input)

        assert actual == expected

    def test_format_query_init_prefixes_same_as_prefixes_to_add(self):

        self.client.prefixes = {"schema": "<http://schema.org/>", "cube": "<https://cube.link/>"}
        input = (
            "PREFIX schema: <http://schema.org/>\n"
            "PREFIX cube: <https://cube.link/>\n"
            "Some SPARQL query"
        )
        actual = self.client._format_query(input)

        assert actual == input

    def test_format_query_has_init_prefixes_has_prefixes_to_add_with_overlap(self):

        self.client.prefixes = {"schema": "<http://schema.org/>", "cube": "<https://cube.link/>"}
        input = (
            "PREFIX schema: <http://schema.org/>\n"
            "Some SPARQL query"
        )
        expected = (
            "PREFIX cube: <https://cube.link/>\n"
            "PREFIX schema: <http://schema.org/>\n"
            "Some SPARQL query"
        )
        actual = self.client._format_query(input)

        assert actual == expected

    def test_format_query_has_init_prefixes_has_prefixes_to_add_no_overlap(self):

        self.client.prefixes = {"cube": "<https://cube.link/>"}
        input = (
            "PREFIX schema: <http://schema.org/>\n"
            "Some SPARQL query"
        )
        expected = (
            "PREFIX cube: <https://cube.link/>\n"
            "PREFIX schema: <http://schema.org/>\n"
            "Some SPARQL query"
        )
        actual = self.client._format_query(input)
        assert actual == expected