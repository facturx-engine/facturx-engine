from setuptools import setup
from Cython.Build import cythonize
from setuptools.extension import Extension
import os

# List of modules to compile into binaries
# We protect the License Manager and the Core Extractor

extensions = [
    Extension("app.license", ["app/license.py"]),
    Extension("app.services.extractor", ["app/services/extractor.py"]),
    Extension("app.services.generator", ["app/services/generator.py"]),
    Extension("app.services.validator", ["app/services/validator.py"]),
]

setup(
    name="Factur-X-Engine-Pro",
    ext_modules=cythonize(
        extensions,
        compiler_directives={'language_level': "3", 'always_allow_keywords': True},
        build_dir="build"
    ),
)
print(f"Compiling extensions: {[e.name for e in extensions]}")
print(f"Current Directory: {os.getcwd()}")
