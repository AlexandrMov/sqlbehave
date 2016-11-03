import os, glob
from sqlalchemy import *
import sqlalchemy.exc
from sqlalchemy.orm import sessionmaker
from parse import *
from lxml import etree
from datetime import datetime, date, time

step_types = {
    'given': 0,
    'when': 1,
    'then': 2
}

curpath = os.path.basename(os.getcwd())
if curpath == 'steps':
    os.chdir('..')

if curpath == 'features':
    os.chdir('..')

global_vars = dict()
connect_config = dict()
link_config = dict()
    
try:
    exec(open("./settings.py").read(), global_vars)
except FileNotFoundError:
    try:
        exec(open("../settings.py").read(), global_vars)
    except FileNotFoundError:
        pass

try:
    connect_config = global_vars['connect_config']
    link_config = global_vars['link_config']
except:
    pass

class TestModule:

    def __init__(self, module_name):
        self.module_name = module_name
        self.results = []
        self.connect_list = dict()

    def run_predicate_from_file(self, predicate, step_type):
        predicate_template = "./features/steps/{step_type}*.sql"
        param_value_tmpl = "--!{param}={value}"
        print(os.getcwd())
        predicate_format = predicate_template.format(step_type=step_type)
        
        params = dict()
        filename_params = dict()
        sql_command = ""
        is_sql_command = 0
        filename = ""
        cmd = ""
        decl = 'DECLARE @context XML,\n@table XML,\n'
        prms = "\t@context = @context OUTPUT,\n"
        prms += "\t@table = @table,\n"

        def process_file(fn):
            sql_command = ""
            is_sql = 0
            schema = ""
            proc_name = ""
            
            with open(g, 'r') as f:
                for line in f:
                    p = parse(param_value_tmpl, line)
                    if p != None and len(p.named) > 0:
                        params[p.named['param']] = p.named['value']

                    sql_command += line

                try:
                    sql_command = 'EXEC {}.{}'.format(params['schema_name'], params['proc_name'])
                    schema, proc_name = params['schema_name'], params['proc_name']
                except:
                    is_sql = 1

            return sql_command, is_sql, schema, proc_name
        
        for g in glob.iglob(predicate_format):
            filename = os.path.basename(os.path.splitext(g)[0])
            step_filename = "{0} {1}".format(step_type, predicate)
            if filename == step_filename:
                cmd, is_sql_command, schema, proc_name = process_file(g)
                break
            else:
                fd = parse(filename, step_filename)
                if fd != None and len(fd.named) > 0:
                    for k in fd.named:
                        vl = fd.named[k]
                        decl += "\t@{} NVARCHAR(128) = '{}',\n".format(k, vl)
                        prms += "\t@{} = @{},\n".format(k, k)

                    cmd, is_sql_command, schema, proc_name = process_file(g)
                    break
            
                        
        context = etree.Element("context")
        table = etree.SubElement(context, "table")
        if self.ctx_table is not None:
            for ct in self.ctx_table:
                row = etree.SubElement(table, 'row')
                for hd in ct.headings:
                    row.set(hd, ct[hd])

        ctx_str = etree.tostring(context)

        if len(cmd) > 0:
            ctx_str = str(ctx_str.decode("utf-8")).replace("'", "''")
            decl = decl[:-2] + "\n\nSET @table = '{}'".format(ctx_str)

            try:
                decl += "\n\nSET @context = '{}'".format(self.ctx_xml)
            except AttributeError:
                pass

            cmd = decl + "\n\n" + cmd + "\n"
            cmd += prms[:-2] if is_sql_command == 0 else ''
            cmd += "\n\nSELECT @context AS behave_result"

        if params['connect'] in link_config:
            params['connect'] = link_config[params['connect']]
            
        engine = create_engine(params['connect'])

        maker = sessionmaker(bind=engine)
        session = maker()

        row = None
        trans = session.begin(subtransactions=True)
        try:
            session.execute("SET DATEFORMAT dmy;")
            res = session.execute(text(cmd))
            if res.cursor != None:

                while 'behave_result' != res.cursor.description[0][0]:
                    names = [c[0] for c in res.cursor.description]
                    store_results = []
                    while 1:
                        row_raw = res.cursor.fetchone()
                        if row_raw is None:
                            break

                        row = dict(zip(names, row_raw))
                        store_results.append(row)

                    self.results.append(store_results)
                    res.cursor.nextset()

                row = res.cursor.fetchone()
                res.close()
                session.execute('IF @@TRANCOUNT > 0 BEGIN COMMIT END')
        except:
            print(cmd)
            raise
        
        # процедура или скрипт вернули данные
        rs_xml = etree.Element("results")
        rs_xml.set('step_type', step_type)
        rs_xml.set('predicate', predicate)
        for res_set in self.results:
            rset_xml = etree.SubElement(rs_xml, "result_set")
            for res_row in res_set:
                rrow_xml = etree.SubElement(rset_xml, "row")
                for res_col in res_row:
                    res_col4xml = 'empty' if len(res_col) == 0 else res_col
                    rrow_xml.set(res_col4xml, str(res_row[res_col]))

        session.close()

        if row != None:
            if row[0] is None:
                ctx_out_xml = etree.Element("context")
            else:
                ctx_out_xml = etree.XML(row[0])
            ctx_out_xml.append(rs_xml)
            return etree.tostring(ctx_out_xml).decode('utf-8')

        return None
