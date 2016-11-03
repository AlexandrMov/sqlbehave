import os, errno
from sqlbehave import behavemodule
from datetime import datetime, date, time
import argparse

env_import = """import sys
from behave import *
from sqlalchemy import *

from sqlbehave.testmodule import TestModule, step_types

"""

env_predicate = """
def before_step(context, step):
    context.step = step
    context.tm = TestModule(context.config.userdata.get("module_name"))

def before_all(context):
    context.acc = None
"""

steps_import = """from behave import *
from sqlalchemy import *
"""

steps_predicate = """
@{predicate_type}(u'{predicate_string}')
def step_impl(context, **kwargs):
    context.tm.params = kwargs
    context.tm.ctx_table = context.table
    context.tm.orig_predicate = "{predicate_string}"

    try:
        context.tm.ctx_xml = context.xml
    except AttributeError:
        pass

    context.xml = context.tm.run_predicate_from_file(context.step.name, context.step.step_type)
"""

step_types = {
    0: 'given',
    1: 'when',
    2: 'then'
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", help="run command")
    parser.add_argument("-m", "--modulename", help="module name", default=None)
    args = parser.parse_args()

    curpath = os.path.basename(os.getcwd())
    MODULE_NAME = None

    if curpath == 'steps':
        os.chdir("..")

    if curpath == 'features':
        os.chdir("..")

    MODULE_NAME = os.path.basename(os.getcwd())

    if args.command == "startmodule":
        if args.modulename is None:
            raise Exception("Please enter new module name with -m argument!")

        if os.path.exists("settings.py") and os.path.exists("../settings.py"):
            chdir("..")

        if not os.path.exists("settings.py"):
            raise Exception("It isn't a sqlbehave project!")

        print(args.modulename)
        module_path = "./%s/features/steps" % args.modulename
        if not os.path.exists(module_path):
            os.makedirs(module_path, exist_ok=True)

        other_path = "./%s/%s"

        readme_path = other_path % (args.modulename, "README.md")
        if not os.path.exists(readme_path):
            with open(readme_path, "w") as f:
                f.write("%s" % args.modulename)

        beini_path = other_path % (args.modulename, "features/behave.ini")
        if not os.path.exists(beini_path):
            with open(beini_path, "w") as f:
                f.write("[behave.userdata]\n")
                f.write("module_name = %s" % args.modulename)

    if args.command == "mksteps":

        if not os.path.exists("../settings.py"):
            raise Exception("It isn't a sqlbehave project!")

        if MODULE_NAME is None:
            raise Exception("Please change current directory on a module folder!")

        bmodule = behavemodule.FileSqlBehaveModule(module_name=MODULE_NAME)
        if bmodule is None:
            raise Exception("Unknown error!")

        if not os.path.exists("./features/steps"):
            os.makedirs("./features/steps", exist_ok=True)

        script_text = steps_import
        pyscript_file = "./features/steps/%s.py" % bmodule.module_name
        for r in bmodule.get_steps():
            script_text += (steps_predicate.format(predicate_type=step_types[r.id_predicate_type], \
                                                   predicate_string=r.predicate))
            filenamestep = "{} {}.sql".format(step_types[r.id_predicate_type], r.predicate)

        with open(pyscript_file, "w") as f:
            f.write(script_text)

        env_text = env_import
        env_text += env_predicate
        with open("./features/environment.py", "w") as f:
            f.write(env_text)

if __name__ == "__main__":
    main()
