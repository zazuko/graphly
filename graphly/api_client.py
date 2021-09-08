# -*- coding: utf-8 -*-
import re
import time
from datetime import date, datetime
from typing import Dict, Optional, Union

import geopandas as gpd
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from shapely import wkt

from graphly.exceptions import ExecutionError, NotFoundError

FIND_PATTERN = "PREFIX\\s*(.*?)\n"
SPLIT_PATTERN = ":\\s*"

DATA_TYPES_TO_PYTHON_CLS = {
    "http://www.w3.org/2001/XMLSchema#integer": int,
    "http://www.w3.org/2001/XMLSchema#float": float,
    "http://www.w3.org/2001/XMLSchema#double": float,
    "http://www.w3.org/2001/XMLSchema#decimal": float,
    "http://www.w3.org/2001/XMLSchema#date": date.fromisoformat,
    "http://www.w3.org/2001/XMLSchema#dateTime": (
        lambda x: datetime.strptime(x, "%Y-%m-%dT%H:%M:%S")
    ),
    "http://www.opengis.net/ont/geosparql#wktLiteral": wkt.loads,
    "http://www.openlinksw.com/schemas/virtrdf#Geometry": wkt.loads,
}

GEODATA_TYPES = set(
    [
        "http://www.opengis.net/ont/geosparql#wktLiteral",
        "http://www.openlinksw.com/schemas/virtrdf#Geometry",
    ]
)


def requests_retry_session(
    retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 504), session=None
):

    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


class SparqlClient:
    def __init__(self, base_url: str = None, timeout: Optional[int] = 15) -> None:
        self.BASE_URL = base_url
        self.last_request = 0
        self.HEADERS = {
            "Accept": "application/sparql-results+json",
        }
        self.prefixes = dict()
        self.timeout = timeout

    def _normalize_prefixes(self, prefixes: Dict) -> str:
        """Transfrom prefixes map to SPARQL-readable format
        Args:
            prefixes: 		prefixes to be normalized

        Returns
            str             SPARQL-readable prefix definition
        """

        normalized_prefixes = "\n".join(
            "PREFIX %s" % ": ".join(map(str, x)) for x in prefixes.items()
        )
        if normalized_prefixes:
            normalized_prefixes += "\n"
        return normalized_prefixes

    def add_prefixes(self, prefixes: Dict) -> None:
        """Define prefixes to be added to every query
        Args:
            prefixes: 		prefixes to be added to every query

        Returns
            None
        """

        self.prefixes = {**self.prefixes, **prefixes}

    def remove_prefixes(self, prefixes: Dict) -> None:
        """Remove prefixes from the prefixes are added to every query
        Args:
            prefixes: 		prefixes to be removed from self.prefixes

        Returns
            None
        """

        for prefix in prefixes:
            self.prefixes.pop(prefix, None)

    def _format_query(self, query: str) -> str:
        """Format SPARQL query to include in-memory prefixes.
        Prefixes already defined in the query have precedence, and are not overwritten.
            Args:
                query: 				user-defined SPARQL query

            Returns
                str:	            SPARQL query with predefined prefixes
        """

        prefixes_in_query = dict(
            [
                re.split(SPLIT_PATTERN, prefix, 1)
                for prefix in re.findall(FIND_PATTERN, query)
            ]
        )
        prefixes_to_add = {
            k: v for (k, v) in self.prefixes.items() if k not in prefixes_in_query
        }

        return self._normalize_prefixes(prefixes_to_add) + query

    def send_query(self, query: str, timeout: Optional[int] = 0) -> pd.DataFrame:
        """Send SPARQL query. Transform results to pd.DataFrame.
        Args:
            query: 				full SPARQL query
            timeout:

        Returns
            pd.DataFrame	    query results
        """

        session = requests_retry_session()
        request = {"query": self._format_query(query)}

        if time.time() < self.last_request + 1:
            time.sleep(1)
        self.last_request = time.time()

        if timeout == 0:
            timeout = self.timeout

        if timeout is None:
            response = session.get(
                self.BASE_URL, headers=self.HEADERS, params=request, timeout=timeout
            )
        else:
            response = session.get(self.BASE_URL, headers=self.HEADERS, params=request)
        response.raise_for_status()
        response = response.json()

        if "head" not in response:
            raise ExecutionError(
                "{}\n Triplestore error code: {}".format(
                    response["message"], response["code"]
                )
            )

        if not response["results"]["bindings"]:
            raise NotFoundError()

        return self._normalize_results(response)

    def _normalize_results(
        self, response: Dict
    ) -> Union[pd.DataFrame, gpd.GeoDataFrame]:
        """Normalize response from SPARQL endpoint. Transform json structure to table. Convert observations to python data types.
        Args:
            response: 			raw response from SPARQL endpoint

        Returns
            pd.DataFrame	    response from SPARQL endpoint in a tabular form, with python data types
        """

        cols = response["head"]["vars"]
        data = dict(zip(cols, [[] for i in range(len(cols))]))

        has_geo_data = False
        for row in response["results"]["bindings"]:
            for key in cols:

                if key in row:

                    value = row[key]["value"]
                    if "datatype" in row[key]:
                        datatype = row[key]["datatype"]
                        value = DATA_TYPES_TO_PYTHON_CLS[datatype](value)

                        if datatype in GEODATA_TYPES:
                            has_geo_data = True
                            geometry_col = key

                else:
                    value = None

                data[key].append(value)

        if has_geo_data:
            return gpd.GeoDataFrame.from_dict(data).set_geometry(col=geometry_col)
        else:
            return pd.DataFrame.from_dict(data)
