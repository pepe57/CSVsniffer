#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright © 2024 W. García
Creative Commons Attribution 4.0 | https://creativecommons.org/licenses/by/4.0/

GENERAL INFO:
This class module deals with computation of the table uniformity as described in the paper
"Detecting CSV file dialects by table uniformity measurement and data type inference", available 
at https://content.iospress.com/articles/data-science/ds240062.

Enhanced with a twist: Improved tau_0 using MAD, tau_1 with entropy, added tau_2 (type coherence) and tau_3 (structural entropy),
and a refined overall score method. Integrates with type_detection.py for type inference and csv_dialect.py for dialect handling.

Reimplemented per user feedback: Total field scores summed and divided by num_cols for lambda_sum; final terms divided by threshold for tau_0 and by n for others to adjust for n >= threshold.

"""

import math
import statistics  # For median
from typing import List
from collections import Counter
from type_detection import type_detector, trip_quotes
from csv_dialect import Dialect

class t_uniformity:
    """
    This container holds methods for compute Table Uniformity parameters, with enhancements from the twist.

    Parameters
    ----------
    table : list[list[str]]
        Target table, typically parsed using a Dialect from csv_dialect.py.
    dialect : Dialect
        Dialect used to parse the table, for accurate type inference.
    """
    def __init__(
        self,
        table: list,  # list[list[str]]
        dialect: Dialect, 
        lambda_sum: float
    ) -> None:
        self.table = table
        self.dialect = dialect
        self.lambda_sum = 0

    def validate(self) -> None:
        if self.table is None:
            raise ValueError(
                "The target table should be provided, got: %r"
                % self.table
            )
        if self.dialect is None:
            raise ValueError(
                "The dialect should be provided, got: %r"
                % self.dialect
            )

    def avg_fields(self) -> float:
        nk = 0
        for record in self.table:
            nk += len(record)
        return nk / len(self.table) if self.table else 0.0

    def compute_type_scores(self) -> List[float]:
        """Compute type scores per column and per rows using type_detector; average per column for tau_2."""
        if not self.table:
            return []
        num_cols = max(len(row) for row in self.table) if self.table else 0
        num_rows = len(self.table)
        column_scores = [0.0] * num_cols
        total_field_scores = 0.0
        detector = type_detector()
        for row in self.table:
            for col_idx, field in enumerate(row):
                if col_idx < num_cols:
                    cleaned_field = trip_quotes(field, self.dialect)
                    is_quoted = field.startswith(self.dialect.quotechar) and field.endswith(self.dialect.quotechar)
                    field_type = detector.detect_type(cleaned_field, is_quoted)
                    score = 100.0 if field_type is not None else 0.1
                    total_field_scores += score
                    column_scores[col_idx] += score
        # Average per rows for tau_2
        column_averages = [score / num_rows if num_rows > 0 else 0.0 for score in column_scores]
        self.lambda_sum = total_field_scores / num_cols if num_cols > 0 else 0.0
        return column_averages

    def compute_tau2(self, column_scores: List[float]) -> float:
        """Column type coherence (tau_2)."""
        if not column_scores:
            return 0.0
        mean_score = sum(column_scores) / len(column_scores)
        variances = [abs(score - mean_score) for score in column_scores]
        max_var = max(variances) if max(variances) > 0 else 1.0
        tau2 = sum(1 - (v / max_var) for v in variances) / len(variances)
        return tau2

    def compute_tau3(self) -> float:
        """Structural entropy (tau_3)."""
        row_structures = []
        for row in self.table:
            structure = tuple(len(cell) for cell in row)  # Simple structure hash
            row_structures.append(structure)
        n = len(row_structures)
        if n == 0:
            return 0.0
        freq = Counter(row_structures)
        entropy = 0.0
        for count in freq.values():
            p = count / n
            if p > 0:
                entropy -= p * math.log2(p)
        return entropy

    def compute(self) -> List[float]:
        self.validate()
        n = len(self.table)  # Number of records
        if n == 0:
            return [0.0, 0.0, 0.0, 0.0, 0.0]  # tau0, tau1, tau2, tau3, lambda_sum

        # Field lengths
        field_lengths = [len(record) for record in self.table]

        # Improved tau_0 with MAD
        if n > 1:
            med = statistics.median(field_lengths)
            devs = [abs(k - med) for k in field_lengths]
            mad = statistics.median(devs) * 1.4826
            tau_0 = 1 / (1 + 2 * mad) if (1 + 2 * mad) != 0 else 1.0
        else:
            tau_0 = 1.0  # Single row is consistent

        # Original parts for tau_1
        phi = self.avg_fields()
        mu, c, sm, alpha, beta = 0, 0, 0, 0, 0
        k_max = field_lengths[0] if field_lengths else 0
        k_min = field_lengths[0] if field_lengths else 0
        for i in range(n):
            k_i = field_lengths[i]
            mu += math.pow(k_i - phi, 2)
            if i == 0:
                c += 1
                if n == 1:
                    sm = c
            else:
                if k_i > k_max:
                    k_max = k_i
                if k_i < k_min:
                    k_min = k_i
                k_prev = field_lengths[i - 1]
                if k_prev != k_i:
                    alpha += 1
                    if c > sm:
                        sm = c
                    c = 0
                else:
                    c += 1
                    if i == n - 1:
                        if c > sm:
                            sm = c
        r = k_max - k_min
        if alpha > 0 and sm > 0:
            beta = sm / n
            base_tau_1 = 2 * r * (math.pow(alpha, 2) + 1) * ((1 - beta) / sm)
        else:
            base_tau_1 = 0.0

        # Improved tau_1 with entropy
        freq = Counter(field_lengths)
        entropy_h = 0.0
        for count in freq.values():
            p = count / n
            if p > 0:
                entropy_h -= p * math.log2(p)
        tau_1 = base_tau_1 * (1 + entropy_h)

        # Type scores for tau_2
        column_scores = self.compute_type_scores()

        # tau_2
        tau_2 = self.compute_tau2(column_scores)

        # tau_3
        tau_3 = self.compute_tau3()

        # lambda_sum as total field scores / num_cols
        lambda_sum = self.lambda_sum

        return [tau_0, tau_1, tau_2, tau_3, lambda_sum]

    def overall_score(self, delta: float = 1.0) -> float:
        """Refined overall score omega'."""
        metrics = self.compute()
        tau_0, tau_1, tau_2, tau_3, lambda_sum = metrics
        n = len(self.table)
        if tau_1 + n == 0 or tau_3 + 1 == 0:
            return 0.0
        score = (tau_0 / delta) + (1 / (tau_1 + n)) + (tau_2 / n) + (1 / ((1 + tau_3) * n)) * lambda_sum
        return score