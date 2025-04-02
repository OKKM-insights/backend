import sys
import types

# Create dummy 'pycuda' module if it doesn't exist.
if "pycuda" not in sys.modules:
    dummy_pycuda = types.ModuleType("pycuda")
    sys.modules["pycuda"] = dummy_pycuda
else:
    dummy_pycuda = sys.modules["pycuda"]

# Create dummy 'pycuda.driver' module.
if "pycuda.driver" not in sys.modules:
    dummy_driver = types.ModuleType("pycuda.driver")
    # Add any dummy functions/attributes you might need.
    dummy_driver.init = lambda: None
    dummy_driver.Device = lambda *args, **kwargs: None
    dummy_driver.Context = lambda *args, **kwargs: None
    sys.modules["pycuda.driver"] = dummy_driver
    dummy_pycuda.driver = dummy_driver

# Create dummy 'pycuda.autoinit' submodule.
if "pycuda.autoinit" not in sys.modules:
    dummy_autoinit = types.ModuleType("pycuda.autoinit")
    sys.modules["pycuda.autoinit"] = dummy_autoinit
    dummy_pycuda.autoinit = dummy_autoinit

# Create dummy 'pycuda.compiler' submodule with a dummy SourceModule.
if "pycuda.compiler" not in sys.modules:
    dummy_compiler = types.ModuleType("pycuda.compiler")
    dummy_compiler.SourceModule = lambda code: None
    sys.modules["pycuda.compiler"] = dummy_compiler
    dummy_pycuda.compiler = dummy_compiler
