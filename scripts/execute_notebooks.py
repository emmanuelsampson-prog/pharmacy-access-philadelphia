"""Execute notebook records; fail on any cell error."""
from pathlib import Path
import argparse
import tempfile
import os
import sys
import contextlib
from datetime import datetime,timezone
import nbformat
from nbclient import NotebookClient
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--ipc',action='store_true',help='Use Unix-domain sockets when local TCP kernel sockets are unavailable')
parser.add_argument('--inprocess',action='store_true',help='Execute actual cells through IPython without kernel sockets')
args=parser.parse_args()

def execute_inprocess(nb):
    """Capture real IPython stdout/stderr and rich displays in execution order."""
    from IPython.core.interactiveshell import InteractiveShell
    InteractiveShell.clear_instance()
    shell=InteractiveShell.instance()
    os.chdir(ROOT)
    count=0
    for cell in nb.cells:
        if cell.cell_type!='code':continue
        count+=1
        outputs=[]
        class Stream:
            def __init__(self,name):self.name=name
            def write(self,value):
                if value:
                    if outputs and outputs[-1].output_type=='stream' and outputs[-1].name==self.name:outputs[-1].text+=value
                    else:outputs.append(nbformat.v4.new_output('stream',name=self.name,text=value))
                return len(value)
            def flush(self):pass
            def isatty(self):return False
        original=shell.display_pub.publish
        def publish(data,metadata=None,**kwargs):
            outputs.append(nbformat.v4.new_output('display_data',data=data,metadata=metadata or {}))
        shell.display_pub.publish=publish
        try:
            with contextlib.redirect_stdout(Stream('stdout')),contextlib.redirect_stderr(Stream('stderr')):
                result=shell.run_cell(cell.source,store_history=True)
            if result.error_before_exec:raise result.error_before_exec
            if result.error_in_exec:raise result.error_in_exec
            cell.execution_count=count;cell.outputs=outputs
        finally:shell.display_pub.publish=original
    nb.metadata['execution_record']={
        'backend':'IPython InteractiveShell in-process; hosted kernel sockets unavailable',
        'executed_at_utc':datetime.now(timezone.utc).isoformat(),
        'python_version':sys.version.split()[0],
        'all_code_cells_executed':True}
    InteractiveShell.clear_instance()

for path in sorted((ROOT/"notebooks").glob("*.ipynb")):
    nb=nbformat.read(path,as_version=4)
    if args.inprocess:
        execute_inprocess(nb)
        nbformat.validate(nb)
        nbformat.write(nb,path)
        print(f'Executed {path.name} using IPython in-process',flush=True)
        continue
    client=NotebookClient(nb,timeout=300,kernel_name="pharmacy-access",resources={"metadata":{"path":str(ROOT)}})
    if args.ipc:
        manager=client.create_kernel_manager()
        manager.transport='ipc'
        manager.ip=str(Path(tempfile.mkdtemp(prefix='pharmacy-kernel-'))/'socket')
    client.execute()
    nbformat.write(nb,path)
    print(f'Executed {path.name}: {sum(c.cell_type=="code" for c in nb.cells)} code cells',flush=True)
