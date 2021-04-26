# ,*, coding: utf,8 ,*,
import datetime
import json
import os

import geopandas as gpd
import pandas as pd
import pytest
from graphly.api_client import SparqlClient
from graphly import exceptions
from shapely import wkt

FILES_PATH = ["tests", "input"]


class Test_SparqlClient(object):
    @classmethod
    def setup_class(cls):

        url = "https://ld.zazuko.com/query"
        cls.client = SparqlClient(url)

    test_data = [
        ({"a": "b"}, "PREFIX a: b\n"),
        (
            {"schema": "<http://schema.org/>", "cube": "<https://cube.link/>"},
            "PREFIX schema: <http://schema.org/>\nPREFIX cube: <https://cube.link/>\n",
        ),
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

        self.client.prefixes = {
            "schema": "<http://schema.org/>",
            "cube": "<https://cube.link/>",
        }
        input = "Some SPARQL query"
        expected = (
            "PREFIX schema: <http://schema.org/>\n"
            "PREFIX cube: <https://cube.link/>\n"
            "Some SPARQL query"
        )
        actual = self.client._format_query(input)

        assert actual == expected

    def test_format_query_init_prefixes_same_as_prefixes_to_add(self):

        self.client.prefixes = {
            "schema": "<http://schema.org/>",
            "cube": "<https://cube.link/>",
        }
        input = (
            "PREFIX schema: <http://schema.org/>\n"
            "PREFIX cube: <https://cube.link/>\n"
            "Some SPARQL query"
        )
        actual = self.client._format_query(input)

        assert actual == input

    def test_format_query_has_init_prefixes_has_prefixes_to_add_with_overlap(self):

        self.client.prefixes = {
            "schema": "<http://schema.org/>",
            "cube": "<https://cube.link/>",
        }
        input = "PREFIX schema: <http://schema.org/>\n" "Some SPARQL query"
        expected = (
            "PREFIX cube: <https://cube.link/>\n"
            "PREFIX schema: <http://schema.org/>\n"
            "Some SPARQL query"
        )
        actual = self.client._format_query(input)

        assert actual == expected

    def test_format_query_has_init_prefixes_has_prefixes_to_add_no_overlap(self):

        self.client.prefixes = {"cube": "<https://cube.link/>"}
        input = "PREFIX schema: <http://schema.org/>\n" "Some SPARQL query"
        expected = (
            "PREFIX cube: <https://cube.link/>\n"
            "PREFIX schema: <http://schema.org/>\n"
            "Some SPARQL query"
        )
        actual = self.client._format_query(input)
        assert actual == expected

    def test__normalize_results_date(self):

        with open(os.path.join(*FILES_PATH, "date.json")) as file:
            input = json.load(file)

        actual = self.client._normalize_results(input)
        data = {
            "time": [datetime.date(1408, 12, 31), datetime.date(1467, 12, 31)],
            "place": ["Kreis 1", "Kreis 2"],
        }
        expected = pd.DataFrame(data)

        assert actual.equals(expected)

    def test__normalize_results_datetime(self):

        with open(os.path.join(*FILES_PATH, "datetime.json")) as file:
            input = json.load(file)

        actual = self.client._normalize_results(input)
        data = {
            "time": [
                datetime.datetime(2001, 10, 26, 21, 32, 32),
                datetime.datetime(2001, 11, 26, 10, 32, 32),
            ],
            "place": ["Kreis 1", "Kreis 2"],
        }
        expected = pd.DataFrame(data)

        assert actual.equals(expected)

    def test__normalize_results_float_decimal_double(self):

        data = {"count": [56.59, 47.12], "place": ["Kreis 1", "Kreis 2"]}
        expected = pd.DataFrame(data)

        for file in ["decimal.json", "double.json", "float.json"]:
            with open(os.path.join(*FILES_PATH, file)) as file:
                input = json.load(file)

            actual = self.client._normalize_results(input)
            assert actual.equals(expected)

    def test__normalize_results_integer(self):

        data = {"count": [56, 47], "place": ["Kreis 1", "Kreis 2"]}
        expected = pd.DataFrame(data)

        with open(os.path.join(*FILES_PATH, "integer.json")) as file:
            input = json.load(file)

        actual = self.client._normalize_results(input)
        assert actual.equals(expected)

    def test__normalize_results_literal(self):

        data = {"capital": ["Rome", "Bern"], "country": ["Italy", "Switzerland"]}
        expected = pd.DataFrame(data)

        with open(os.path.join(*FILES_PATH, "literal.json")) as file:
            input = json.load(file)

        actual = self.client._normalize_results(input)
        assert actual.equals(expected)

    def test__normalize_results_wktLiteral(self):

        data = {
            "place": ["Enge", "Hirslanden"],
            "geometry": [
                wkt.loads("Point(8.53172 47.36410)"),
                wkt.loads("Point(8.56628 47.36464)"),
            ],
        }
        expected = gpd.GeoDataFrame(data)

        with open(os.path.join(*FILES_PATH, "wktLiteral.json")) as file:
            input = json.load(file)

        actual = self.client._normalize_results(input)

        assert actual.equals(expected)

    def test_send_query_no_results(self):

        query = """
        SELECT *
        WHERE {<inexistentNode> ?p ?o}
        """

        with pytest.raises(exceptions.NotFoundError):
            self.client.send_query(query)

    def test_send_query_triplestore_error(self):

        query = """
        SELECT *
        """

        with pytest.raises(exceptions.ExecutionError):
            self.client.send_query(query)

    def test_send_query_valid_query(self):

        query = """
        SELECT *
        WHERE {?s ?p ?o}
        LIMIT 5
        """

        res = self.client.send_query(query)

        assert type(res) == pd.core.frame.DataFrame
        assert len(res) == 5
        assert list(res.columns) == ["s", "p", "o"]