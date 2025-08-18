#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from typing import List
from csv_dialect import Dialect
from table_score_MAD_EPY import t_score
from potential_dialects import p_dialects
from csv_sniffer_MAD_EPY import sniffer

def main(basePath:str, fileName:str):
    #Parent folder
    mainPath = os.path.dirname(basePath)
    #CSV file path
    CSVpath = os.path.join(mainPath, 'testing CSV')
    filePath = os.path.join(CSVpath, fileName)
    #Sniff dialect
    iDialect = sniffer.sniff(sniffer(filePath,
                                     threshold=50,
                                     delimiter_list=[',', ';', '\t','|', ':', '=', ' ', '#', '*'])
                                     )
    """
    or
        obj_sniffer = sniffer(filePath,threshold=25)
        iDialect = obj_sniffer.sniff()
    """
    print(iDialect)

if __name__ == "__main__":
    #Working dir
    path = os.getcwd()
    """
    +[act.csv]: gets correct delimiter and quote character. Previous implementations was picking ';'
    ~+[baselog.csv]: gets correct delimiter. Previous implementations was picking '|'
    X[bugs.csv]: Fails as previous
    X[diamonds.csv]: Fails to get fixed width spaced files
    ~+[iometeroutput.csv]: gets correct delimiter. Previous implementations was picking ':'
    +[items.csv]: gets correct delimiter and quote character. Previous implementations was picking '='
    X[register_data.csv]: Fails as previous
    +[resources.csv]: gets correct delimiter and quote character. Previous implementations was picking ','
    +[simulation.csv]: gets correct delimiter and quote character. Previous implementations was picking ','
    """
    filename = 'simulation.csv'
    main(path, filename)