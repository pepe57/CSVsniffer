#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright © 2024 W. García
Creative Commons Attribution 4.0 | https://creativecommons.org/licenses/by/4.0/

GENERAL INFO:
This is the core class module to perform dialect detection as described in the paper
"Detecting CSV file dialects by table uniformity measurement and data type inference", available 
at https://content.iospress.com/articles/data-science/ds240062.

Enhanced with a twist: Uses improved table uniformity metrics (tau_0 with MAD, tau_1 with entropy, new tau_2 and tau_3)
and a refined overall score (omega') from table_uniformity.py.

"""

from typing import List
from csv_dialect import Dialect
from table_def import table_constructor 
from table_uniformity import t_uniformity

class t_score:
    """
    This container holds methods for compute the table score.

    Parameters
    ----------
    csv_path : str
        Path to the target CSV file.
    dialect : Dialect
        Configuration used to load the data from the CSV.
    threshold : int
        Count of records to load from CSV file, default value is 10.
    encoding : str
        Codec to be used to read the CSV file.
    """
    def __init__(
        self,
        csv_path: str,
        dialect: Dialect,
        threshold: int = 10,
        encoding: str = 'utf_8',
    ) -> None:
        self.csv_path = csv_path
        self.dialect = dialect
        self.threshold = threshold
        self.encoding = encoding

    def validate(self) -> None:
        if self.csv_path is None or len(self.csv_path) == 0:
            raise ValueError(
                "The path to the target CSV file should be provided, got: %r"
                % self.csv_path
            )
        if self.dialect is None or not self.dialect.validate:
            raise ValueError(
                "The dialect should be provided, got: %r"
                % self.dialect
            )

    def compute(self) -> float:
        self.validate()
        # Initialize table object
        table_obj = table_constructor(file_path=self.csv_path, threshold=self.threshold, encoding=self.encoding)
        sample = table_obj.fromCSV(_dialect=self.dialect)
        # Compute table uniformity with twist-enhanced metrics
        uniformity = t_uniformity(table=sample, dialect=self.dialect)
        return uniformity.overall_score(delta=self.threshold)