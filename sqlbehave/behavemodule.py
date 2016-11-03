import os, glob
import parse
from lxml import etree
from datetime import datetime, date, time

from sqlbehave.testmodule import connect_config, step_types, link_config

class ModuleStep:
    pass

class FileSqlBehaveModule:

    def __init__(self, module_name, revision = None):
        self.module_name = module_name
        self.features = dict()
        self.steps = dict()
    
    def get_steps(self):
        predicate_format = "{step_type} {predicate}"
        connect_value_tmpl = "--!connect={value}"

        for st in step_types:
            filetemplate = "./features/steps/" + predicate_format + ".sql"
            for g in glob.iglob(filetemplate.format(step_type=st, predicate="*")):
                filename = os.path.basename(os.path.splitext(g)[0])
                ms = ModuleStep()
                ms.id_predicate_type = step_types[st]
                
                p = parse.parse(predicate_format, filename)
                try:
                    ms.predicate = p.named["predicate"]
                except:
                    continue

                with open(g, 'r') as f:
                    ms.sql_test_command = ""
                    for line in f:
                        if not hasattr(ms, "id_server"):
                            p = parse.parse(connect_value_tmpl, line)
                            if p != None and len(p.named) > 0:
                                vl = p.named['value']
                                for id_server, connect in connect_config.items():
                                    if connect == vl:
                                        ms.id_server = id_server
                        else:
                            ms.sql_test_command += line

                yield ms
