# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/01a_doclinks.ipynb.

#nbdev_cell auto 0
__all__ = ['mod_fn2name', 'DocLinks', 'nbdev_build_lib']


#nbdev_cell ../nbs/01a_doclinks.ipynb 2
#export
from .read import *
from .export import *
from .imports import *
from fastcore.script import *
from fastcore.imports import *
from fastcore.utils import *

import ast,contextlib
from pprint import pformat
from urllib.parse import urljoin


#nbdev_cell ../nbs/01a_doclinks.ipynb 5
#export
def mod_fn2name(fn):
    "Convert filename `fn` to its module name"
    return '.'.join(str(Path(fn).with_suffix('')).split('/'))


#nbdev_cell ../nbs/01a_doclinks.ipynb 7
#export
class DocLinks:
    def __init__(self, mod_fn, doc_func, dest_fn, mod_name=None):
        mod_fn,dest_fn = Path(mod_fn),Path(dest_fn)
        if mod_name is None: mod_name = mod_fn2name(
            mod_fn.resolve().relative_to(dest_fn.parent.parent.resolve()))
        store_attr()
        if self.dest_fn.exists(): self.d = exec_local(self.dest_fn.read_text(), 'd')
        else: self.d = dict(mods={}, syms={}, settings={}) 


#nbdev_cell ../nbs/01a_doclinks.ipynb 9
#export
@patch
def write_nbdev_idx(self:DocLinks):
    "Create nbdev documentation index file`"
    self.dest_fn.write_text("# Autogenerated by nbdev\n\nd = "
                            + pformat(self.d, width=160, indent=2, compact=True, sort_dicts=False))


#nbdev_cell ../nbs/01a_doclinks.ipynb 11
#export
@patch
def update_mods(self:DocLinks): self.d['mods'][self.mod_name] = self.doc_func(self.mod_name)


#nbdev_cell ../nbs/01a_doclinks.ipynb 13
#export
def _all_or_exports(fn):
    code = Path(fn).read_text()
    trees = L(ast.parse(code).body)
    res = read_var(code, '__all__')
    return L(retr_exports(trees) if res is None else res),trees

def _is_patch(o): return any(L(o.decorator_list).filter(Self.id.startswith('patch')))
def _pat_name(o):
    try: return f'{o.args.args[0].annotation.id}.{o.name}'
    except AttributeError: return None 

def _exp_meths(tree):
    return L(f"{tree.name}.{o.name}" for o in tree.body
             if isinstance(o,(ast.FunctionDef,ast.AsyncFunctionDef)) and o.name[0]!='_')


#nbdev_cell ../nbs/01a_doclinks.ipynb 14
#export
@patch
def update_syms(self:DocLinks):
    exp,trees = _all_or_exports(self.mod_fn)
    exp_class = trees.filter(lambda o: isinstance(o, ast.ClassDef) and o.name in exp)
    exp += exp_class.map(_exp_meths).concat()
    pats = L(f'{o.args.args[0].annotation.id}.{o.name}' for o in trees
       if isinstance(o,(ast.FunctionDef,ast.AsyncFunctionDef)) and _is_patch(o))
    exp += pats.filter()
    exp = exp.map(f"{self.mod_name}.{{}}")
    self.d['syms'][self.mod_name] = exp.map_dict(partial(self.doc_func, self.mod_name))


#nbdev_cell ../nbs/01a_doclinks.ipynb 16
#export
@patch
def build_index(self:DocLinks):
    self.update_mods()
    self.update_syms()
    self.d['settings'] = dict(**Config().d)
    self.write_nbdev_idx()


#nbdev_cell ../nbs/01a_doclinks.ipynb 20
#export
def _doc_link(url, mod, sym=None):
    res = urljoin(url, mod)
    if sym: res += "#" + remove_prefix(sym, mod+".")
    return res


#nbdev_cell ../nbs/01a_doclinks.ipynb 21
#export
def _update_baseurl(path=None):
    "Add or update `baseurl` in `_config.yml` for the docs"
    _re_baseurl = re.compile('^baseurl\s*:.*$', re.MULTILINE)
    path = Path(ifnone(path, Config().doc_path))
    fname = path/'_config.yml'
    if not fname.exists(): return
    code = fname.read_text()
    if _re_baseurl.search(code) is None: code = code + f"\nbaseurl: {Config().doc_baseurl}"
    else: code = _re_baseurl.sub(f"baseurl: {Config().doc_baseurl}", code)
    fname.write_text(code)

def _use_nb(p): return not p.name.startswith('_') and '.ipynb_checkpoints' not in p.parts


#nbdev_cell ../nbs/01a_doclinks.ipynb 22
#export
@call_parse
def nbdev_build_lib(
    nbs:Param("Glob specifiying notebooks to export (defaults to all nbs in `nbs_path`)", str)=None,
    dest:Param("Destination for library (defaults to `lib_path`)", str)=None):
    "Convert notebooks matching `nbs` to modules"
    cfg = Config()
    dest = cfg.config_path/(ifnone(dest, cfg.lib_path))
    if os.environ.get('IN_TEST',0): return
    _fn = dest/'_modidx.py'
    if nbs is None:
        files = L(cfg.path('nbs_path').glob('*.ipynb')).filter(_use_nb)
        with contextlib.suppress(FileNotFoundError): _fn.unlink()
    else: files = glob.glob(nbs)
    for file in files: ExportModuleProcessor(file, dest).create_modules()
    doc_func = partial(_doc_link, urljoin(cfg.doc_host,cfg.doc_baseurl))
    for file in dest.glob("**/*.py"):
        if file.name[0]!='_': DocLinks(file, doc_func, _fn).build_index()
    if not cfg.get('extension',False):
        _update_baseurl()
        add_init(dest)


